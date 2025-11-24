"""
Service Layer para Pedidos de Venda
"""
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.pedidos_venda.repository import PedidoVendaRepository
from app.modules.pedidos_venda.models import StatusPedidoVenda, TipoEntrega
from app.modules.pedidos_venda.schemas import (
    PedidoVendaCreate,
    PedidoVendaUpdate,
    PedidoVendaResponse,
    PedidoVendaListResponse,
    ConfirmarPedidoRequest,
    SepararPedidoRequest,
    FaturarPedidoRequest,
    CancelarPedidoRequest,
    RelatorioPedidosResponse,
)
from app.modules.produtos.repository import ProdutoRepository
from app.modules.orcamentos.repository import OrcamentoRepository
from app.modules.orcamentos.models import StatusOrcamento
from app.modules.vendas.service import VendasService
from app.modules.vendas.schemas import VendaCreate, ItemVendaCreate
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


class PedidoVendaService:
    """Service para regras de negócio de Pedidos de Venda"""

    def __init__(self, session: AsyncSession):
        self.repository = PedidoVendaRepository(session)
        self.produto_repository = ProdutoRepository(session)
        self.orcamento_repository = OrcamentoRepository(session)
        self.session = session

    async def criar_pedido(
        self, pedido_data: PedidoVendaCreate, vendedor_id: int
    ) -> PedidoVendaResponse:
        """
        Cria um pedido de venda completo com itens

        Regras:
        - Valida se todos os produtos existem
        - Pode ser criado a partir de um orçamento aprovado
        - Calcula totais (subtotal, valor_total)
        - NÃO mexe em estoque (só reserva quando separar)
        - Cria o pedido com status RASCUNHO
        - Gera número sequencial (PV000001)

        Args:
            pedido_data: Dados do pedido com itens
            vendedor_id: ID do vendedor que está criando o pedido

        Returns:
            PedidoVendaResponse com o pedido criado

        Raises:
            NotFoundException: Se produto ou orçamento não existe
            ValidationException: Se validações falharem
            BusinessRuleException: Se orçamento não pode ser usado
        """
        # Valida que há itens
        if not pedido_data.itens or len(pedido_data.itens) == 0:
            raise ValidationException("Pedido deve ter pelo menos um item")

        # Se foi criado a partir de orçamento, valida o orçamento
        if pedido_data.orcamento_id:
            orcamento = await self.orcamento_repository.get_by_id(
                pedido_data.orcamento_id
            )
            if not orcamento:
                raise NotFoundException(
                    f"Orçamento {pedido_data.orcamento_id} não encontrado"
                )

            if orcamento.status != StatusOrcamento.APROVADO:
                raise BusinessRuleException(
                    f"Orçamento deve estar APROVADO. Status atual: {orcamento.status}"
                )

        # Valida produtos para todos os itens
        for item in pedido_data.itens:
            produto = await self.produto_repository.get_by_id(item.produto_id)
            if not produto:
                raise NotFoundException(f"Produto {item.produto_id} não encontrado")

            if not produto.ativo:
                raise ValidationException(
                    f"Produto '{produto.descricao}' está inativo"
                )

        # Gera número do pedido
        numero_pedido = await self.repository.gerar_numero_pedido()

        # Prepara dados do pedido
        pedido_dict = pedido_data.model_dump(exclude={"itens"})
        pedido_dict["vendedor_id"] = vendedor_id
        pedido_dict["numero_pedido"] = numero_pedido
        pedido_dict["data_pedido"] = date.today()
        pedido_dict["status"] = StatusPedidoVenda.RASCUNHO

        # Calcula subtotal
        subtotal = 0.0
        for item in pedido_data.itens:
            total_item = (
                item.quantidade * item.preco_unitario
            ) - item.desconto_item
            subtotal += total_item

        # Calcula valor total
        valor_total = (
            subtotal
            + pedido_data.valor_frete
            + pedido_data.outras_despesas
            - pedido_data.desconto
        )

        if valor_total < 0:
            raise ValidationException(
                "Valor total do pedido não pode ser negativo"
            )

        pedido_dict["subtotal"] = subtotal
        pedido_dict["valor_total"] = valor_total

        # Cria o pedido
        from app.modules.pedidos_venda.models import PedidoVenda, ItemPedidoVenda

        pedido = PedidoVenda(**pedido_dict)
        self.session.add(pedido)
        await self.session.flush()

        # Cria itens
        for item_data in pedido_data.itens:
            total_item = (
                item_data.quantidade * item_data.preco_unitario
            ) - item_data.desconto_item

            item_dict = item_data.model_dump()
            item_dict["pedido_id"] = pedido.id
            item_dict["total_item"] = total_item
            item_dict["quantidade_separada"] = 0.0

            item = ItemPedidoVenda(**item_dict)
            self.session.add(item)

        await self.session.flush()
        await self.session.refresh(pedido)

        return PedidoVendaResponse.model_validate(pedido)

    async def atualizar_pedido(
        self, pedido_id: int, pedido_data: PedidoVendaUpdate
    ) -> PedidoVendaResponse:
        """
        Atualiza um pedido de venda

        Regras:
        - Pedido deve existir
        - Só pode editar se status = RASCUNHO
        - Recalcula valor_total se houver mudanças

        Args:
            pedido_id: ID do pedido
            pedido_data: Dados para atualização

        Returns:
            PedidoVendaResponse com o pedido atualizado

        Raises:
            NotFoundException: Se pedido não existe
            BusinessRuleException: Se pedido não pode ser editado
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        if pedido.status != StatusPedidoVenda.RASCUNHO:
            raise BusinessRuleException(
                f"Pedido não pode ser editado. Status atual: {pedido.status}. "
                "Apenas pedidos com status RASCUNHO podem ser editados."
            )

        # Atualiza campos
        update_dict = pedido_data.model_dump(exclude_unset=True)

        # Recalcula valor_total se necessário
        if any(
            key in update_dict
            for key in ["desconto", "valor_frete", "outras_despesas"]
        ):
            valor_total = (
                pedido.subtotal
                + update_dict.get("valor_frete", pedido.valor_frete)
                + update_dict.get("outras_despesas", pedido.outras_despesas)
                - update_dict.get("desconto", pedido.desconto)
            )
            update_dict["valor_total"] = valor_total

        pedido_atualizado = await self.repository.update(pedido_id, update_dict)
        await self.session.flush()

        return PedidoVendaResponse.model_validate(pedido_atualizado)

    async def confirmar_pedido(
        self, pedido_id: int, request: ConfirmarPedidoRequest, usuario_id: int
    ) -> PedidoVendaResponse:
        """
        Confirma um pedido (RASCUNHO → CONFIRMADO)

        Args:
            pedido_id: ID do pedido
            request: Dados para confirmação
            usuario_id: ID do usuário que está confirmando

        Returns:
            PedidoVendaResponse com o pedido confirmado
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        if pedido.status != StatusPedidoVenda.RASCUNHO:
            raise BusinessRuleException(
                f"Pedido não pode ser confirmado. Status atual: {pedido.status}"
            )

        # Atualiza status e observações
        update_data = {
            "status": StatusPedidoVenda.CONFIRMADO,
        }

        if request.observacao:
            observacoes_atuais = pedido.observacoes_internas or ""
            update_data["observacoes_internas"] = (
                f"{observacoes_atuais}\n[CONFIRMADO] {request.observacao}".strip()
            )

        pedido_atualizado = await self.repository.update(pedido_id, update_data)
        await self.session.flush()

        return PedidoVendaResponse.model_validate(pedido_atualizado)

    async def iniciar_separacao(
        self, pedido_id: int, usuario_id: int
    ) -> PedidoVendaResponse:
        """
        Inicia separação de produtos (CONFIRMADO → EM_SEPARACAO)

        Args:
            pedido_id: ID do pedido
            usuario_id: ID do usuário que está iniciando a separação

        Returns:
            PedidoVendaResponse
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        if pedido.status != StatusPedidoVenda.CONFIRMADO:
            raise BusinessRuleException(
                f"Pedido não pode iniciar separação. Status atual: {pedido.status}"
            )

        update_data = {
            "status": StatusPedidoVenda.EM_SEPARACAO,
            "usuario_separacao_id": usuario_id,
        }

        pedido_atualizado = await self.repository.update(pedido_id, update_data)
        await self.session.flush()

        return PedidoVendaResponse.model_validate(pedido_atualizado)

    async def separar_pedido(
        self, pedido_id: int, request: SepararPedidoRequest, usuario_id: int
    ) -> PedidoVendaResponse:
        """
        Marca pedido como separado (EM_SEPARACAO → SEPARADO)

        Registra quantidade separada para cada item

        Args:
            pedido_id: ID do pedido
            request: Dados com itens_separados
            usuario_id: ID do usuário

        Returns:
            PedidoVendaResponse
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        if pedido.status != StatusPedidoVenda.EM_SEPARACAO:
            raise BusinessRuleException(
                f"Pedido não está em separação. Status atual: {pedido.status}"
            )

        # Atualiza quantidade_separada dos itens
        from app.modules.pedidos_venda.models import ItemPedidoVenda

        for item_separado in request.itens_separados:
            item = next(
                (
                    i
                    for i in pedido.itens
                    if i.produto_id == item_separado["produto_id"]
                ),
                None,
            )
            if item:
                item.quantidade_separada = item_separado["quantidade_separada"]

        # Atualiza status
        update_data = {
            "status": StatusPedidoVenda.SEPARADO,
            "data_separacao": datetime.utcnow(),
        }

        pedido_atualizado = await self.repository.update(pedido_id, update_data)
        await self.session.flush()

        return PedidoVendaResponse.model_validate(pedido_atualizado)

    async def enviar_para_entrega(
        self, pedido_id: int, usuario_id: int
    ) -> PedidoVendaResponse:
        """
        Marca pedido como em entrega (SEPARADO → EM_ENTREGA)

        Args:
            pedido_id: ID do pedido
            usuario_id: ID do usuário

        Returns:
            PedidoVendaResponse
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        if pedido.status != StatusPedidoVenda.SEPARADO:
            raise BusinessRuleException(
                f"Pedido não está separado. Status atual: {pedido.status}"
            )

        update_data = {"status": StatusPedidoVenda.EM_ENTREGA}

        pedido_atualizado = await self.repository.update(pedido_id, update_data)
        await self.session.flush()

        return PedidoVendaResponse.model_validate(pedido_atualizado)

    async def confirmar_entrega(
        self, pedido_id: int, usuario_id: int
    ) -> PedidoVendaResponse:
        """
        Confirma entrega (EM_ENTREGA → ENTREGUE)

        Args:
            pedido_id: ID do pedido
            usuario_id: ID do usuário

        Returns:
            PedidoVendaResponse
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        if pedido.status != StatusPedidoVenda.EM_ENTREGA:
            raise BusinessRuleException(
                f"Pedido não está em entrega. Status atual: {pedido.status}"
            )

        update_data = {
            "status": StatusPedidoVenda.ENTREGUE,
            "data_entrega_real": date.today(),
        }

        pedido_atualizado = await self.repository.update(pedido_id, update_data)
        await self.session.flush()

        return PedidoVendaResponse.model_validate(pedido_atualizado)

    async def faturar_pedido(
        self, pedido_id: int, request: FaturarPedidoRequest, usuario_id: int
    ) -> dict:
        """
        Fatura pedido criando venda (ENTREGUE → FATURADO)

        Regras:
        - Cria Venda através de VendasService
        - VendasService já valida estoque e cria saídas
        - Opcionalmente gera NF-e

        Args:
            pedido_id: ID do pedido
            request: Dados para faturamento
            usuario_id: ID do usuário

        Returns:
            Dict com pedido e venda criada
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        if pedido.status != StatusPedidoVenda.ENTREGUE:
            raise BusinessRuleException(
                f"Pedido não pode ser faturado. Status atual: {pedido.status}. "
                "Pedido deve estar ENTREGUE."
            )

        # Prepara dados da venda a partir do pedido
        itens_venda = []
        for item in pedido.itens:
            item_venda = ItemVendaCreate(
                produto_id=item.produto_id,
                quantidade=item.quantidade_separada or item.quantidade,
                preco_unitario=item.preco_unitario,
                desconto_item=item.desconto_item,
            )
            itens_venda.append(item_venda)

        venda_data = VendaCreate(
            cliente_id=pedido.cliente_id,
            vendedor_id=pedido.vendedor_id,
            forma_pagamento=pedido.forma_pagamento or "DINHEIRO",
            desconto=pedido.desconto,
            observacoes=f"Faturado do Pedido {pedido.numero_pedido}",
            itens=itens_venda,
        )

        # Cria venda através do VendasService
        vendas_service = VendasService(self.session)
        venda = await vendas_service.criar_venda(venda_data)

        # Atualiza status do pedido para FATURADO
        update_data = {
            "status": StatusPedidoVenda.FATURADO,
            "venda_id": venda.id,
        }

        pedido_atualizado = await self.repository.update(pedido_id, update_data)
        await self.session.flush()

        # TODO: Gerar NF-e se request.gerar_nfe == True
        # Integração com módulo fiscal

        return {
            "pedido": PedidoVendaResponse.model_validate(pedido_atualizado),
            "venda": venda,
        }

    async def cancelar_pedido(
        self, pedido_id: int, request: CancelarPedidoRequest, usuario_id: int
    ) -> PedidoVendaResponse:
        """
        Cancela um pedido (qualquer status → CANCELADO)

        Regras:
        - Pedidos FATURADOS não podem ser cancelados
        - Registra motivo nas observações internas

        Args:
            pedido_id: ID do pedido
            request: Dados com motivo do cancelamento
            usuario_id: ID do usuário

        Returns:
            PedidoVendaResponse
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        if pedido.status == StatusPedidoVenda.FATURADO:
            raise BusinessRuleException(
                "Pedidos FATURADOS não podem ser cancelados. "
                "Cancele a venda correspondente."
            )

        if pedido.status == StatusPedidoVenda.CANCELADO:
            raise BusinessRuleException("Pedido já está cancelado")

        # Atualiza status e registra motivo
        observacoes_atuais = pedido.observacoes_internas or ""
        update_data = {
            "status": StatusPedidoVenda.CANCELADO,
            "observacoes_internas": (
                f"{observacoes_atuais}\n[CANCELADO] {request.motivo}".strip()
            ),
        }

        pedido_atualizado = await self.repository.update(pedido_id, update_data)
        await self.session.flush()

        return PedidoVendaResponse.model_validate(pedido_atualizado)

    async def get_pedido(self, pedido_id: int) -> PedidoVendaResponse:
        """
        Busca pedido completo com itens

        Args:
            pedido_id: ID do pedido

        Returns:
            PedidoVendaResponse

        Raises:
            NotFoundException: Se pedido não existe
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        return PedidoVendaResponse.model_validate(pedido)

    async def list_pedidos(
        self,
        skip: int = 0,
        limit: int = 100,
        cliente_id: Optional[int] = None,
        vendedor_id: Optional[int] = None,
        status: Optional[StatusPedidoVenda] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
    ) -> List[PedidoVendaResponse]:
        """
        Lista pedidos com filtros

        Args:
            skip: Offset para paginação
            limit: Limite de resultados
            cliente_id: Filtrar por cliente
            vendedor_id: Filtrar por vendedor
            status: Filtrar por status
            data_inicio: Data inicial
            data_fim: Data final

        Returns:
            Lista de PedidoVendaResponse
        """
        pedidos = await self.repository.list_all(
            skip=skip,
            limit=limit,
            cliente_id=cliente_id,
            vendedor_id=vendedor_id,
            status=status,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        return [PedidoVendaResponse.model_validate(p) for p in pedidos]

    async def get_pedidos_atrasados(self) -> List[PedidoVendaResponse]:
        """
        Busca pedidos atrasados (data_entrega_prevista vencida e não entregues)

        Returns:
            Lista de pedidos atrasados
        """
        from sqlalchemy import select, and_
        from app.modules.pedidos_venda.models import PedidoVenda

        hoje = date.today()

        result = await self.session.execute(
            select(PedidoVenda).where(
                and_(
                    PedidoVenda.data_entrega_prevista < hoje,
                    PedidoVenda.status.in_(
                        [
                            StatusPedidoVenda.CONFIRMADO,
                            StatusPedidoVenda.EM_SEPARACAO,
                            StatusPedidoVenda.SEPARADO,
                            StatusPedidoVenda.EM_ENTREGA,
                        ]
                    ),
                )
            )
        )

        pedidos = result.scalars().all()
        return [PedidoVendaResponse.model_validate(p) for p in pedidos]

    async def get_relatorio_pedidos(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
    ) -> RelatorioPedidosResponse:
        """
        Gera relatório de pedidos

        Args:
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)

        Returns:
            RelatorioPedidosResponse
        """
        from sqlalchemy import select, func
        from app.modules.pedidos_venda.models import PedidoVenda

        query = select(PedidoVenda)

        if data_inicio:
            query = query.where(PedidoVenda.data_pedido >= data_inicio)
        if data_fim:
            query = query.where(PedidoVenda.data_pedido <= data_fim)

        result = await self.session.execute(query)
        pedidos = result.scalars().all()

        # Total de pedidos
        total_pedidos = len(pedidos)

        # Total de valor
        total_valor = sum(p.valor_total for p in pedidos)

        # Pedidos por status
        pedidos_por_status = {}
        for status in StatusPedidoVenda:
            count = len([p for p in pedidos if p.status == status])
            pedidos_por_status[status.value] = count

        # Pedidos atrasados
        hoje = date.today()
        pedidos_atrasados = len(
            [
                p
                for p in pedidos
                if p.data_entrega_prevista < hoje
                and p.status
                not in [
                    StatusPedidoVenda.ENTREGUE,
                    StatusPedidoVenda.FATURADO,
                    StatusPedidoVenda.CANCELADO,
                ]
            ]
        )

        # Ticket médio
        ticket_medio = total_valor / total_pedidos if total_pedidos > 0 else 0.0

        return RelatorioPedidosResponse(
            total_pedidos=total_pedidos,
            total_valor=total_valor,
            pedidos_por_status=pedidos_por_status,
            pedidos_atrasados=pedidos_atrasados,
            ticket_medio=ticket_medio,
        )
