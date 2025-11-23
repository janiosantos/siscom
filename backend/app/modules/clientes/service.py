"""
Service Layer para Clientes
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.clientes.repository import ClienteRepository
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ClienteList,
)
from app.modules.clientes.models import Cliente
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    DuplicateException,
)


class ClienteService:
    """Service para regras de negócio de Clientes"""

    def __init__(self, session: AsyncSession):
        self.repository = ClienteRepository(session)

    async def criar_cliente(self, cliente_data: ClienteCreate) -> ClienteResponse:
        """
        Cria um novo cliente

        Regras:
        - CPF/CNPJ não pode estar duplicado
        - CPF/CNPJ deve ser válido (validação feita no schema)
        """
        # Verifica duplicação de CPF/CNPJ
        existing = await self.repository.get_by_cpf_cnpj(cliente_data.cpf_cnpj)
        if existing:
            raise DuplicateException(
                f"Cliente com CPF/CNPJ '{cliente_data.cpf_cnpj}' já existe"
            )

        # Cria cliente
        cliente = await self.repository.create(cliente_data)

        return ClienteResponse.model_validate(cliente)

    async def buscar_cliente(self, cliente_id: int) -> ClienteResponse:
        """Busca cliente por ID"""
        cliente = await self.repository.get_by_id(cliente_id)
        if not cliente:
            raise NotFoundException(f"Cliente {cliente_id} não encontrado")

        return ClienteResponse.model_validate(cliente)

    async def listar_clientes(
        self,
        page: int = 1,
        page_size: int = 50,
        apenas_ativos: bool = False,
    ) -> ClienteList:
        """
        Lista clientes com paginação

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            apenas_ativos: Se deve listar apenas clientes ativos
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca clientes e total
        clientes = await self.repository.get_all(skip, page_size, apenas_ativos)
        total = await self.repository.count(apenas_ativos)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return ClienteList(
            items=[ClienteResponse.model_validate(c) for c in clientes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def atualizar_cliente(
        self, cliente_id: int, cliente_data: ClienteUpdate
    ) -> ClienteResponse:
        """
        Atualiza um cliente

        Regras:
        - Se mudar CPF/CNPJ, não pode duplicar com existente
        - CPF/CNPJ deve ser válido (validação feita no schema)
        """
        # Verifica se cliente existe
        cliente_atual = await self.repository.get_by_id(cliente_id)
        if not cliente_atual:
            raise NotFoundException(f"Cliente {cliente_id} não encontrado")

        # Verifica duplicação de CPF/CNPJ se foi alterado
        if (
            cliente_data.cpf_cnpj
            and cliente_data.cpf_cnpj != cliente_atual.cpf_cnpj
        ):
            existing = await self.repository.get_by_cpf_cnpj(cliente_data.cpf_cnpj)
            if existing:
                raise DuplicateException(
                    f"Cliente com CPF/CNPJ '{cliente_data.cpf_cnpj}' já existe"
                )

        # Atualiza
        cliente = await self.repository.update(cliente_id, cliente_data)

        return ClienteResponse.model_validate(cliente)

    async def delete_cliente(self, cliente_id: int) -> bool:
        """
        Inativa um cliente (soft delete)

        Regras:
        - Apenas inativa, não deleta do banco
        """
        cliente = await self.repository.get_by_id(cliente_id)
        if not cliente:
            raise NotFoundException(f"Cliente {cliente_id} não encontrado")

        return await self.repository.delete(cliente_id)

    async def search_clientes(
        self, termo: str, page: int = 1, page_size: int = 50, apenas_ativos: bool = True
    ) -> ClienteList:
        """
        Busca clientes por nome ou CPF/CNPJ

        Args:
            termo: Termo de busca
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            apenas_ativos: Se deve buscar apenas clientes ativos
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca clientes
        clientes = await self.repository.search_by_nome(
            termo, skip, page_size, apenas_ativos
        )

        # Conta total (fazendo a mesma busca sem paginação)
        todos_clientes = await self.repository.search_by_nome(
            termo, 0, 10000, apenas_ativos
        )
        total = len(todos_clientes)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return ClienteList(
            items=[ClienteResponse.model_validate(c) for c in clientes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_aniversariantes_mes(
        self, mes: int, page: int = 1, page_size: int = 50
    ) -> ClienteList:
        """
        Retorna clientes que fazem aniversário em um mês específico

        Args:
            mes: Mês (1-12)
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
        """
        # Valida mês
        if mes < 1 or mes > 12:
            raise ValidationException("Mês deve estar entre 1 e 12")

        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca aniversariantes
        clientes = await self.repository.get_aniversariantes_mes(mes, skip, page_size)

        # Conta total
        todos_clientes = await self.repository.get_aniversariantes_mes(mes, 0, 10000)
        total = len(todos_clientes)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return ClienteList(
            items=[ClienteResponse.model_validate(c) for c in clientes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
