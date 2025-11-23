"""
Router para endpoints de Produtos
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.produtos.service import ProdutoService
from app.modules.produtos.schemas import (
    ProdutoCreate,
    ProdutoUpdate,
    ProdutoResponse,
    ProdutoList,
)

router = APIRouter()


@router.post(
    "/",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo produto",
    description="Cria um novo produto no sistema",
)
async def create_produto(
    produto_data: ProdutoCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo produto.

    **Validações:**
    - Código de barras único
    - Categoria deve existir e estar ativa
    - Preço de venda >= preço de custo

    **Exemplo de requisição:**
    ```json
    {
        "codigo_barras": "7891234567890",
        "descricao": "Cimento Portland CP-II 50kg",
        "categoria_id": 1,
        "preco_custo": 25.50,
        "preco_venda": 32.90,
        "estoque_atual": 100.0,
        "estoque_minimo": 20.0,
        "unidade": "SC",
        "ncm": "25231000",
        "ativo": true
    }
    ```
    """
    service = ProdutoService(db)
    return await service.create_produto(produto_data)


@router.get(
    "/{produto_id}",
    response_model=ProdutoResponse,
    summary="Buscar produto por ID",
    description="Retorna os dados de um produto específico",
)
async def get_produto(produto_id: int, db: AsyncSession = Depends(get_db)):
    """Busca um produto por ID"""
    service = ProdutoService(db)
    return await service.get_produto(produto_id)


@router.get(
    "/",
    response_model=ProdutoList,
    summary="Listar produtos",
    description="Lista todos os produtos com paginação e filtros",
)
async def list_produtos(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    apenas_ativos: bool = Query(False, description="Listar apenas produtos ativos"),
    categoria_id: int = Query(None, description="Filtrar por categoria"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista produtos com paginação e filtros.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **apenas_ativos**: Se True, lista apenas produtos ativos
    - **categoria_id**: Se fornecido, filtra por categoria
    """
    service = ProdutoService(db)
    return await service.list_produtos(page, page_size, apenas_ativos, categoria_id)


@router.put(
    "/{produto_id}",
    response_model=ProdutoResponse,
    summary="Atualizar produto",
    description="Atualiza os dados de um produto",
)
async def update_produto(
    produto_id: int,
    produto_data: ProdutoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza um produto existente.

    **Validações:**
    - Se alterar código de barras, deve ser único
    - Se alterar categoria, deve existir e estar ativa
    - Se alterar preços, preço de venda >= preço de custo

    **Exemplo de requisição:**
    ```json
    {
        "descricao": "Cimento Portland CP-II 50kg - Alta Resistência",
        "preco_venda": 35.90
    }
    ```
    """
    service = ProdutoService(db)
    return await service.update_produto(produto_id, produto_data)


@router.delete(
    "/{produto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Inativar produto",
    description="Inativa um produto (soft delete)",
)
async def delete_produto(produto_id: int, db: AsyncSession = Depends(get_db)):
    """
    Inativa um produto (soft delete).
    O produto não é removido do banco, apenas marcado como inativo.
    """
    service = ProdutoService(db)
    await service.delete_produto(produto_id)
    return None


@router.get(
    "/buscar/search",
    response_model=ProdutoList,
    summary="Buscar produtos",
    description="Busca produtos por descrição ou código de barras",
)
async def search_produtos(
    termo: str = Query(..., min_length=1, description="Termo de busca"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    apenas_ativos: bool = Query(True, description="Buscar apenas produtos ativos"),
    db: AsyncSession = Depends(get_db),
):
    """
    Busca produtos por descrição ou código de barras.

    **Parâmetros:**
    - **termo**: Termo de busca (busca na descrição e código de barras)
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **apenas_ativos**: Se True, busca apenas produtos ativos (padrão: True)

    **Exemplo:**
    - `/buscar/search?termo=cimento` - busca produtos com "cimento" na descrição
    - `/buscar/search?termo=789123` - busca produtos com "789123" no código de barras
    """
    service = ProdutoService(db)
    return await service.search_produtos(termo, page, page_size, apenas_ativos)


@router.get(
    "/categoria/{categoria_id}/produtos",
    response_model=ProdutoList,
    summary="Listar produtos por categoria",
    description="Lista todos os produtos de uma categoria específica",
)
async def get_produtos_by_categoria(
    categoria_id: int,
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista produtos de uma categoria específica.

    **Parâmetros:**
    - **categoria_id**: ID da categoria
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    """
    service = ProdutoService(db)
    return await service.get_produtos_by_categoria(categoria_id, page, page_size)


@router.get(
    "/estoque/minimo",
    response_model=ProdutoList,
    summary="Produtos abaixo do estoque mínimo",
    description="Lista produtos com estoque abaixo do mínimo configurado",
)
async def get_produtos_abaixo_estoque_minimo(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista produtos com estoque atual abaixo do estoque mínimo.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)

    **Útil para:**
    - Alertas de reposição de estoque
    - Relatórios de produtos em falta
    - Planejamento de compras
    """
    service = ProdutoService(db)
    return await service.get_produtos_abaixo_estoque_minimo(page, page_size)
