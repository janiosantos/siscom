"""
Repository para Categorias
"""
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categorias.models import Categoria
from app.modules.categorias.schemas import CategoriaCreate, CategoriaUpdate


class CategoriaRepository:
    """Repository para operações de banco de dados de Categorias"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, categoria_data: CategoriaCreate) -> Categoria:
        """Cria uma nova categoria"""
        categoria = Categoria(**categoria_data.model_dump())
        self.session.add(categoria)
        await self.session.flush()
        await self.session.refresh(categoria)
        return categoria

    async def get_by_id(self, categoria_id: int) -> Optional[Categoria]:
        """Busca categoria por ID"""
        result = await self.session.execute(
            select(Categoria).where(Categoria.id == categoria_id)
        )
        return result.scalar_one_or_none()

    async def get_by_nome(self, nome: str) -> Optional[Categoria]:
        """Busca categoria por nome"""
        result = await self.session.execute(
            select(Categoria).where(Categoria.nome == nome)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, apenas_ativas: bool = False
    ) -> List[Categoria]:
        """Lista todas as categorias com paginação"""
        query = select(Categoria)

        if apenas_ativas:
            query = query.where(Categoria.ativa == True)

        query = query.offset(skip).limit(limit).order_by(Categoria.nome)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, apenas_ativas: bool = False) -> int:
        """Conta total de categorias"""
        query = select(func.count(Categoria.id))

        if apenas_ativas:
            query = query.where(Categoria.ativa == True)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(
        self, categoria_id: int, categoria_data: CategoriaUpdate
    ) -> Optional[Categoria]:
        """Atualiza uma categoria"""
        categoria = await self.get_by_id(categoria_id)
        if not categoria:
            return None

        update_data = categoria_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(categoria, field, value)

        await self.session.flush()
        await self.session.refresh(categoria)
        return categoria

    async def delete(self, categoria_id: int) -> bool:
        """Deleta uma categoria (soft delete - apenas inativa)"""
        categoria = await self.get_by_id(categoria_id)
        if not categoria:
            return False

        categoria.ativa = False
        await self.session.commit()
        return True

    async def delete_permanent(self, categoria_id: int) -> bool:
        """Deleta permanentemente uma categoria"""
        categoria = await self.get_by_id(categoria_id)
        if not categoria:
            return False

        await self.session.delete(categoria)
        await self.session.flush()
        return True
