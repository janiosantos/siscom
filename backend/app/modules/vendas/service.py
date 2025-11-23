"""
Service Layer para Vendas
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.vendas.repository import VendaRepository
from app.modules.vendas.models import StatusVenda
from app.modules.vendas.schemas import (
    VendaCreate,
    VendaUpdate,
    VendaResponse,
    VendaList,
    ItemVendaCreate,
    ItemVendaResponse,
    StatusVendaEnum,
)
from app.modules.produtos.repository import ProdutoRepository
from app.modules.estoque.service import EstoqueService
from app.modules.estoque.schemas import SaidaEstoqueCreate
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


class VendasService:
    """Service para regras de negócio de Vendas"""

    def __init__(self, session: AsyncSession):
        self.repository = VendaRepository(session)
        self.produto_repository = ProdutoRepository(session)
        self.estoque_service = EstoqueService(session)
        self.session = session

    async def criar_venda(self, venda_data: VendaCreate) -> VendaResponse:
        """
        Cria uma venda completa com itens

        Regras:
        - Valida se todos os produtos existem
        - Valida estoque disponível para todos os itens
        - Calcula totais (subtotal, desconto, valor_total)
        - Registra saídas de estoque automaticamente
        - Cria a venda com status PENDENTE

        Args:
            venda_data: Dados da venda com itens

        Returns:
            VendaResponse com a venda criada

        Raises:
            NotFoundException: Se produto não existe
            ValidationException: Se validações falharem
            InsufficientStockException: Se não há estoque suficiente
        """
        # Valida que há itens
        if not venda_data.itens or len(venda_data.itens) == 0:
            raise ValidationException("Venda deve ter pelo menos um item")

        # Valida produtos e estoque para todos os itens
        for item in venda_data.itens:
            # Verifica se produto existe
            produto = await self.produto_repository.get_by_id(item.produto_id)
            if not produto:
                raise NotFoundException(f"Produto {item.produto_id} não encontrado")

            if not produto.ativo:
                raise ValidationException(
                    f"Produto '{produto.descricao}' está inativo e não pode ser vendido"
                )

            # Valida estoque disponível
            await self.estoque_service.validar_estoque_suficiente(
                item.produto_id, item.quantidade
            )

        # Cria a venda (sem itens)
        venda = await self.repository.create_venda(venda_data)

        # Calcula subtotal da venda
        subtotal = 0.0

        # Cria itens e registra saídas de estoque
        for item_data in venda_data.itens:
            # Calcula subtotal do item
            subtotal_item = item_data.quantidade * item_data.preco_unitario

            # Calcula total do item (subtotal - desconto)
            total_item = subtotal_item - item_data.desconto_item

            # Cria item da venda
            await self.repository.create_item_venda(
                venda_id=venda.id,
                item_data=item_data,
                subtotal=subtotal_item,
                total=total_item,
            )

            # Acumula subtotal da venda
            subtotal += subtotal_item

            # Registra saída de estoque
            saida_data = SaidaEstoqueCreate(
                produto_id=item_data.produto_id,
                quantidade=item_data.quantidade,
                custo_unitario=item_data.preco_unitario,
                documento_referencia=f"VENDA-{venda.id}",
                observacao=f"Venda #{venda.id}",
                usuario_id=venda_data.vendedor_id,
            )
            await self.estoque_service.saida_estoque(saida_data)

        # Calcula valor total da venda (subtotal - desconto)
        valor_total = subtotal - venda_data.desconto

        # Valida que valor total não seja negativo
        if valor_total < 0:
            raise ValidationException(
                "Desconto não pode ser maior que o subtotal da venda"
            )

        # Atualiza totais da venda
        await self.repository.atualizar_totais_venda(
            venda_id=venda.id,
            subtotal=subtotal,
            desconto=venda_data.desconto,
            valor_total=valor_total,
        )

        # Commit da transação
        await self.session.flush()

        # Busca venda completa com itens
        venda_completa = await self.repository.get_by_id(venda.id)

        return VendaResponse.model_validate(venda_completa)

    async def finalizar_venda(self, venda_id: int) -> VendaResponse:
        """
        Finaliza uma venda (altera status para FINALIZADA)

        Regras:
        - Venda deve existir
        - Venda deve estar PENDENTE
        - Altera status para FINALIZADA
        - TODO: Gera conta a receber (implementar quando houver módulo financeiro)

        Args:
            venda_id: ID da venda

        Returns:
            VendaResponse com a venda finalizada

        Raises:
            NotFoundException: Se venda não existe
            BusinessRuleException: Se venda não pode ser finalizada
        """
        venda = await self.repository.get_by_id(venda_id)
        if not venda:
            raise NotFoundException(f"Venda {venda_id} não encontrada")

        if venda.status != StatusVenda.PENDENTE:
            raise BusinessRuleException(
                f"Venda não pode ser finalizada. Status atual: {venda.status}"
            )

        # Finaliza venda
        venda = await self.repository.finalizar_venda(venda_id)

        # TODO: Gerar conta a receber quando módulo financeiro estiver pronto

        await self.session.flush()

        return VendaResponse.model_validate(venda)

    async def cancelar_venda(self, venda_id: int) -> VendaResponse:
        """
        Cancela uma venda e devolve o estoque

        Regras:
        - Venda deve existir
        - Venda deve estar PENDENTE ou FINALIZADA
        - Altera status para CANCELADA
        - Devolve estoque (registra entradas de estoque)

        Args:
            venda_id: ID da venda

        Returns:
            VendaResponse com a venda cancelada

        Raises:
            NotFoundException: Se venda não existe
            BusinessRuleException: Se venda não pode ser cancelada
        """
        venda = await self.repository.get_by_id(venda_id)
        if not venda:
            raise NotFoundException(f"Venda {venda_id} não encontrada")

        if venda.status == StatusVenda.CANCELADA:
            raise BusinessRuleException("Venda já está cancelada")

        # Devolve estoque (registra ajustes de entrada para cada item)
        for item in venda.itens:
            # Usa ajuste de estoque para devolver o produto
            from app.modules.estoque.schemas import AjusteEstoqueCreate

            ajuste_data = AjusteEstoqueCreate(
                produto_id=item.produto_id,
                quantidade=item.quantidade,  # Quantidade positiva para adicionar ao estoque
                custo_unitario=item.preco_unitario,
                observacao=f"Devolução por cancelamento da Venda #{venda_id}",
                usuario_id=venda.vendedor_id,
            )
            await self.estoque_service.ajuste_estoque(ajuste_data)

        # Cancela venda
        venda = await self.repository.cancelar_venda(venda_id)

        await self.session.flush()

        return VendaResponse.model_validate(venda)

    async def get_venda(self, venda_id: int) -> VendaResponse:
        """
        Busca venda completa com itens

        Args:
            venda_id: ID da venda

        Returns:
            VendaResponse com a venda completa

        Raises:
            NotFoundException: Se venda não existe
        """
        venda = await self.repository.get_by_id(venda_id)
        if not venda:
            raise NotFoundException(f"Venda {venda_id} não encontrada")

        return VendaResponse.model_validate(venda)

    async def list_vendas(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[StatusVendaEnum] = None,
        cliente_id: Optional[int] = None,
        vendedor_id: Optional[int] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> VendaList:
        """
        Lista vendas com paginação e filtros

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            status: Filtrar por status (opcional)
            cliente_id: Filtrar por cliente (opcional)
            vendedor_id: Filtrar por vendedor (opcional)
            data_inicio: Data inicial do filtro (opcional)
            data_fim: Data final do filtro (opcional)

        Returns:
            VendaList com lista paginada
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Converte StatusVendaEnum para StatusVenda se necessário
        status_db = None
        if status:
            status_db = StatusVenda(status.value)

        # Busca vendas e total
        vendas = await self.repository.get_all(
            skip=skip,
            limit=page_size,
            status=status_db,
            cliente_id=cliente_id,
            vendedor_id=vendedor_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        total = await self.repository.count(
            status=status_db,
            cliente_id=cliente_id,
            vendedor_id=vendedor_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return VendaList(
            items=[VendaResponse.model_validate(v) for v in vendas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_vendas_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        page: int = 1,
        page_size: int = 50,
    ) -> VendaList:
        """
        Busca vendas por período

        Args:
            data_inicio: Data inicial
            data_fim: Data final
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página

        Returns:
            VendaList com vendas do período
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        vendas = await self.repository.get_vendas_periodo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            skip=skip,
            limit=page_size,
        )

        total = await self.repository.count(
            data_inicio=data_inicio, data_fim=data_fim
        )

        pages = math.ceil(total / page_size) if total > 0 else 1

        return VendaList(
            items=[VendaResponse.model_validate(v) for v in vendas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_total_vendas_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        status: Optional[StatusVendaEnum] = None,
    ) -> float:
        """
        Calcula total de vendas em um período

        Args:
            data_inicio: Data inicial
            data_fim: Data final
            status: Filtrar por status (opcional)

        Returns:
            Total de vendas no período
        """
        status_db = None
        if status:
            status_db = StatusVenda(status.value)

        return await self.repository.get_total_vendas_periodo(
            data_inicio=data_inicio, data_fim=data_fim, status=status_db
        )
