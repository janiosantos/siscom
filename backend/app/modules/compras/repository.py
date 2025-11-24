"""
Repository para Compras
"""
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.compras.models import PedidoCompra, ItemPedidoCompra, StatusPedidoCompra
from app.modules.compras.schemas import (
    PedidoCompraCreate,
    PedidoCompraUpdate,
    ItemPedidoCompraCreate,
)


class PedidoCompraRepository:
    """Repository para operações de banco de dados de Pedidos de Compra"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ============================================
    # OPERAÇÕES DE PEDIDO
    # ============================================

    async def create_pedido(self, pedido_data: dict) -> PedidoCompra:
        """
        Cria um novo pedido de compra (sem itens)

        Args:
            pedido_data: Dicionário com dados do pedido

        Returns:
            PedidoCompra criado
        """
        pedido = PedidoCompra(**pedido_data)
        self.session.add(pedido)
        await self.session.flush()
        await self.session.refresh(pedido)
        return pedido

    async def create_item_pedido(self, item_data: dict) -> ItemPedidoCompra:
        """
        Cria um novo item de pedido

        Args:
            item_data: Dicionário com dados do item

        Returns:
            ItemPedidoCompra criado
        """
        item = ItemPedidoCompra(**item_data)
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, pedido_id: int) -> Optional[PedidoCompra]:
        """
        Busca pedido por ID

        Args:
            pedido_id: ID do pedido

        Returns:
            PedidoCompra ou None se não encontrado
        """
        result = await self.session.execute(
            select(PedidoCompra)
            .options(
                selectinload(PedidoCompra.fornecedor),
                selectinload(PedidoCompra.itens).selectinload(ItemPedidoCompra.produto)
            )
            .where(PedidoCompra.id == pedido_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        fornecedor_id: Optional[int] = None,
        status: Optional[StatusPedidoCompra] = None,
    ) -> List[PedidoCompra]:
        """
        Lista todos os pedidos com paginação e filtros

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            fornecedor_id: Filtrar por fornecedor
            status: Filtrar por status

        Returns:
            Lista de PedidoCompra
        """
        query = select(PedidoCompra)

        if fornecedor_id:
            query = query.where(PedidoCompra.fornecedor_id == fornecedor_id)

        if status:
            query = query.where(PedidoCompra.status == status)

        query = query.offset(skip).limit(limit).order_by(PedidoCompra.data_pedido.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        fornecedor_id: Optional[int] = None,
        status: Optional[StatusPedidoCompra] = None,
    ) -> int:
        """
        Conta total de pedidos

        Args:
            fornecedor_id: Filtrar por fornecedor
            status: Filtrar por status

        Returns:
            Total de pedidos
        """
        query = select(func.count(PedidoCompra.id))

        if fornecedor_id:
            query = query.where(PedidoCompra.fornecedor_id == fornecedor_id)

        if status:
            query = query.where(PedidoCompra.status == status)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(
        self, pedido_id: int, pedido_data: PedidoCompraUpdate
    ) -> Optional[PedidoCompra]:
        """
        Atualiza um pedido

        Args:
            pedido_id: ID do pedido
            pedido_data: Dados para atualização

        Returns:
            PedidoCompra atualizado ou None
        """
        pedido = await self.get_by_id(pedido_id)
        if not pedido:
            return None

        update_data = pedido_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pedido, field, value)

        await self.session.flush()
        await self.session.refresh(pedido)
        return pedido

    async def atualizar_status(
        self, pedido_id: int, status: StatusPedidoCompra
    ) -> Optional[PedidoCompra]:
        """
        Atualiza status do pedido

        Args:
            pedido_id: ID do pedido
            status: Novo status

        Returns:
            PedidoCompra atualizado ou None
        """
        pedido = await self.get_by_id(pedido_id)
        if not pedido:
            return None

        pedido.status = status
        await self.session.commit()
        # Recarregar pedido com todos os relacionamentos após commit
        return await self.get_by_id(pedido_id)

    async def get_por_fornecedor(
        self, fornecedor_id: int, skip: int = 0, limit: int = 100
    ) -> List[PedidoCompra]:
        """
        Busca pedidos por fornecedor

        Args:
            fornecedor_id: ID do fornecedor
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de PedidoCompra
        """
        query = (
            select(PedidoCompra)
            .where(PedidoCompra.fornecedor_id == fornecedor_id)
            .offset(skip)
            .limit(limit)
            .order_by(PedidoCompra.data_pedido.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_por_status(
        self, status: StatusPedidoCompra, skip: int = 0, limit: int = 100
    ) -> List[PedidoCompra]:
        """
        Busca pedidos por status

        Args:
            status: Status do pedido
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de PedidoCompra
        """
        query = (
            select(PedidoCompra)
            .where(PedidoCompra.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(PedidoCompra.data_pedido.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pendentes(self, skip: int = 0, limit: int = 100) -> List[PedidoCompra]:
        """
        Busca pedidos pendentes

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de PedidoCompra pendentes
        """
        return await self.get_por_status(StatusPedidoCompra.PENDENTE, skip, limit)

    async def get_atrasados(self, skip: int = 0, limit: int = 100) -> List[PedidoCompra]:
        """
        Busca pedidos atrasados (data_entrega_prevista < hoje e status != RECEBIDO e != CANCELADO)

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de PedidoCompra atrasados
        """
        hoje = date.today()
        query = (
            select(PedidoCompra)
            .where(
                and_(
                    PedidoCompra.data_entrega_prevista < hoje,
                    PedidoCompra.status.not_in(
                        [StatusPedidoCompra.RECEBIDO, StatusPedidoCompra.CANCELADO]
                    ),
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(PedidoCompra.data_entrega_prevista)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def registrar_recebimento(
        self, pedido_id: int, data_recebimento: date
    ) -> Optional[PedidoCompra]:
        """
        Registra data de recebimento do pedido

        Args:
            pedido_id: ID do pedido
            data_recebimento: Data do recebimento

        Returns:
            PedidoCompra atualizado ou None
        """
        pedido = await self.get_by_id(pedido_id)
        if not pedido:
            return None

        pedido.data_entrega_real = data_recebimento
        await self.session.flush()
        await self.session.refresh(pedido)
        return pedido

    # ============================================
    # OPERAÇÕES DE ITENS
    # ============================================

    async def get_itens_pedido(self, pedido_id: int) -> List[ItemPedidoCompra]:
        """
        Busca todos os itens de um pedido

        Args:
            pedido_id: ID do pedido

        Returns:
            Lista de ItemPedidoCompra
        """
        query = select(ItemPedidoCompra).where(ItemPedidoCompra.pedido_id == pedido_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_item_by_id(self, item_id: int) -> Optional[ItemPedidoCompra]:
        """
        Busca item de pedido por ID

        Args:
            item_id: ID do item

        Returns:
            ItemPedidoCompra ou None
        """
        result = await self.session.execute(
            select(ItemPedidoCompra).where(ItemPedidoCompra.id == item_id)
        )
        return result.scalar_one_or_none()

    async def atualizar_quantidade_recebida(
        self, item_id: int, quantidade_recebida: float
    ) -> Optional[ItemPedidoCompra]:
        """
        Atualiza quantidade recebida de um item

        Args:
            item_id: ID do item
            quantidade_recebida: Quantidade recebida a somar

        Returns:
            ItemPedidoCompra atualizado ou None
        """
        item = await self.get_item_by_id(item_id)
        if not item:
            return None

        item.quantidade_recebida = float(item.quantidade_recebida) + quantidade_recebida
        await self.session.flush()
        await self.session.refresh(item)
        return item
