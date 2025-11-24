"""
Repository para Pedidos de Venda
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date

from .models import PedidoVenda, ItemPedidoVenda, StatusPedidoVenda


class PedidoVendaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, pedido_data: dict) -> PedidoVenda:
        """Criar novo pedido de venda"""
        pedido = PedidoVenda(**pedido_data)
        self.db.add(pedido)
        await self.db.commit()
        await self.db.refresh(pedido)
        return pedido

    async def get_by_id(self, pedido_id: int) -> Optional[PedidoVenda]:
        """Buscar pedido por ID"""
        result = await self.db.execute(
            select(PedidoVenda)
            .options(selectinload(PedidoVenda.itens))
            .where(PedidoVenda.id == pedido_id)
        )
        return result.scalar_one_or_none()

    async def get_by_numero(self, numero_pedido: str) -> Optional[PedidoVenda]:
        """Buscar pedido por número"""
        result = await self.db.execute(
            select(PedidoVenda).where(PedidoVenda.numero_pedido == numero_pedido)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        cliente_id: Optional[int] = None,
        vendedor_id: Optional[int] = None,
        status: Optional[StatusPedidoVenda] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
    ) -> List[PedidoVenda]:
        """Listar pedidos com filtros"""
        query = select(PedidoVenda).options(selectinload(PedidoVenda.itens))

        filters = []
        if cliente_id:
            filters.append(PedidoVenda.cliente_id == cliente_id)
        if vendedor_id:
            filters.append(PedidoVenda.vendedor_id == vendedor_id)
        if status:
            filters.append(PedidoVenda.status == status)
        if data_inicio:
            filters.append(PedidoVenda.data_pedido >= data_inicio)
        if data_fim:
            filters.append(PedidoVenda.data_pedido <= data_fim)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(desc(PedidoVenda.data_pedido)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, pedido_id: int, data: dict) -> Optional[PedidoVenda]:
        """Atualizar pedido"""
        pedido = await self.get_by_id(pedido_id)
        if not pedido:
            return None

        for key, value in data.items():
            if value is not None and hasattr(pedido, key):
                setattr(pedido, key, value)

        await self.db.commit()
        await self.db.refresh(pedido)
        return pedido

    async def delete(self, pedido_id: int) -> bool:
        """Deletar pedido"""
        pedido = await self.get_by_id(pedido_id)
        if not pedido:
            return False

        await self.db.delete(pedido)
        await self.db.commit()
        return True

    async def gerar_numero_pedido(self) -> str:
        """Gerar próximo número de pedido"""
        result = await self.db.execute(
            select(func.max(PedidoVenda.numero_pedido))
        )
        ultimo_numero = result.scalar()

        if not ultimo_numero:
            return "PV000001"

        # Extrair número e incrementar
        numero = int(ultimo_numero[2:]) + 1
        return f"PV{numero:06d}"
