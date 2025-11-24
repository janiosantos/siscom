"""
Repository para Produtos
"""
from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.produtos.models import Produto
from app.modules.produtos.schemas import ProdutoCreate, ProdutoUpdate


class ProdutoRepository:
    """Repository para operações de banco de dados de Produtos"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, produto_data: ProdutoCreate) -> Produto:
        """Cria um novo produto"""
        produto = Produto(**produto_data.model_dump())
        self.session.add(produto)
        await self.session.flush()
        await self.session.refresh(produto)
        return produto

    async def get_by_id(self, produto_id: int) -> Optional[Produto]:
        """Busca produto por ID"""
        result = await self.session.execute(
            select(Produto).where(Produto.id == produto_id)
        )
        return result.scalar_one_or_none()

    async def get_by_codigo_barras(self, codigo_barras: str) -> Optional[Produto]:
        """Busca produto por código de barras"""
        result = await self.session.execute(
            select(Produto).where(Produto.codigo_barras == codigo_barras)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        apenas_ativos: bool = False,
        categoria_id: Optional[int] = None,
    ) -> List[Produto]:
        """
        Lista todos os produtos com paginação e filtros

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            apenas_ativos: Se deve listar apenas produtos ativos
            categoria_id: Filtrar por categoria
        """
        query = select(Produto)

        if apenas_ativos:
            query = query.where(Produto.ativo == True)

        if categoria_id:
            query = query.where(Produto.categoria_id == categoria_id)

        query = query.offset(skip).limit(limit).order_by(Produto.descricao)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self, apenas_ativos: bool = False, categoria_id: Optional[int] = None
    ) -> int:
        """
        Conta total de produtos

        Args:
            apenas_ativos: Se deve contar apenas produtos ativos
            categoria_id: Filtrar por categoria
        """
        query = select(func.count(Produto.id))

        if apenas_ativos:
            query = query.where(Produto.ativo == True)

        if categoria_id:
            query = query.where(Produto.categoria_id == categoria_id)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(
        self, produto_id: int, produto_data: ProdutoUpdate
    ) -> Optional[Produto]:
        """Atualiza um produto"""
        produto = await self.get_by_id(produto_id)
        if not produto:
            return None

        update_data = produto_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(produto, field, value)

        await self.session.flush()
        await self.session.refresh(produto)
        return produto

    async def delete(self, produto_id: int) -> bool:
        """Deleta um produto (soft delete - apenas inativa)"""
        produto = await self.get_by_id(produto_id)
        if not produto:
            return False

        produto.ativo = False
        await self.session.commit()
        return True

    async def search_by_descricao(
        self, termo: str, skip: int = 0, limit: int = 100, apenas_ativos: bool = True
    ) -> List[Produto]:
        """
        Busca produtos por descrição ou código de barras

        Args:
            termo: Termo de busca
            skip: Quantidade de registros para pular
            limit: Limite de registros
            apenas_ativos: Se deve buscar apenas produtos ativos
        """
        query = select(Produto).where(
            or_(
                Produto.descricao.ilike(f"%{termo}%"),
                Produto.codigo_barras.ilike(f"%{termo}%"),
            )
        )

        if apenas_ativos:
            query = query.where(Produto.ativo == True)

        query = query.offset(skip).limit(limit).order_by(Produto.descricao)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_categoria(
        self, categoria_id: int, skip: int = 0, limit: int = 100
    ) -> List[Produto]:
        """
        Busca produtos por categoria

        Args:
            categoria_id: ID da categoria
            skip: Quantidade de registros para pular
            limit: Limite de registros
        """
        query = (
            select(Produto)
            .where(Produto.categoria_id == categoria_id)
            .where(Produto.ativo == True)
            .offset(skip)
            .limit(limit)
            .order_by(Produto.descricao)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_abaixo_estoque_minimo(
        self, skip: int = 0, limit: int = 100
    ) -> List[Produto]:
        """
        Busca produtos com estoque abaixo do mínimo

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
        """
        query = (
            select(Produto)
            .where(Produto.estoque_atual < Produto.estoque_minimo)
            .where(Produto.ativo == True)
            .offset(skip)
            .limit(limit)
            .order_by(Produto.descricao)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
