"""
Router para endpoints de Categorias
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.categorias.service import CategoriaService
from app.modules.categorias.schemas import (
    CategoriaCreate,
    CategoriaUpdate,
    CategoriaResponse,
    CategoriaList,
)

router = APIRouter()


@router.post(
    "/",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova categoria",
    description="Cria uma nova categoria de produtos",
)
async def create_categoria(
    categoria_data: CategoriaCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova categoria de produtos.

    **Exemplo de requisição:**
    ```json
    {
        "nome": "Cimentos",
        "descricao": "Cimentos e argamassas",
        "ativa": true
    }
    ```
    """
    service = CategoriaService(db)
    return await service.create_categoria(categoria_data)


@router.get(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Buscar categoria por ID",
    description="Retorna os dados de uma categoria específica",
)
async def get_categoria(categoria_id: int, db: AsyncSession = Depends(get_db)):
    """Busca uma categoria por ID"""
    service = CategoriaService(db)
    return await service.get_categoria(categoria_id)


@router.get(
    "/",
    response_model=CategoriaList,
    summary="Listar categorias",
    description="Lista todas as categorias com paginação",
)
async def list_categorias(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    apenas_ativas: bool = Query(False, description="Listar apenas categorias ativas"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista categorias com paginação.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **apenas_ativas**: Se True, lista apenas categorias ativas
    """
    service = CategoriaService(db)
    return await service.list_categorias(page, page_size, apenas_ativas)


@router.put(
    "/{categoria_id}",
    response_model=CategoriaResponse,
    summary="Atualizar categoria",
    description="Atualiza os dados de uma categoria",
)
async def update_categoria(
    categoria_id: int,
    categoria_data: CategoriaUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza uma categoria existente.

    **Exemplo de requisição:**
    ```json
    {
        "nome": "Cimentos e Argamassas",
        "descricao": "Categoria atualizada"
    }
    ```
    """
    service = CategoriaService(db)
    return await service.update_categoria(categoria_id, categoria_data)


@router.delete(
    "/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Inativar categoria",
    description="Inativa uma categoria (soft delete)",
)
async def delete_categoria(categoria_id: int, db: AsyncSession = Depends(get_db)):
    """
    Inativa uma categoria (soft delete).
    A categoria não é removida do banco, apenas marcada como inativa.
    """
    service = CategoriaService(db)
    await service.delete_categoria(categoria_id)
    return None


@router.post(
    "/{categoria_id}/reativar",
    response_model=CategoriaResponse,
    summary="Reativar categoria",
    description="Reativa uma categoria inativa",
)
async def reativar_categoria(categoria_id: int, db: AsyncSession = Depends(get_db)):
    """Reativa uma categoria que foi inativada"""
    service = CategoriaService(db)
    return await service.reativar_categoria(categoria_id)
