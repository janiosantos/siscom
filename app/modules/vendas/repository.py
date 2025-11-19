"""
Repository para Vendas
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.vendas.models import Venda, ItemVenda, StatusVenda
from app.modules.vendas.schemas import VendaCreate, ItemVendaCreate


class VendaRepository:
    """Repository para operações de banco de dados de Vendas"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_venda(self, venda_data: VendaCreate) -> Venda:
        """
        Cria uma nova venda (sem itens)

        Args:
            venda_data: Dados da venda

        Returns:
            Venda criada
        """
        venda_dict = venda_data.model_dump(exclude={"itens"})
        venda = Venda(**venda_dict)
        self.session.add(venda)
        await self.session.flush()
        await self.session.refresh(venda)
        return venda

    async def create_item_venda(
        self, venda_id: int, item_data: ItemVendaCreate, subtotal: float, total: float
    ) -> ItemVenda:
        """
        Cria um item de venda

        Args:
            venda_id: ID da venda
            item_data: Dados do item
            subtotal: Subtotal do item (quantidade * preco_unitario)
            total: Total do item (subtotal - desconto)

        Returns:
            Item criado
        """
        item = ItemVenda(
            venda_id=venda_id,
            produto_id=item_data.produto_id,
            quantidade=item_data.quantidade,
            preco_unitario=item_data.preco_unitario,
            desconto_item=item_data.desconto_item,
            subtotal_item=subtotal,
            total_item=total,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, venda_id: int) -> Optional[Venda]:
        """
        Busca venda por ID com seus itens

        Args:
            venda_id: ID da venda

        Returns:
            Venda com itens ou None
        """
        result = await self.session.execute(
            select(Venda)
            .options(selectinload(Venda.itens))
            .where(Venda.id == venda_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[StatusVenda] = None,
        cliente_id: Optional[int] = None,
        vendedor_id: Optional[int] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> List[Venda]:
        """
        Lista todas as vendas com paginação e filtros

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            status: Filtrar por status
            cliente_id: Filtrar por cliente
            vendedor_id: Filtrar por vendedor
            data_inicio: Data inicial do filtro
            data_fim: Data final do filtro

        Returns:
            Lista de vendas
        """
        query = select(Venda).options(selectinload(Venda.itens))

        if status:
            query = query.where(Venda.status == status)

        if cliente_id:
            query = query.where(Venda.cliente_id == cliente_id)

        if vendedor_id:
            query = query.where(Venda.vendedor_id == vendedor_id)

        if data_inicio:
            query = query.where(Venda.data_venda >= data_inicio)

        if data_fim:
            query = query.where(Venda.data_venda <= data_fim)

        query = query.offset(skip).limit(limit).order_by(Venda.data_venda.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        status: Optional[StatusVenda] = None,
        cliente_id: Optional[int] = None,
        vendedor_id: Optional[int] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> int:
        """
        Conta total de vendas

        Args:
            status: Filtrar por status
            cliente_id: Filtrar por cliente
            vendedor_id: Filtrar por vendedor
            data_inicio: Data inicial do filtro
            data_fim: Data final do filtro

        Returns:
            Total de vendas
        """
        query = select(func.count(Venda.id))

        if status:
            query = query.where(Venda.status == status)

        if cliente_id:
            query = query.where(Venda.cliente_id == cliente_id)

        if vendedor_id:
            query = query.where(Venda.vendedor_id == vendedor_id)

        if data_inicio:
            query = query.where(Venda.data_venda >= data_inicio)

        if data_fim:
            query = query.where(Venda.data_venda <= data_fim)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_vendas_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Venda]:
        """
        Busca vendas por período

        Args:
            data_inicio: Data inicial
            data_fim: Data final
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de vendas no período
        """
        query = (
            select(Venda)
            .options(selectinload(Venda.itens))
            .where(
                and_(
                    Venda.data_venda >= data_inicio,
                    Venda.data_venda <= data_fim,
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(Venda.data_venda.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_vendas_por_cliente(
        self, cliente_id: int, skip: int = 0, limit: int = 100
    ) -> List[Venda]:
        """
        Busca vendas por cliente

        Args:
            cliente_id: ID do cliente
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de vendas do cliente
        """
        query = (
            select(Venda)
            .options(selectinload(Venda.itens))
            .where(Venda.cliente_id == cliente_id)
            .offset(skip)
            .limit(limit)
            .order_by(Venda.data_venda.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_vendas_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        status: Optional[StatusVenda] = None,
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
        query = select(func.sum(Venda.valor_total)).where(
            and_(
                Venda.data_venda >= data_inicio,
                Venda.data_venda <= data_fim,
            )
        )

        if status:
            query = query.where(Venda.status == status)

        result = await self.session.execute(query)
        total = result.scalar_one_or_none()
        return float(total) if total else 0.0

    async def get_itens_venda(self, venda_id: int) -> List[ItemVenda]:
        """
        Busca itens de uma venda

        Args:
            venda_id: ID da venda

        Returns:
            Lista de itens da venda
        """
        result = await self.session.execute(
            select(ItemVenda).where(ItemVenda.venda_id == venda_id)
        )
        return list(result.scalars().all())

    async def cancelar_venda(self, venda_id: int) -> Optional[Venda]:
        """
        Cancela uma venda (altera status para CANCELADA)

        Args:
            venda_id: ID da venda

        Returns:
            Venda cancelada ou None
        """
        venda = await self.get_by_id(venda_id)
        if not venda:
            return None

        venda.status = StatusVenda.CANCELADA
        await self.session.flush()
        await self.session.refresh(venda)
        return venda

    async def finalizar_venda(self, venda_id: int) -> Optional[Venda]:
        """
        Finaliza uma venda (altera status para FINALIZADA)

        Args:
            venda_id: ID da venda

        Returns:
            Venda finalizada ou None
        """
        venda = await self.get_by_id(venda_id)
        if not venda:
            return None

        venda.status = StatusVenda.FINALIZADA
        await self.session.flush()
        await self.session.refresh(venda)
        return venda

    async def atualizar_totais_venda(
        self, venda_id: int, subtotal: float, desconto: float, valor_total: float
    ) -> Optional[Venda]:
        """
        Atualiza os totais de uma venda

        Args:
            venda_id: ID da venda
            subtotal: Subtotal
            desconto: Desconto
            valor_total: Valor total

        Returns:
            Venda atualizada ou None
        """
        venda = await self.get_by_id(venda_id)
        if not venda:
            return None

        venda.subtotal = subtotal
        venda.desconto = desconto
        venda.valor_total = valor_total
        await self.session.flush()
        await self.session.refresh(venda)
        return venda
