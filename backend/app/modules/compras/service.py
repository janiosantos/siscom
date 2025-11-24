"""
Service Layer para Compras
"""
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.compras.repository import PedidoCompraRepository
from app.modules.compras.models import StatusPedidoCompra
from app.modules.compras.schemas import (
    PedidoCompraCreate,
    PedidoCompraUpdate,
    PedidoCompraResponse,
    PedidoCompraList,
    ItemPedidoCompraCreate,
    ReceberPedidoRequest,
    SugestaoCompraResponse,
    SugestaoCompraList,
    StatusPedidoCompraEnum,
)
from app.modules.produtos.repository import ProdutoRepository
from app.modules.fornecedores.repository import FornecedorRepository
from app.modules.estoque.service import EstoqueService
from app.modules.estoque.schemas import EntradaEstoqueCreate
from app.modules.financeiro.service import FinanceiroService
from app.modules.financeiro.schemas import ContaPagarCreate
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


class ComprasService:
    """Service para regras de negócio de Compras"""

    def __init__(self, session: AsyncSession):
        self.repository = PedidoCompraRepository(session)
        self.produto_repository = ProdutoRepository(session)
        self.fornecedor_repository = FornecedorRepository(session)
        self.estoque_service = EstoqueService(session)
        self.financeiro_service = FinanceiroService(session)
        self.session = session

    # ============================================
    # VALIDAÇÕES
    # ============================================

    async def validar_fornecedor_existe(self, fornecedor_id: int):
        """
        Valida se o fornecedor existe e está ativo

        Args:
            fornecedor_id: ID do fornecedor

        Raises:
            NotFoundException: Se fornecedor não existe
            ValidationException: Se fornecedor está inativo
        """
        fornecedor = await self.fornecedor_repository.get_by_id(fornecedor_id)
        if not fornecedor:
            raise NotFoundException(f"Fornecedor {fornecedor_id} não encontrado")

        if not fornecedor.ativo:
            raise ValidationException(
                f"Fornecedor '{fornecedor.razao_social}' está inativo e não pode receber pedidos"
            )

        return fornecedor

    async def validar_produto_existe(self, produto_id: int):
        """
        Valida se o produto existe e está ativo

        Args:
            produto_id: ID do produto

        Raises:
            NotFoundException: Se produto não existe
            ValidationException: Se produto está inativo
        """
        produto = await self.produto_repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        if not produto.ativo:
            raise ValidationException(
                f"Produto '{produto.descricao}' está inativo e não pode ser comprado"
            )

        return produto

    # ============================================
    # OPERAÇÕES DE PEDIDO
    # ============================================

    async def criar_pedido_compra(
        self, pedido_data: PedidoCompraCreate
    ) -> PedidoCompraResponse:
        """
        Cria um pedido de compra completo com itens

        Regras:
        - Fornecedor deve existir e estar ativo
        - Todos os produtos devem existir e estar ativos
        - Calcula subtotal somando subtotal de todos os itens
        - Calcula valor_total = subtotal - desconto + valor_frete
        - Status inicial é PENDENTE

        Args:
            pedido_data: Dados do pedido com itens

        Returns:
            PedidoCompraResponse com pedido criado
        """
        # Valida fornecedor
        await self.validar_fornecedor_existe(pedido_data.fornecedor_id)

        # Valida todos os produtos e calcula subtotal
        subtotal = 0.0
        for item in pedido_data.itens:
            await self.validar_produto_existe(item.produto_id)
            subtotal_item = item.quantidade_solicitada * item.preco_unitario
            subtotal += subtotal_item

        # Calcula valor total
        valor_total = subtotal - pedido_data.desconto + pedido_data.valor_frete

        if valor_total < 0:
            raise ValidationException("Valor total do pedido não pode ser negativo")

        # Cria pedido
        pedido_dict = pedido_data.model_dump(exclude={"itens"})
        pedido_dict["subtotal"] = subtotal
        pedido_dict["valor_total"] = valor_total
        pedido_dict["status"] = StatusPedidoCompra.PENDENTE

        pedido = await self.repository.create_pedido(pedido_dict)

        # Cria itens
        for item_data in pedido_data.itens:
            item_dict = item_data.model_dump()
            item_dict["pedido_id"] = pedido.id
            item_dict["subtotal_item"] = (
                item_data.quantidade_solicitada * item_data.preco_unitario
            )
            item_dict["quantidade_recebida"] = 0.0
            await self.repository.create_item_pedido(item_dict)

        await self.session.flush()
        await self.session.refresh(pedido)

        return PedidoCompraResponse.model_validate(pedido)

    async def get_pedido(self, pedido_id: int) -> PedidoCompraResponse:
        """
        Busca pedido por ID

        Args:
            pedido_id: ID do pedido

        Returns:
            PedidoCompraResponse

        Raises:
            NotFoundException: Se pedido não encontrado
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido de compra {pedido_id} não encontrado")

        return PedidoCompraResponse.model_validate(pedido)

    async def list_pedidos(
        self,
        page: int = 1,
        page_size: int = 50,
        fornecedor_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> PedidoCompraList:
        """
        Lista pedidos com paginação e filtros

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            fornecedor_id: Filtrar por fornecedor (opcional)
            status: Filtrar por status (opcional)

        Returns:
            PedidoCompraList com lista paginada
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Converte status string para enum se fornecido
        status_enum = None
        if status:
            try:
                status_enum = StatusPedidoCompra[status]
            except KeyError:
                raise ValidationException(f"Status '{status}' inválido")

        # Busca pedidos e total
        pedidos = await self.repository.get_all(skip, page_size, fornecedor_id, status_enum)
        total = await self.repository.count(fornecedor_id, status_enum)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return PedidoCompraList(
            items=[PedidoCompraResponse.model_validate(p) for p in pedidos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def atualizar_pedido(
        self, pedido_id: int, pedido_data: PedidoCompraUpdate
    ) -> PedidoCompraResponse:
        """
        Atualiza um pedido de compra

        Regras:
        - Não pode atualizar pedido já recebido ou cancelado
        - Se atualizar desconto ou frete, recalcula valor_total

        Args:
            pedido_id: ID do pedido
            pedido_data: Dados para atualização

        Returns:
            PedidoCompraResponse atualizado
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido de compra {pedido_id} não encontrado")

        if pedido.status in [StatusPedidoCompra.RECEBIDO, StatusPedidoCompra.CANCELADO]:
            raise BusinessRuleException(
                f"Não é possível atualizar pedido com status '{pedido.status.value}'"
            )

        # Valida fornecedor se foi alterado
        if pedido_data.fornecedor_id:
            await self.validar_fornecedor_existe(pedido_data.fornecedor_id)

        pedido_atualizado = await self.repository.update(pedido_id, pedido_data)

        # Recalcula valor_total se desconto ou frete foram alterados
        if pedido_data.desconto is not None or pedido_data.valor_frete is not None:
            pedido_atualizado.valor_total = (
                float(pedido_atualizado.subtotal)
                - float(pedido_atualizado.desconto)
                + float(pedido_atualizado.valor_frete)
            )
            await self.session.flush()
            await self.session.refresh(pedido_atualizado)

        return PedidoCompraResponse.model_validate(pedido_atualizado)

    async def aprovar_pedido(self, pedido_id: int) -> PedidoCompraResponse:
        """
        Aprova um pedido de compra

        Regras:
        - Pedido deve estar com status PENDENTE
        - Altera status para APROVADO

        Args:
            pedido_id: ID do pedido

        Returns:
            PedidoCompraResponse aprovado
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido de compra {pedido_id} não encontrado")

        if pedido.status != StatusPedidoCompra.PENDENTE:
            raise BusinessRuleException(
                f"Apenas pedidos PENDENTES podem ser aprovados. Status atual: {pedido.status.value}"
            )

        pedido_aprovado = await self.repository.atualizar_status(
            pedido_id, StatusPedidoCompra.APROVADO
        )

        return PedidoCompraResponse.model_validate(pedido_aprovado)

    async def receber_pedido(
        self, pedido_id: int, recebimento_data: ReceberPedidoRequest
    ) -> PedidoCompraResponse:
        """
        Registra recebimento de pedido (total ou parcial)

        Regras:
        - Pedido deve estar APROVADO ou RECEBIDO_PARCIAL
        - Cria entrada de estoque para cada item recebido via EstoqueService
        - Cria conta a pagar via FinanceiroService (proporcional ao recebido)
        - Atualiza quantidade_recebida dos itens
        - Se todos itens recebidos completamente: status = RECEBIDO
        - Se apenas alguns itens ou parcialmente: status = RECEBIDO_PARCIAL
        - Registra data_entrega_real

        Args:
            pedido_id: ID do pedido
            recebimento_data: Dados do recebimento

        Returns:
            PedidoCompraResponse atualizado
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido de compra {pedido_id} não encontrado")

        if pedido.status not in [
            StatusPedidoCompra.APROVADO,
            StatusPedidoCompra.RECEBIDO_PARCIAL,
        ]:
            raise BusinessRuleException(
                f"Apenas pedidos APROVADOS ou RECEBIDO_PARCIAL podem ser recebidos. "
                f"Status atual: {pedido.status.value}"
            )

        # Busca todos os itens do pedido
        itens_pedido = await self.repository.get_itens_pedido(pedido_id)
        itens_dict = {item.id: item for item in itens_pedido}

        valor_recebido = 0.0

        # Processa cada item recebido
        for item_recebido in recebimento_data.itens_recebidos:
            item_id = item_recebido["item_id"]
            quantidade_recebida = float(item_recebido["quantidade_recebida"])

            # Valida se item existe no pedido
            if item_id not in itens_dict:
                raise ValidationException(
                    f"Item {item_id} não pertence ao pedido {pedido_id}"
                )

            item = itens_dict[item_id]

            # Valida quantidade
            quantidade_pendente = float(item.quantidade_solicitada) - float(
                item.quantidade_recebida
            )
            if quantidade_recebida > quantidade_pendente:
                raise ValidationException(
                    f"Quantidade recebida ({quantidade_recebida}) do item {item_id} "
                    f"excede a quantidade pendente ({quantidade_pendente})"
                )

            # Cria entrada de estoque
            entrada_data = EntradaEstoqueCreate(
                produto_id=item.produto_id,
                quantidade=quantidade_recebida,
                custo_unitario=float(item.preco_unitario),
                documento_referencia=f"PEDIDO-{pedido_id}",
                observacao=f"Recebimento pedido compra #{pedido_id}",
                usuario_id=None,  # TODO: pegar do contexto de autenticação
            )
            await self.estoque_service.entrada_estoque(entrada_data)

            # Atualiza quantidade recebida do item
            await self.repository.atualizar_quantidade_recebida(item_id, quantidade_recebida)

            # Calcula valor recebido
            valor_recebido += quantidade_recebida * float(item.preco_unitario)

        # Cria conta a pagar proporcional ao valor recebido
        # Aplica desconto e frete proporcionalmente
        proporcao = valor_recebido / float(pedido.subtotal) if float(pedido.subtotal) > 0 else 1.0
        desconto_proporcional = float(pedido.desconto) * proporcao
        frete_proporcional = float(pedido.valor_frete) * proporcao
        valor_conta = valor_recebido - desconto_proporcional + frete_proporcional

        # Cria conta a pagar
        conta_data = ContaPagarCreate(
            fornecedor_id=pedido.fornecedor_id,
            descricao=f"Compra - Pedido #{pedido_id} - Recebimento {recebimento_data.data_recebimento}",
            valor_original=valor_conta,
            data_emissao=recebimento_data.data_recebimento,
            data_vencimento=recebimento_data.data_recebimento,  # TODO: adicionar prazo de pagamento
            documento=f"PEDIDO-{pedido_id}",
            categoria_financeira="COMPRAS",
            observacoes=recebimento_data.observacao,
        )
        await self.financeiro_service.criar_conta_pagar(conta_data)

        # Atualiza data de entrega real
        await self.repository.registrar_recebimento(pedido_id, recebimento_data.data_recebimento)

        # Verifica se pedido foi totalmente recebido
        await self.session.refresh(pedido)
        itens_atualizados = await self.repository.get_itens_pedido(pedido_id)

        totalmente_recebido = all(
            float(item.quantidade_recebida) >= float(item.quantidade_solicitada)
            for item in itens_atualizados
        )

        novo_status = (
            StatusPedidoCompra.RECEBIDO
            if totalmente_recebido
            else StatusPedidoCompra.RECEBIDO_PARCIAL
        )

        pedido_atualizado = await self.repository.atualizar_status(pedido_id, novo_status)

        return PedidoCompraResponse.model_validate(pedido_atualizado)

    async def cancelar_pedido(self, pedido_id: int) -> PedidoCompraResponse:
        """
        Cancela um pedido de compra

        Regras:
        - Não pode cancelar pedido já recebido (total ou parcial)
        - Altera status para CANCELADO

        Args:
            pedido_id: ID do pedido

        Returns:
            PedidoCompraResponse cancelado
        """
        pedido = await self.repository.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido de compra {pedido_id} não encontrado")

        if pedido.status in [
            StatusPedidoCompra.RECEBIDO,
            StatusPedidoCompra.RECEBIDO_PARCIAL,
        ]:
            raise BusinessRuleException(
                f"Não é possível cancelar pedido com status '{pedido.status.value}'"
            )

        pedido_cancelado = await self.repository.atualizar_status(
            pedido_id, StatusPedidoCompra.CANCELADO
        )

        return PedidoCompraResponse.model_validate(pedido_cancelado)

    async def get_pedidos_atrasados(
        self, page: int = 1, page_size: int = 50
    ) -> PedidoCompraList:
        """
        Lista pedidos atrasados (data_entrega_prevista < hoje e não recebidos)

        Args:
            page: Página atual
            page_size: Quantidade de itens por página

        Returns:
            PedidoCompraList com pedidos atrasados
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        pedidos = await self.repository.get_atrasados(skip, page_size)

        # Conta total de atrasados
        todos_atrasados = await self.repository.get_atrasados(0, 10000)
        total = len(todos_atrasados)

        pages = math.ceil(total / page_size) if total > 0 else 1

        return PedidoCompraList(
            items=[PedidoCompraResponse.model_validate(p) for p in pedidos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # ============================================
    # SUGESTÃO DE COMPRAS
    # ============================================

    async def sugerir_compras(self) -> SugestaoCompraList:
        """
        Gera sugestão automática de compras

        Regras:
        - Analisa produtos com estoque_atual < estoque_minimo
        - Considera curva ABC (prioriza classe A)
        - Quantidade sugerida = (estoque_minimo * 2) - estoque_atual
        - Classe ABC baseada em valor em estoque (A=alto, B=médio, C=baixo)
        - Ordena por classe ABC (A primeiro) e depois por déficit de estoque

        Returns:
            SugestaoCompraList com produtos sugeridos
        """
        # Busca todos os produtos abaixo do estoque mínimo
        produtos_baixo_estoque = await self.produto_repository.get_abaixo_estoque_minimo(
            skip=0, limit=1000
        )

        sugestoes = []
        valor_total_geral = 0.0

        for produto in produtos_baixo_estoque:
            # Calcula quantidade sugerida
            quantidade_sugerida = (float(produto.estoque_minimo) * 2) - float(
                produto.estoque_atual
            )
            if quantidade_sugerida <= 0:
                continue

            # Calcula valor total da sugestão
            valor_total_sugestao = quantidade_sugerida * float(produto.preco_custo)
            valor_total_geral += valor_total_sugestao

            # Calcula valor do estoque atual para classificação ABC
            valor_estoque_atual = float(produto.estoque_atual) * float(produto.preco_custo)

            # Classificação ABC simplificada por valor em estoque
            # A: produtos com valor alto (>= R$ 1000)
            # B: produtos com valor médio (>= R$ 200 e < R$ 1000)
            # C: produtos com valor baixo (< R$ 200)
            if valor_estoque_atual >= 1000 or float(produto.preco_custo) >= 100:
                classe_abc = "A"
            elif valor_estoque_atual >= 200 or float(produto.preco_custo) >= 20:
                classe_abc = "B"
            else:
                classe_abc = "C"

            sugestao = SugestaoCompraResponse(
                produto_id=produto.id,
                produto_descricao=produto.descricao,
                codigo_barras=produto.codigo_barras,
                estoque_atual=float(produto.estoque_atual),
                estoque_minimo=float(produto.estoque_minimo),
                quantidade_sugerida=quantidade_sugerida,
                preco_custo=float(produto.preco_custo),
                valor_total_sugestao=valor_total_sugestao,
                classe_abc=classe_abc,
            )
            sugestoes.append(sugestao)

        # Ordena por classe ABC (A primeiro) e depois por quantidade sugerida (maior primeiro)
        sugestoes_ordenadas = sorted(
            sugestoes,
            key=lambda x: (
                {"A": 0, "B": 1, "C": 2}[x.classe_abc],
                -x.quantidade_sugerida,
            ),
        )

        return SugestaoCompraList(
            items=sugestoes_ordenadas,
            total=len(sugestoes_ordenadas),
            valor_total_geral=valor_total_geral,
        )
