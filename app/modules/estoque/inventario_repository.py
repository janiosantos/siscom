"""
Repository para Inventário de Estoque
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.estoque.models import (
    FichaInventario,
    ItemInventario,
    StatusInventario,
    TipoInventario,
)


class InventarioRepository:
    """Repository para operações de Inventário"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== FICHAS DE INVENTÁRIO ====================

    async def create_ficha(
        self,
        tipo: TipoInventario,
        usuario_responsavel_id: Optional[int] = None,
        observacoes: Optional[str] = None,
    ) -> FichaInventario:
        """Cria nova ficha de inventário"""
        ficha = FichaInventario(
            tipo=tipo,
            usuario_responsavel_id=usuario_responsavel_id,
            observacoes=observacoes,
            status=StatusInventario.ABERTA,
        )
        self.session.add(ficha)
        await self.session.flush()
        await self.session.refresh(ficha)
        return ficha

    async def get_ficha_by_id(self, ficha_id: int) -> Optional[FichaInventario]:
        """Busca ficha de inventário por ID"""
        query = select(FichaInventario).where(FichaInventario.id == ficha_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_fichas(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[StatusInventario] = None,
        tipo: Optional[TipoInventario] = None,
    ) -> List[FichaInventario]:
        """Lista fichas de inventário com filtros"""
        query = select(FichaInventario)

        if status:
            query = query.where(FichaInventario.status == status)

        if tipo:
            query = query.where(FichaInventario.tipo == tipo)

        query = (
            query.order_by(FichaInventario.data_geracao.desc()).offset(skip).limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_fichas(
        self, status: Optional[StatusInventario] = None, tipo: Optional[TipoInventario] = None
    ) -> int:
        """Conta total de fichas"""
        query = select(func.count(FichaInventario.id))

        if status:
            query = query.where(FichaInventario.status == status)

        if tipo:
            query = query.where(FichaInventario.tipo == tipo)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update_ficha_status(
        self, ficha_id: int, status: StatusInventario
    ) -> Optional[FichaInventario]:
        """Atualiza status da ficha"""
        ficha = await self.get_ficha_by_id(ficha_id)
        if not ficha:
            return None

        ficha.status = status

        if status == StatusInventario.EM_ANDAMENTO and not ficha.data_inicio:
            ficha.data_inicio = datetime.utcnow()
        elif status == StatusInventario.CONCLUIDA and not ficha.data_conclusao:
            ficha.data_conclusao = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(ficha)
        return ficha

    async def update_ficha(
        self, ficha_id: int, **kwargs
    ) -> Optional[FichaInventario]:
        """Atualiza ficha de inventário"""
        ficha = await self.get_ficha_by_id(ficha_id)
        if not ficha:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(ficha, key):
                setattr(ficha, key, value)

        await self.session.flush()
        await self.session.refresh(ficha)
        return ficha

    # ==================== ITENS DE INVENTÁRIO ====================

    async def create_item(
        self,
        ficha_id: int,
        produto_id: int,
        quantidade_sistema: float,
        localizacao_id: Optional[int] = None,
    ) -> ItemInventario:
        """Cria item de inventário"""
        item = ItemInventario(
            ficha_id=ficha_id,
            produto_id=produto_id,
            quantidade_sistema=quantidade_sistema,
            localizacao_id=localizacao_id,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def get_item_by_id(self, item_id: int) -> Optional[ItemInventario]:
        """Busca item de inventário por ID"""
        query = select(ItemInventario).where(ItemInventario.id == item_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_itens_ficha(self, ficha_id: int) -> List[ItemInventario]:
        """Lista todos os itens de uma ficha"""
        query = (
            select(ItemInventario)
            .where(ItemInventario.ficha_id == ficha_id)
            .order_by(ItemInventario.produto_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def registrar_contagem(
        self,
        item_id: int,
        quantidade_contada: float,
        conferido_por_id: Optional[int] = None,
        justificativa: Optional[str] = None,
    ) -> Optional[ItemInventario]:
        """Registra contagem de um item"""
        item = await self.get_item_by_id(item_id)
        if not item:
            return None

        item.quantidade_contada = quantidade_contada
        item.divergencia = quantidade_contada - item.quantidade_sistema
        item.conferido_por_id = conferido_por_id
        item.justificativa = justificativa
        item.data_contagem = datetime.utcnow()

        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def get_itens_com_divergencia(
        self, ficha_id: int
    ) -> List[ItemInventario]:
        """Retorna itens com divergência (quantidade_contada != quantidade_sistema)"""
        query = (
            select(ItemInventario)
            .where(
                and_(
                    ItemInventario.ficha_id == ficha_id,
                    ItemInventario.quantidade_contada.isnot(None),
                    ItemInventario.divergencia != 0,
                )
            )
            .order_by(ItemInventario.divergencia.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_itens_sem_contagem(
        self, ficha_id: int
    ) -> List[ItemInventario]:
        """Retorna itens que ainda não foram contados"""
        query = (
            select(ItemInventario)
            .where(
                and_(
                    ItemInventario.ficha_id == ficha_id,
                    ItemInventario.quantidade_contada.is_(None),
                )
            )
            .order_by(ItemInventario.produto_id)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def contar_itens_por_status(
        self, ficha_id: int
    ) -> dict:
        """
        Conta itens por status de contagem

        Returns:
            dict com 'total', 'contados', 'pendentes'
        """
        query_total = select(func.count(ItemInventario.id)).where(
            ItemInventario.ficha_id == ficha_id
        )
        result_total = await self.session.execute(query_total)
        total = result_total.scalar() or 0

        query_contados = select(func.count(ItemInventario.id)).where(
            and_(
                ItemInventario.ficha_id == ficha_id,
                ItemInventario.quantidade_contada.isnot(None),
            )
        )
        result_contados = await self.session.execute(query_contados)
        contados = result_contados.scalar() or 0

        return {
            "total": total,
            "contados": contados,
            "pendentes": total - contados,
        }
