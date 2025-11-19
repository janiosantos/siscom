"""
Service Layer para Categorias
"""
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categorias.repository import CategoriaRepository
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaResponse,
    CategoriaList,
)
from app.modules.categorias.models import Categoria
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    DuplicateException,
)
import math


class CategoriaService:
    """Service para regras de negócio de Categorias"""

    def __init__(self, session: AsyncSession):
        self.repository = CategoriaRepository(session)

    async def create_categoria(
        self, categoria_data: CategoriaCreate
    ) -> CategoriaResponse:
        """
        Cria uma nova categoria

        Regras:
        - Nome não pode estar duplicado
        - Nome é obrigatório
        """
        # Verifica duplicação
        existing = await self.repository.get_by_nome(categoria_data.nome)
        if existing:
            raise DuplicateException(
                f"Categoria com nome '{categoria_data.nome}' já existe"
            )

        # Cria categoria
        categoria = await self.repository.create(categoria_data)
        return CategoriaResponse.model_validate(categoria)

    async def get_categoria(self, categoria_id: int) -> CategoriaResponse:
        """Busca categoria por ID"""
        categoria = await self.repository.get_by_id(categoria_id)
        if not categoria:
            raise NotFoundException(f"Categoria {categoria_id} não encontrada")

        return CategoriaResponse.model_validate(categoria)

    async def list_categorias(
        self, page: int = 1, page_size: int = 50, apenas_ativas: bool = False
    ) -> CategoriaList:
        """
        Lista categorias com paginação

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            apenas_ativas: Se deve listar apenas categorias ativas
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca categorias e total
        categorias = await self.repository.get_all(skip, page_size, apenas_ativas)
        total = await self.repository.count(apenas_ativas)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return CategoriaList(
            items=[CategoriaResponse.model_validate(c) for c in categorias],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def update_categoria(
        self, categoria_id: int, categoria_data: CategoriaUpdate
    ) -> CategoriaResponse:
        """
        Atualiza uma categoria

        Regras:
        - Se mudar nome, não pode duplicar com existente
        """
        # Verifica se categoria existe
        categoria_atual = await self.repository.get_by_id(categoria_id)
        if not categoria_atual:
            raise NotFoundException(f"Categoria {categoria_id} não encontrada")

        # Verifica duplicação de nome se foi alterado
        if categoria_data.nome and categoria_data.nome != categoria_atual.nome:
            existing = await self.repository.get_by_nome(categoria_data.nome)
            if existing:
                raise DuplicateException(
                    f"Categoria com nome '{categoria_data.nome}' já existe"
                )

        # Atualiza
        categoria = await self.repository.update(categoria_id, categoria_data)
        return CategoriaResponse.model_validate(categoria)

    async def delete_categoria(self, categoria_id: int) -> bool:
        """
        Inativa uma categoria (soft delete)

        Regras:
        - Apenas inativa, não deleta do banco
        - Produtos vinculados permanecem vinculados
        """
        categoria = await self.repository.get_by_id(categoria_id)
        if not categoria:
            raise NotFoundException(f"Categoria {categoria_id} não encontrada")

        return await self.repository.delete(categoria_id)

    async def reativar_categoria(self, categoria_id: int) -> CategoriaResponse:
        """Reativa uma categoria inativa"""
        categoria = await self.repository.get_by_id(categoria_id)
        if not categoria:
            raise NotFoundException(f"Categoria {categoria_id} não encontrada")

        if categoria.ativa:
            raise ValidationException("Categoria já está ativa")

        update_data = CategoriaUpdate(ativa=True)
        categoria_atualizada = await self.repository.update(categoria_id, update_data)
        return CategoriaResponse.model_validate(categoria_atualizada)
