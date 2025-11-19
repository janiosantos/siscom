"""
Service Layer para Produtos
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.produtos.repository import ProdutoRepository
from app.modules.produtos.schemas import (
    ProdutoCreate,
    ProdutoUpdate,
    ProdutoResponse,
    ProdutoList,
)
from app.modules.produtos.models import Produto
from app.modules.categorias.repository import CategoriaRepository
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    DuplicateException,
    BusinessRuleException,
)


class ProdutoService:
    """Service para regras de negócio de Produtos"""

    def __init__(self, session: AsyncSession):
        self.repository = ProdutoRepository(session)
        self.categoria_repository = CategoriaRepository(session)

    def calcular_margem_lucro(self, preco_custo: float, preco_venda: float) -> float:
        """
        Calcula a margem de lucro percentual

        Args:
            preco_custo: Preço de custo
            preco_venda: Preço de venda

        Returns:
            Margem de lucro em percentual
        """
        if preco_custo == 0:
            return 0.0

        return ((preco_venda - preco_custo) / preco_custo) * 100

    async def validar_preco_venda(
        self, preco_custo: float, preco_venda: float
    ) -> None:
        """
        Valida se o preço de venda é maior ou igual ao preço de custo

        Args:
            preco_custo: Preço de custo
            preco_venda: Preço de venda

        Raises:
            ValidationException: Se preço de venda for menor que preço de custo
        """
        if preco_venda < preco_custo:
            raise ValidationException(
                f"Preço de venda (R$ {preco_venda:.2f}) não pode ser menor que o preço de custo (R$ {preco_custo:.2f})"
            )

    async def validar_categoria_existe(self, categoria_id: int) -> None:
        """
        Valida se a categoria existe e está ativa

        Args:
            categoria_id: ID da categoria

        Raises:
            NotFoundException: Se categoria não existe
            ValidationException: Se categoria está inativa
        """
        categoria = await self.categoria_repository.get_by_id(categoria_id)
        if not categoria:
            raise NotFoundException(f"Categoria {categoria_id} não encontrada")

        if not categoria.ativa:
            raise ValidationException(
                f"Categoria '{categoria.nome}' está inativa e não pode ser usada"
            )

    async def verificar_alerta_estoque_minimo(self, produto: Produto) -> bool:
        """
        Verifica se o produto está abaixo do estoque mínimo

        Args:
            produto: Produto a verificar

        Returns:
            True se está abaixo do estoque mínimo
        """
        return produto.estoque_atual < produto.estoque_minimo

    async def create_produto(self, produto_data: ProdutoCreate) -> ProdutoResponse:
        """
        Cria um novo produto

        Regras:
        - Código de barras não pode estar duplicado
        - Categoria deve existir e estar ativa
        - Preço de venda deve ser >= preço de custo
        """
        # Verifica duplicação de código de barras
        existing = await self.repository.get_by_codigo_barras(
            produto_data.codigo_barras
        )
        if existing:
            raise DuplicateException(
                f"Produto com código de barras '{produto_data.codigo_barras}' já existe"
            )

        # Valida categoria
        await self.validar_categoria_existe(produto_data.categoria_id)

        # Valida preço de venda
        await self.validar_preco_venda(produto_data.preco_custo, produto_data.preco_venda)

        # Cria produto
        produto = await self.repository.create(produto_data)

        # Verifica alerta de estoque mínimo
        if await self.verificar_alerta_estoque_minimo(produto):
            # Aqui poderia disparar um evento/notificação
            pass

        return ProdutoResponse.model_validate(produto)

    async def get_produto(self, produto_id: int) -> ProdutoResponse:
        """Busca produto por ID"""
        produto = await self.repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        return ProdutoResponse.model_validate(produto)

    async def list_produtos(
        self,
        page: int = 1,
        page_size: int = 50,
        apenas_ativos: bool = False,
        categoria_id: Optional[int] = None,
    ) -> ProdutoList:
        """
        Lista produtos com paginação

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            apenas_ativos: Se deve listar apenas produtos ativos
            categoria_id: Filtrar por categoria
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca produtos e total
        produtos = await self.repository.get_all(
            skip, page_size, apenas_ativos, categoria_id
        )
        total = await self.repository.count(apenas_ativos, categoria_id)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return ProdutoList(
            items=[ProdutoResponse.model_validate(p) for p in produtos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def update_produto(
        self, produto_id: int, produto_data: ProdutoUpdate
    ) -> ProdutoResponse:
        """
        Atualiza um produto

        Regras:
        - Se mudar código de barras, não pode duplicar com existente
        - Se mudar categoria, categoria deve existir e estar ativa
        - Se alterar preços, preço de venda deve ser >= preço de custo
        """
        # Verifica se produto existe
        produto_atual = await self.repository.get_by_id(produto_id)
        if not produto_atual:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        # Verifica duplicação de código de barras se foi alterado
        if (
            produto_data.codigo_barras
            and produto_data.codigo_barras != produto_atual.codigo_barras
        ):
            existing = await self.repository.get_by_codigo_barras(
                produto_data.codigo_barras
            )
            if existing:
                raise DuplicateException(
                    f"Produto com código de barras '{produto_data.codigo_barras}' já existe"
                )

        # Valida categoria se foi alterada
        if produto_data.categoria_id:
            await self.validar_categoria_existe(produto_data.categoria_id)

        # Valida preços se foram alterados
        preco_custo = (
            produto_data.preco_custo
            if produto_data.preco_custo is not None
            else produto_atual.preco_custo
        )
        preco_venda = (
            produto_data.preco_venda
            if produto_data.preco_venda is not None
            else produto_atual.preco_venda
        )

        await self.validar_preco_venda(preco_custo, preco_venda)

        # Atualiza
        produto = await self.repository.update(produto_id, produto_data)

        # Verifica alerta de estoque mínimo
        if await self.verificar_alerta_estoque_minimo(produto):
            # Aqui poderia disparar um evento/notificação
            pass

        return ProdutoResponse.model_validate(produto)

    async def delete_produto(self, produto_id: int) -> bool:
        """
        Inativa um produto (soft delete)

        Regras:
        - Apenas inativa, não deleta do banco
        """
        produto = await self.repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        return await self.repository.delete(produto_id)

    async def search_produtos(
        self, termo: str, page: int = 1, page_size: int = 50, apenas_ativos: bool = True
    ) -> ProdutoList:
        """
        Busca produtos por descrição ou código de barras

        Args:
            termo: Termo de busca
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            apenas_ativos: Se deve buscar apenas produtos ativos
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca produtos
        produtos = await self.repository.search_by_descricao(
            termo, skip, page_size, apenas_ativos
        )

        # Conta total (fazendo a mesma busca sem paginação)
        todos_produtos = await self.repository.search_by_descricao(
            termo, 0, 10000, apenas_ativos
        )
        total = len(todos_produtos)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return ProdutoList(
            items=[ProdutoResponse.model_validate(p) for p in produtos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_produtos_by_categoria(
        self, categoria_id: int, page: int = 1, page_size: int = 50
    ) -> ProdutoList:
        """
        Lista produtos de uma categoria específica

        Args:
            categoria_id: ID da categoria
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
        """
        # Valida se categoria existe
        await self.validar_categoria_existe(categoria_id)

        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca produtos
        produtos = await self.repository.get_by_categoria(
            categoria_id, skip, page_size
        )
        total = await self.repository.count(apenas_ativos=True, categoria_id=categoria_id)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return ProdutoList(
            items=[ProdutoResponse.model_validate(p) for p in produtos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_produtos_abaixo_estoque_minimo(
        self, page: int = 1, page_size: int = 50
    ) -> ProdutoList:
        """
        Lista produtos com estoque abaixo do mínimo

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca produtos
        produtos = await self.repository.get_abaixo_estoque_minimo(skip, page_size)

        # Conta total
        todos_produtos = await self.repository.get_abaixo_estoque_minimo(0, 10000)
        total = len(todos_produtos)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return ProdutoList(
            items=[ProdutoResponse.model_validate(p) for p in produtos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
