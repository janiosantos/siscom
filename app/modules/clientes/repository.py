"""
Repository para Clientes
"""
from typing import Optional, List
from sqlalchemy import select, func, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.clientes.models import Cliente
from app.modules.clientes.schemas import ClienteCreate, ClienteUpdate


class ClienteRepository:
    """Repository para operações de banco de dados de Clientes"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, cliente_data: ClienteCreate) -> Cliente:
        """Cria um novo cliente"""
        cliente = Cliente(**cliente_data.model_dump())
        self.session.add(cliente)
        await self.session.flush()
        await self.session.refresh(cliente)
        return cliente

    async def get_by_id(self, cliente_id: int) -> Optional[Cliente]:
        """Busca cliente por ID"""
        result = await self.session.execute(
            select(Cliente).where(Cliente.id == cliente_id)
        )
        return result.scalar_one_or_none()

    async def get_by_cpf_cnpj(self, cpf_cnpj: str) -> Optional[Cliente]:
        """Busca cliente por CPF/CNPJ"""
        result = await self.session.execute(
            select(Cliente).where(Cliente.cpf_cnpj == cpf_cnpj)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        apenas_ativos: bool = False,
    ) -> List[Cliente]:
        """
        Lista todos os clientes com paginação e filtros

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            apenas_ativos: Se deve listar apenas clientes ativos
        """
        query = select(Cliente)

        if apenas_ativos:
            query = query.where(Cliente.ativo == True)

        query = query.offset(skip).limit(limit).order_by(Cliente.nome)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, apenas_ativos: bool = False) -> int:
        """
        Conta total de clientes

        Args:
            apenas_ativos: Se deve contar apenas clientes ativos
        """
        query = select(func.count(Cliente.id))

        if apenas_ativos:
            query = query.where(Cliente.ativo == True)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(
        self, cliente_id: int, cliente_data: ClienteUpdate
    ) -> Optional[Cliente]:
        """Atualiza um cliente"""
        cliente = await self.get_by_id(cliente_id)
        if not cliente:
            return None

        update_data = cliente_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cliente, field, value)

        await self.session.flush()
        await self.session.refresh(cliente)
        return cliente

    async def delete(self, cliente_id: int) -> bool:
        """Deleta um cliente (soft delete - apenas inativa)"""
        cliente = await self.get_by_id(cliente_id)
        if not cliente:
            return False

        cliente.ativo = False
        await self.session.flush()
        return True

    async def search_by_nome(
        self, termo: str, skip: int = 0, limit: int = 100, apenas_ativos: bool = True
    ) -> List[Cliente]:
        """
        Busca clientes por nome ou CPF/CNPJ

        Args:
            termo: Termo de busca
            skip: Quantidade de registros para pular
            limit: Limite de registros
            apenas_ativos: Se deve buscar apenas clientes ativos
        """
        query = select(Cliente).where(
            or_(
                Cliente.nome.ilike(f"%{termo}%"),
                Cliente.cpf_cnpj.ilike(f"%{termo}%"),
            )
        )

        if apenas_ativos:
            query = query.where(Cliente.ativo == True)

        query = query.offset(skip).limit(limit).order_by(Cliente.nome)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_aniversariantes_mes(
        self, mes: int, skip: int = 0, limit: int = 100
    ) -> List[Cliente]:
        """
        Busca clientes que fazem aniversário em um mês específico

        Args:
            mes: Mês (1-12)
            skip: Quantidade de registros para pular
            limit: Limite de registros
        """
        query = (
            select(Cliente)
            .where(Cliente.data_nascimento.isnot(None))
            .where(extract("month", Cliente.data_nascimento) == mes)
            .where(Cliente.ativo == True)
            .offset(skip)
            .limit(limit)
            .order_by(extract("day", Cliente.data_nascimento))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
