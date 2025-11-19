"""
Service para Integração E-commerce
"""
import math
import time
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ecommerce.models import (
    ConfiguracaoEcommerce,
    PedidoEcommerce,
    ItemPedidoEcommerce,
    LogSincronizacao,
    StatusPedidoEcommerce,
)
from app.modules.ecommerce.schemas import (
    ConfiguracaoEcommerceCreate,
    ConfiguracaoEcommerceUpdate,
    ConfiguracaoEcommerceResponse,
    PedidoEcommerceCreate,
    PedidoEcommerceResponse,
    PedidoEcommerceList,
    ProcessarPedidoRequest,
    ResultadoSincronizacao,
)
from app.modules.produtos.repository import ProdutoRepository
from app.modules.clientes.repository import ClienteRepository
from app.modules.vendas.service import VendasService
from app.core.exceptions import NotFoundException, ValidationException


class EcommerceService:
    """Service para integração com E-commerce"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.produto_repository = ProdutoRepository(session)
        self.cliente_repository = ClienteRepository(session)

    # ==================== CONFIGURAÇÃO ====================

    async def criar_configuracao(
        self, data: ConfiguracaoEcommerceCreate
    ) -> ConfiguracaoEcommerceResponse:
        """Cria configuração de e-commerce"""
        config = ConfiguracaoEcommerce(**data.model_dump())
        self.session.add(config)
        await self.session.flush()
        await self.session.refresh(config)
        return ConfiguracaoEcommerceResponse.model_validate(config)

    async def get_configuracao(self, config_id: int) -> ConfiguracaoEcommerceResponse:
        """Busca configuração por ID"""
        query = select(ConfiguracaoEcommerce).where(ConfiguracaoEcommerce.id == config_id)
        result = await self.session.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            raise NotFoundException(f"Configuração {config_id} não encontrada")

        return ConfiguracaoEcommerceResponse.model_validate(config)

    async def atualizar_configuracao(
        self, config_id: int, data: ConfiguracaoEcommerceUpdate
    ) -> ConfiguracaoEcommerceResponse:
        """Atualiza configuração"""
        query = select(ConfiguracaoEcommerce).where(ConfiguracaoEcommerce.id == config_id)
        result = await self.session.execute(query)
        config = result.scalar_one_or_none()

        if not config:
            raise NotFoundException(f"Configuração {config_id} não encontrada")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        await self.session.flush()
        await self.session.refresh(config)
        return ConfiguracaoEcommerceResponse.model_validate(config)

    # ==================== PEDIDOS ====================

    async def criar_pedido(
        self, data: PedidoEcommerceCreate
    ) -> PedidoEcommerceResponse:
        """Cria pedido recebido do e-commerce"""
        # Verifica se pedido já existe
        query = select(PedidoEcommerce).where(
            and_(
                PedidoEcommerce.configuracao_id == data.configuracao_id,
                PedidoEcommerce.pedido_externo_id == data.pedido_externo_id,
            )
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValidationException(
                f"Pedido {data.pedido_externo_id} já foi importado"
            )

        # Cria pedido
        pedido_dict = data.model_dump(exclude={"itens"})
        pedido = PedidoEcommerce(**pedido_dict)
        self.session.add(pedido)
        await self.session.flush()

        # Cria itens
        for item_data in data.itens:
            # Tenta mapear produto por SKU
            produto = await self._mapear_produto(item_data.produto_sku)

            item = ItemPedidoEcommerce(
                pedido_id=pedido.id,
                produto_id=produto.id if produto else None,
                **item_data.model_dump(),
            )
            self.session.add(item)

        await self.session.flush()
        await self.session.refresh(pedido)
        return PedidoEcommerceResponse.model_validate(pedido)

    async def get_pedido(self, pedido_id: int) -> PedidoEcommerceResponse:
        """Busca pedido por ID"""
        query = select(PedidoEcommerce).where(PedidoEcommerce.id == pedido_id)
        result = await self.session.execute(query)
        pedido = result.scalar_one_or_none()

        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        return PedidoEcommerceResponse.model_validate(pedido)

    async def list_pedidos(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
        config_id: Optional[int] = None,
    ) -> PedidoEcommerceList:
        """Lista pedidos com filtros"""
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        query = select(PedidoEcommerce)

        if status:
            query = query.where(PedidoEcommerce.status == status)
        if config_id:
            query = query.where(PedidoEcommerce.configuracao_id == config_id)

        query = query.order_by(PedidoEcommerce.data_pedido.desc()).offset(skip).limit(page_size)

        result = await self.session.execute(query)
        pedidos = list(result.scalars().all())

        # Count total
        count_query = select(PedidoEcommerce)
        if status:
            count_query = count_query.where(PedidoEcommerce.status == status)
        if config_id:
            count_query = count_query.where(PedidoEcommerce.configuracao_id == config_id)

        from sqlalchemy import func
        count_query = select(func.count()).select_from(count_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        pages = math.ceil(total / page_size) if total > 0 else 1

        return PedidoEcommerceList(
            items=[PedidoEcommerceResponse.model_validate(p) for p in pedidos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def processar_pedido(
        self, pedido_id: int, data: ProcessarPedidoRequest
    ) -> PedidoEcommerceResponse:
        """
        Processa pedido do e-commerce e cria venda no ERP

        Regras:
        - Cria cliente se não existir (opcional)
        - Mapeia produtos
        - Cria venda no ERP
        - Atualiza status do pedido
        """
        # Busca pedido
        query = select(PedidoEcommerce).where(PedidoEcommerce.id == pedido_id)
        result = await self.session.execute(query)
        pedido = result.scalar_one_or_none()

        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        if pedido.status != StatusPedidoEcommerce.PENDENTE:
            raise ValidationException(
                f"Apenas pedidos PENDENTES podem ser processados. Status atual: {pedido.status}"
            )

        try:
            pedido.status = StatusPedidoEcommerce.PROCESSANDO
            await self.session.flush()

            # Busca ou cria cliente
            cliente_id = await self._buscar_ou_criar_cliente(
                pedido, criar_se_nao_existir=data.criar_cliente
            )

            # Cria venda no ERP
            vendas_service = VendasService(self.session)

            # Monta itens da venda
            itens_venda = []
            for item in pedido.itens:
                if not item.produto_id:
                    raise ValidationException(
                        f"Produto '{item.produto_nome}' não mapeado no ERP"
                    )

                itens_venda.append({
                    "produto_id": item.produto_id,
                    "quantidade": float(item.quantidade),
                    "preco_unitario": float(item.preco_unitario),
                })

            # Importa schema de vendas
            from app.modules.vendas.schemas import VendaCreate, ItemVendaCreate

            venda_data = VendaCreate(
                cliente_id=cliente_id,
                itens=[ItemVendaCreate(**item) for item in itens_venda],
                observacoes=f"Pedido E-commerce #{pedido.numero_pedido}",
            )

            venda = await vendas_service.criar_venda(venda_data)

            # Atualiza pedido
            pedido.venda_id = venda.id
            pedido.status = StatusPedidoEcommerce.FATURADO
            pedido.data_processamento = datetime.utcnow()
            pedido.erro_integracao = None

            await self.session.flush()
            await self.session.refresh(pedido)

            return PedidoEcommerceResponse.model_validate(pedido)

        except Exception as e:
            # Registra erro
            pedido.status = StatusPedidoEcommerce.ERRO
            pedido.erro_integracao = str(e)
            await self.session.flush()
            raise

    async def _mapear_produto(self, sku: Optional[str]):
        """Tenta mapear produto do e-commerce com produto do ERP via SKU/código de barras"""
        if not sku:
            return None

        produto = await self.produto_repository.get_by_codigo_barras(sku)
        return produto

    async def _buscar_ou_criar_cliente(
        self, pedido: PedidoEcommerce, criar_se_nao_existir: bool = True
    ):
        """Busca cliente por CPF/CNPJ ou cria novo"""
        # Tenta buscar por CPF/CNPJ
        if pedido.cliente_cpf_cnpj:
            cliente = await self.cliente_repository.get_by_cpf_cnpj(
                pedido.cliente_cpf_cnpj
            )
            if cliente:
                return cliente.id

        # Tenta buscar por email
        if pedido.cliente_email:
            query = select(self.cliente_repository.model).where(
                self.cliente_repository.model.email == pedido.cliente_email
            )
            result = await self.session.execute(query)
            cliente = result.scalar_one_or_none()
            if cliente:
                return cliente.id

        # Cria novo cliente se autorizado
        if criar_se_nao_existir:
            from app.modules.clientes.schemas import ClienteCreate

            cliente_data = ClienteCreate(
                nome=pedido.cliente_nome,
                tipo="PF" if len(pedido.cliente_cpf_cnpj or "") == 11 else "PJ",
                cpf=pedido.cliente_cpf_cnpj if len(pedido.cliente_cpf_cnpj or "") == 11 else None,
                cnpj=pedido.cliente_cpf_cnpj if len(pedido.cliente_cpf_cnpj or "") == 14 else None,
                email=pedido.cliente_email,
                telefone=pedido.cliente_telefone,
            )

            cliente = await self.cliente_repository.create(cliente_data)
            return cliente.id

        raise ValidationException(
            f"Cliente '{pedido.cliente_nome}' não encontrado no ERP"
        )

    # ==================== SINCRONIZAÇÃO ====================

    async def sincronizar_produtos(
        self, config_id: int, produto_ids: Optional[List[int]] = None
    ) -> ResultadoSincronizacao:
        """
        Sincroniza produtos do ERP para E-commerce

        Nota: Esta é uma implementação simulada.
        Na prática, seria necessário implementar conectores específicos
        para cada plataforma (WooCommerce, Magento, etc.)
        """
        inicio = time.time()

        config = await self.get_configuracao(config_id)

        if produto_ids:
            produtos = []
            for pid in produto_ids:
                produto = await self.produto_repository.get_by_id(pid)
                if produto:
                    produtos.append(produto)
        else:
            produtos = await self.produto_repository.get_all(0, 10000, apenas_ativos=True)

        total = len(produtos)
        sucesso = 0
        erro = 0
        mensagens = []

        for produto in produtos:
            try:
                # Simula sincronização
                # Na prática, aqui seria chamada a API da plataforma
                await self._log_sincronizacao(
                    config_id, "PRODUTO", produto.id, True, "Produto sincronizado com sucesso"
                )
                sucesso += 1
            except Exception as e:
                await self._log_sincronizacao(
                    config_id, "PRODUTO", produto.id, False, str(e)
                )
                erro += 1
                mensagens.append(f"Erro no produto {produto.id}: {str(e)}")

        tempo = time.time() - inicio

        return ResultadoSincronizacao(
            tipo="PRODUTO",
            total_processados=total,
            total_sucesso=sucesso,
            total_erro=erro,
            tempo_execucao_segundos=round(tempo, 2),
            mensagens=mensagens[:10],  # Limita a 10 mensagens
        )

    async def _log_sincronizacao(
        self, config_id: int, tipo: str, produto_id: Optional[int], sucesso: bool, mensagem: str
    ):
        """Registra log de sincronização"""
        log = LogSincronizacao(
            configuracao_id=config_id,
            tipo_sincronizacao=tipo,
            produto_id=produto_id,
            sucesso=sucesso,
            mensagem=mensagem,
        )
        self.session.add(log)
        await self.session.flush()
