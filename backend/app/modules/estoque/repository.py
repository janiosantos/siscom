"""
Repository para Movimentações de Estoque
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.estoque.models import MovimentacaoEstoque, TipoMovimentacao
from app.modules.estoque.schemas import MovimentacaoCreate


class MovimentacaoEstoqueRepository:
    """Repository para operações de banco de dados de Movimentações de Estoque"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_movimentacao(
        self, movimentacao_data: MovimentacaoCreate
    ) -> MovimentacaoEstoque:
        """
        Cria uma nova movimentação de estoque

        Args:
            movimentacao_data: Dados da movimentação

        Returns:
            MovimentacaoEstoque criada
        """
        # Calcula valor total
        valor_total = movimentacao_data.quantidade * movimentacao_data.custo_unitario

        movimentacao = MovimentacaoEstoque(
            **movimentacao_data.model_dump(), valor_total=valor_total
        )
        self.session.add(movimentacao)
        await self.session.flush()
        await self.session.refresh(movimentacao)
        return movimentacao

    async def get_by_id(
        self, movimentacao_id: int
    ) -> Optional[MovimentacaoEstoque]:
        """
        Busca movimentação por ID

        Args:
            movimentacao_id: ID da movimentação

        Returns:
            MovimentacaoEstoque ou None se não encontrada
        """
        result = await self.session.execute(
            select(MovimentacaoEstoque).where(MovimentacaoEstoque.id == movimentacao_id)
        )
        return result.scalar_one_or_none()

    async def get_by_produto(
        self,
        produto_id: int,
        skip: int = 0,
        limit: int = 100,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        tipo: Optional[TipoMovimentacao] = None,
    ) -> List[MovimentacaoEstoque]:
        """
        Busca movimentações de um produto específico com filtros opcionais

        Args:
            produto_id: ID do produto
            skip: Quantidade de registros para pular
            limit: Limite de registros
            data_inicio: Data inicial do filtro (opcional)
            data_fim: Data final do filtro (opcional)
            tipo: Tipo de movimentação para filtrar (opcional)

        Returns:
            Lista de movimentações
        """
        query = select(MovimentacaoEstoque).where(
            MovimentacaoEstoque.produto_id == produto_id
        )

        if data_inicio:
            query = query.where(MovimentacaoEstoque.created_at >= data_inicio)

        if data_fim:
            query = query.where(MovimentacaoEstoque.created_at <= data_fim)

        if tipo:
            query = query.where(MovimentacaoEstoque.tipo == tipo)

        query = (
            query.offset(skip)
            .limit(limit)
            .order_by(MovimentacaoEstoque.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        produto_id: Optional[int] = None,
        tipo: Optional[TipoMovimentacao] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> List[MovimentacaoEstoque]:
        """
        Lista todas as movimentações com paginação e filtros

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            produto_id: Filtrar por produto (opcional)
            tipo: Filtrar por tipo de movimentação (opcional)
            data_inicio: Data inicial do filtro (opcional)
            data_fim: Data final do filtro (opcional)

        Returns:
            Lista de movimentações
        """
        query = select(MovimentacaoEstoque)

        if produto_id:
            query = query.where(MovimentacaoEstoque.produto_id == produto_id)

        if tipo:
            query = query.where(MovimentacaoEstoque.tipo == tipo)

        if data_inicio:
            query = query.where(MovimentacaoEstoque.created_at >= data_inicio)

        if data_fim:
            query = query.where(MovimentacaoEstoque.created_at <= data_fim)

        query = (
            query.offset(skip)
            .limit(limit)
            .order_by(MovimentacaoEstoque.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        produto_id: Optional[int] = None,
        tipo: Optional[TipoMovimentacao] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> int:
        """
        Conta total de movimentações com filtros

        Args:
            produto_id: Filtrar por produto (opcional)
            tipo: Filtrar por tipo de movimentação (opcional)
            data_inicio: Data inicial do filtro (opcional)
            data_fim: Data final do filtro (opcional)

        Returns:
            Total de movimentações
        """
        query = select(func.count(MovimentacaoEstoque.id))

        if produto_id:
            query = query.where(MovimentacaoEstoque.produto_id == produto_id)

        if tipo:
            query = query.where(MovimentacaoEstoque.tipo == tipo)

        if data_inicio:
            query = query.where(MovimentacaoEstoque.created_at >= data_inicio)

        if data_fim:
            query = query.where(MovimentacaoEstoque.created_at <= data_fim)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_saldo_atual(self, produto_id: int) -> float:
        """
        Calcula o saldo atual de um produto baseado nas movimentações

        Args:
            produto_id: ID do produto

        Returns:
            Saldo atual calculado (entradas - saídas + ajustes)
        """
        # Calcula entradas
        query_entradas = select(
            func.coalesce(func.sum(MovimentacaoEstoque.quantidade), 0)
        ).where(
            and_(
                MovimentacaoEstoque.produto_id == produto_id,
                MovimentacaoEstoque.tipo.in_(
                    [TipoMovimentacao.ENTRADA, TipoMovimentacao.DEVOLUCAO]
                ),
            )
        )

        result_entradas = await self.session.execute(query_entradas)
        entradas = result_entradas.scalar_one()

        # Calcula saídas
        query_saidas = select(
            func.coalesce(func.sum(MovimentacaoEstoque.quantidade), 0)
        ).where(
            and_(
                MovimentacaoEstoque.produto_id == produto_id,
                MovimentacaoEstoque.tipo.in_(
                    [TipoMovimentacao.SAIDA, TipoMovimentacao.TRANSFERENCIA]
                ),
            )
        )

        result_saidas = await self.session.execute(query_saidas)
        saidas = result_saidas.scalar_one()

        # Calcula ajustes (podem ser positivos ou negativos)
        # Para ajustes, vamos considerar a quantidade com sinal
        query_ajustes = select(
            func.coalesce(func.sum(MovimentacaoEstoque.quantidade), 0)
        ).where(
            and_(
                MovimentacaoEstoque.produto_id == produto_id,
                MovimentacaoEstoque.tipo == TipoMovimentacao.AJUSTE,
            )
        )

        result_ajustes = await self.session.execute(query_ajustes)
        ajustes = result_ajustes.scalar_one()

        # Saldo = Entradas - Saídas + Ajustes
        # Nota: Ajustes positivos aumentam, negativos diminuem
        saldo = float(entradas) - float(saidas) + float(ajustes)
        return saldo

    async def get_movimentacoes_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MovimentacaoEstoque]:
        """
        Busca movimentações em um período específico

        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de movimentações no período
        """
        query = (
            select(MovimentacaoEstoque)
            .where(
                and_(
                    MovimentacaoEstoque.created_at >= data_inicio,
                    MovimentacaoEstoque.created_at <= data_fim,
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(MovimentacaoEstoque.created_at.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_entradas_por_produto(
        self, produto_id: int, skip: int = 0, limit: int = 100
    ) -> List[MovimentacaoEstoque]:
        """
        Busca apenas entradas de um produto específico

        Args:
            produto_id: ID do produto
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de movimentações de entrada
        """
        query = (
            select(MovimentacaoEstoque)
            .where(
                and_(
                    MovimentacaoEstoque.produto_id == produto_id,
                    MovimentacaoEstoque.tipo == TipoMovimentacao.ENTRADA,
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(MovimentacaoEstoque.created_at.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_saidas_por_produto(
        self, produto_id: int, skip: int = 0, limit: int = 100
    ) -> List[MovimentacaoEstoque]:
        """
        Busca apenas saídas de um produto específico

        Args:
            produto_id: ID do produto
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de movimentações de saída
        """
        query = (
            select(MovimentacaoEstoque)
            .where(
                and_(
                    MovimentacaoEstoque.produto_id == produto_id,
                    MovimentacaoEstoque.tipo == TipoMovimentacao.SAIDA,
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(MovimentacaoEstoque.created_at.desc())
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())
