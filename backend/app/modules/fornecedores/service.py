"""
Service Layer para Fornecedores
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.fornecedores.repository import FornecedorRepository
from app.modules.fornecedores.schemas import (
    FornecedorCreate,
    FornecedorUpdate,
    FornecedorResponse,
    FornecedorList,
)
from app.modules.fornecedores.models import Fornecedor
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    DuplicateException,
)


class FornecedorService:
    """Service para regras de negócio de Fornecedores"""

    def __init__(self, session: AsyncSession):
        self.repository = FornecedorRepository(session)

    async def criar_fornecedor(
        self, fornecedor_data: FornecedorCreate
    ) -> FornecedorResponse:
        """
        Cria um novo fornecedor

        Regras:
        - CNPJ não pode estar duplicado
        - CNPJ deve ser válido (validação feita no schema)
        """
        # Verifica duplicação de CNPJ
        existing = await self.repository.get_by_cnpj(fornecedor_data.cnpj)
        if existing:
            raise DuplicateException(
                f"Fornecedor com CNPJ '{fornecedor_data.cnpj}' já existe"
            )

        # Cria fornecedor
        fornecedor = await self.repository.create(fornecedor_data)

        return FornecedorResponse.model_validate(fornecedor)

    async def buscar_fornecedor(self, fornecedor_id: int) -> FornecedorResponse:
        """Busca fornecedor por ID"""
        fornecedor = await self.repository.get_by_id(fornecedor_id)
        if not fornecedor:
            raise NotFoundException(f"Fornecedor {fornecedor_id} não encontrado")

        return FornecedorResponse.model_validate(fornecedor)

    async def listar_fornecedores(
        self,
        page: int = 1,
        page_size: int = 50,
        apenas_ativos: bool = False,
    ) -> FornecedorList:
        """
        Lista fornecedores com paginação

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            apenas_ativos: Se deve listar apenas fornecedores ativos
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca fornecedores e total
        fornecedores = await self.repository.get_all(skip, page_size, apenas_ativos)
        total = await self.repository.count(apenas_ativos)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return FornecedorList(
            items=[FornecedorResponse.model_validate(f) for f in fornecedores],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def atualizar_fornecedor(
        self, fornecedor_id: int, fornecedor_data: FornecedorUpdate
    ) -> FornecedorResponse:
        """
        Atualiza um fornecedor

        Regras:
        - Se mudar CNPJ, não pode duplicar com existente
        - CNPJ deve ser válido (validação feita no schema)
        """
        # Verifica se fornecedor existe
        fornecedor_atual = await self.repository.get_by_id(fornecedor_id)
        if not fornecedor_atual:
            raise NotFoundException(f"Fornecedor {fornecedor_id} não encontrado")

        # Verifica duplicação de CNPJ se foi alterado
        if fornecedor_data.cnpj and fornecedor_data.cnpj != fornecedor_atual.cnpj:
            existing = await self.repository.get_by_cnpj(fornecedor_data.cnpj)
            if existing:
                raise DuplicateException(
                    f"Fornecedor com CNPJ '{fornecedor_data.cnpj}' já existe"
                )

        # Atualiza
        fornecedor = await self.repository.update(fornecedor_id, fornecedor_data)

        return FornecedorResponse.model_validate(fornecedor)

    async def delete_fornecedor(self, fornecedor_id: int) -> bool:
        """
        Inativa um fornecedor (soft delete)

        Regras:
        - Apenas inativa, não deleta do banco
        """
        fornecedor = await self.repository.get_by_id(fornecedor_id)
        if not fornecedor:
            raise NotFoundException(f"Fornecedor {fornecedor_id} não encontrado")

        return await self.repository.delete(fornecedor_id)

    async def search_fornecedores(
        self, termo: str, page: int = 1, page_size: int = 50, apenas_ativos: bool = True
    ) -> FornecedorList:
        """
        Busca fornecedores por razão social, nome fantasia ou CNPJ

        Args:
            termo: Termo de busca
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            apenas_ativos: Se deve buscar apenas fornecedores ativos
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca fornecedores
        fornecedores = await self.repository.search_by_nome(
            termo, skip, page_size, apenas_ativos
        )

        # Conta total (fazendo a mesma busca sem paginação)
        todos_fornecedores = await self.repository.search_by_nome(
            termo, 0, 10000, apenas_ativos
        )
        total = len(todos_fornecedores)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return FornecedorList(
            items=[FornecedorResponse.model_validate(f) for f in fornecedores],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
