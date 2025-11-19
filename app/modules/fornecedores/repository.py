"""
Repository para Fornecedores
"""
from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fornecedores.models import Fornecedor
from app.modules.fornecedores.schemas import FornecedorCreate, FornecedorUpdate


class FornecedorRepository:
    """Repository para operações de banco de dados de Fornecedores"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, fornecedor_data: FornecedorCreate) -> Fornecedor:
        """Cria um novo fornecedor"""
        fornecedor = Fornecedor(**fornecedor_data.model_dump())
        self.session.add(fornecedor)
        await self.session.flush()
        await self.session.refresh(fornecedor)
        return fornecedor

    async def get_by_id(self, fornecedor_id: int) -> Optional[Fornecedor]:
        """Busca fornecedor por ID"""
        result = await self.session.execute(
            select(Fornecedor).where(Fornecedor.id == fornecedor_id)
        )
        return result.scalar_one_or_none()

    async def get_by_cnpj(self, cnpj: str) -> Optional[Fornecedor]:
        """Busca fornecedor por CNPJ"""
        result = await self.session.execute(
            select(Fornecedor).where(Fornecedor.cnpj == cnpj)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        apenas_ativos: bool = False,
    ) -> List[Fornecedor]:
        """
        Lista todos os fornecedores com paginação e filtros

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            apenas_ativos: Se deve listar apenas fornecedores ativos
        """
        query = select(Fornecedor)

        if apenas_ativos:
            query = query.where(Fornecedor.ativo == True)

        query = query.offset(skip).limit(limit).order_by(Fornecedor.razao_social)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, apenas_ativos: bool = False) -> int:
        """
        Conta total de fornecedores

        Args:
            apenas_ativos: Se deve contar apenas fornecedores ativos
        """
        query = select(func.count(Fornecedor.id))

        if apenas_ativos:
            query = query.where(Fornecedor.ativo == True)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(
        self, fornecedor_id: int, fornecedor_data: FornecedorUpdate
    ) -> Optional[Fornecedor]:
        """Atualiza um fornecedor"""
        fornecedor = await self.get_by_id(fornecedor_id)
        if not fornecedor:
            return None

        update_data = fornecedor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(fornecedor, field, value)

        await self.session.flush()
        await self.session.refresh(fornecedor)
        return fornecedor

    async def delete(self, fornecedor_id: int) -> bool:
        """Deleta um fornecedor (soft delete - apenas inativa)"""
        fornecedor = await self.get_by_id(fornecedor_id)
        if not fornecedor:
            return False

        fornecedor.ativo = False
        await self.session.flush()
        return True

    async def search_by_nome(
        self, termo: str, skip: int = 0, limit: int = 100, apenas_ativos: bool = True
    ) -> List[Fornecedor]:
        """
        Busca fornecedores por razão social, nome fantasia ou CNPJ

        Args:
            termo: Termo de busca
            skip: Quantidade de registros para pular
            limit: Limite de registros
            apenas_ativos: Se deve buscar apenas fornecedores ativos
        """
        query = select(Fornecedor).where(
            or_(
                Fornecedor.razao_social.ilike(f"%{termo}%"),
                Fornecedor.nome_fantasia.ilike(f"%{termo}%"),
                Fornecedor.cnpj.ilike(f"%{termo}%"),
            )
        )

        if apenas_ativos:
            query = query.where(Fornecedor.ativo == True)

        query = query.offset(skip).limit(limit).order_by(Fornecedor.razao_social)
        result = await self.session.execute(query)
        return list(result.scalars().all())
