"""
Repository para Lotes de Estoque
"""
from typing import Optional, List
from datetime import date, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.estoque.models import LoteEstoque
from app.modules.estoque.schemas import LoteEstoqueCreate


class LoteEstoqueRepository:
    """Repository para operações de banco de dados de Lotes de Estoque"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_lote(self, lote_data: LoteEstoqueCreate) -> LoteEstoque:
        """
        Cria um novo lote de estoque

        Args:
            lote_data: Dados do lote

        Returns:
            LoteEstoque criado
        """
        lote = LoteEstoque(
            **lote_data.model_dump(),
            quantidade_atual=lote_data.quantidade_inicial
        )
        self.session.add(lote)
        await self.session.flush()
        await self.session.refresh(lote)
        return lote

    async def get_by_id(self, lote_id: int) -> Optional[LoteEstoque]:
        """
        Busca lote por ID

        Args:
            lote_id: ID do lote

        Returns:
            LoteEstoque ou None se não encontrado
        """
        result = await self.session.execute(
            select(LoteEstoque).where(LoteEstoque.id == lote_id)
        )
        return result.scalar_one_or_none()

    async def get_by_produto(
        self,
        produto_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LoteEstoque]:
        """
        Busca todos os lotes de um produto específico

        Args:
            produto_id: ID do produto
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de lotes do produto
        """
        query = (
            select(LoteEstoque)
            .where(LoteEstoque.produto_id == produto_id)
            .order_by(LoteEstoque.data_validade.asc(), LoteEstoque.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LoteEstoque]:
        """
        Lista todos os lotes com paginação

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de lotes
        """
        query = (
            select(LoteEstoque)
            .order_by(LoteEstoque.data_validade.asc(), LoteEstoque.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_lotes_disponiveis(
        self, produto_id: int
    ) -> List[LoteEstoque]:
        """
        Busca lotes disponíveis (quantidade_atual > 0) de um produto

        Args:
            produto_id: ID do produto

        Returns:
            Lista de lotes disponíveis ordenados por data de validade (FIFO)
        """
        query = (
            select(LoteEstoque)
            .where(
                and_(
                    LoteEstoque.produto_id == produto_id,
                    LoteEstoque.quantidade_atual > 0
                )
            )
            .order_by(LoteEstoque.data_validade.asc(), LoteEstoque.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_lote_mais_antigo_disponivel(
        self, produto_id: int
    ) -> Optional[LoteEstoque]:
        """
        Busca o lote mais antigo disponível (FIFO) de um produto
        Prioriza pela data de validade mais próxima

        Args:
            produto_id: ID do produto

        Returns:
            LoteEstoque mais antigo disponível ou None se não houver
        """
        query = (
            select(LoteEstoque)
            .where(
                and_(
                    LoteEstoque.produto_id == produto_id,
                    LoteEstoque.quantidade_atual > 0
                )
            )
            .order_by(LoteEstoque.data_validade.asc(), LoteEstoque.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_lotes_vencidos(
        self,
        data_referencia: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LoteEstoque]:
        """
        Busca lotes vencidos

        Args:
            data_referencia: Data de referência (padrão: hoje)
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de lotes vencidos
        """
        if data_referencia is None:
            data_referencia = date.today()

        query = (
            select(LoteEstoque)
            .where(LoteEstoque.data_validade < data_referencia)
            .order_by(LoteEstoque.data_validade.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_lotes_a_vencer(
        self,
        dias: int = 30,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LoteEstoque]:
        """
        Busca lotes que vencem nos próximos N dias

        Args:
            dias: Número de dias para verificar (padrão: 30)
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de lotes a vencer
        """
        hoje = date.today()
        data_limite = hoje + timedelta(days=dias)

        query = (
            select(LoteEstoque)
            .where(
                and_(
                    LoteEstoque.data_validade >= hoje,
                    LoteEstoque.data_validade <= data_limite,
                    LoteEstoque.quantidade_atual > 0
                )
            )
            .order_by(LoteEstoque.data_validade.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def dar_baixa_lote(
        self, lote_id: int, quantidade: float
    ) -> Optional[LoteEstoque]:
        """
        Dá baixa em um lote, reduzindo a quantidade_atual

        Args:
            lote_id: ID do lote
            quantidade: Quantidade a reduzir

        Returns:
            LoteEstoque atualizado ou None se não encontrado
        """
        lote = await self.get_by_id(lote_id)
        if not lote:
            return None

        lote.quantidade_atual = float(lote.quantidade_atual) - quantidade
        await self.session.flush()
        await self.session.refresh(lote)
        return lote

    async def get_lotes_zerados(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LoteEstoque]:
        """
        Busca lotes com quantidade zerada

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de lotes zerados
        """
        query = (
            select(LoteEstoque)
            .where(LoteEstoque.quantidade_atual <= 0)
            .order_by(LoteEstoque.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_produto(self, produto_id: int) -> int:
        """
        Conta total de lotes de um produto

        Args:
            produto_id: ID do produto

        Returns:
            Total de lotes
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(LoteEstoque.id)).where(
                LoteEstoque.produto_id == produto_id
            )
        )
        return result.scalar_one()

    async def get_estoque_total_por_produto(self, produto_id: int) -> float:
        """
        Calcula o estoque total de um produto somando todos os lotes disponíveis

        Args:
            produto_id: ID do produto

        Returns:
            Estoque total (soma de quantidade_atual de todos os lotes)
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.coalesce(func.sum(LoteEstoque.quantidade_atual), 0)).where(
                LoteEstoque.produto_id == produto_id
            )
        )
        return float(result.scalar_one())
