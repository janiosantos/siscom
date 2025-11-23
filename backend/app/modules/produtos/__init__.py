"""
Módulo de Produtos
"""
from app.modules.produtos.models import Produto
from app.modules.produtos.schemas import (
    ProdutoBase,
    ProdutoCreate,
    ProdutoUpdate,
    ProdutoResponse,
    ProdutoList,
)
from app.modules.produtos.repository import ProdutoRepository
from app.modules.produtos.service import ProdutoService
from app.modules.produtos.router import router

__all__ = [
    "Produto",
    "ProdutoBase",
    "ProdutoCreate",
    "ProdutoUpdate",
    "ProdutoResponse",
    "ProdutoList",
    "ProdutoRepository",
    "ProdutoService",
    "router",
]
