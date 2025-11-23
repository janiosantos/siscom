"""
Repository para PDV
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.pdv.models import Caixa, MovimentacaoCaixa, StatusCaixa, TipoMovimentacaoCaixa
from app.modules.pdv.schemas import AbrirCaixaCreate, MovimentacaoCaixaCreate


class CaixaRepository:
    """Repository para operações de banco de dados de Caixa"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def abrir_caixa(self, caixa_data: AbrirCaixaCreate) -> Caixa:
        """
        Abre um novo caixa

        Args:
            caixa_data: Dados do caixa

        Returns:
            Caixa criado
        """
        caixa = Caixa(
            operador_id=caixa_data.operador_id,
            valor_abertura=caixa_data.valor_abertura,
            status=StatusCaixa.ABERTO,
        )
        self.session.add(caixa)
        await self.session.flush()
        await self.session.refresh(caixa)
        return caixa

    async def fechar_caixa(
        self, caixa_id: int, valor_fechamento: float
    ) -> Optional[Caixa]:
        """
        Fecha um caixa

        Args:
            caixa_id: ID do caixa
            valor_fechamento: Valor de fechamento

        Returns:
            Caixa fechado ou None
        """
        caixa = await self.get_by_id(caixa_id)
        if not caixa:
            return None

        caixa.status = StatusCaixa.FECHADO
        caixa.data_fechamento = datetime.utcnow()
        caixa.valor_fechamento = valor_fechamento

        await self.session.flush()
        await self.session.refresh(caixa)
        return caixa

    async def get_by_id(self, caixa_id: int) -> Optional[Caixa]:
        """
        Busca caixa por ID

        Args:
            caixa_id: ID do caixa

        Returns:
            Caixa ou None
        """
        result = await self.session.execute(
            select(Caixa)
            .options(selectinload(Caixa.movimentacoes))
            .where(Caixa.id == caixa_id)
        )
        return result.scalar_one_or_none()

    async def get_caixa_aberto(self, operador_id: int) -> Optional[Caixa]:
        """
        Busca caixa aberto de um operador

        Args:
            operador_id: ID do operador

        Returns:
            Caixa aberto ou None
        """
        result = await self.session.execute(
            select(Caixa)
            .options(selectinload(Caixa.movimentacoes))
            .where(
                and_(
                    Caixa.operador_id == operador_id,
                    Caixa.status == StatusCaixa.ABERTO,
                )
            )
            .order_by(Caixa.data_abertura.desc())
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        operador_id: Optional[int] = None,
        status: Optional[StatusCaixa] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> List[Caixa]:
        """
        Lista todos os caixas com paginação e filtros

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            operador_id: Filtrar por operador
            status: Filtrar por status
            data_inicio: Data inicial do filtro
            data_fim: Data final do filtro

        Returns:
            Lista de caixas
        """
        query = select(Caixa).options(selectinload(Caixa.movimentacoes))

        if operador_id:
            query = query.where(Caixa.operador_id == operador_id)

        if status:
            query = query.where(Caixa.status == status)

        if data_inicio:
            query = query.where(Caixa.data_abertura >= data_inicio)

        if data_fim:
            query = query.where(Caixa.data_abertura <= data_fim)

        query = query.offset(skip).limit(limit).order_by(Caixa.data_abertura.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        operador_id: Optional[int] = None,
        status: Optional[StatusCaixa] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> int:
        """
        Conta total de caixas

        Args:
            operador_id: Filtrar por operador
            status: Filtrar por status
            data_inicio: Data inicial do filtro
            data_fim: Data final do filtro

        Returns:
            Total de caixas
        """
        query = select(func.count(Caixa.id))

        if operador_id:
            query = query.where(Caixa.operador_id == operador_id)

        if status:
            query = query.where(Caixa.status == status)

        if data_inicio:
            query = query.where(Caixa.data_abertura >= data_inicio)

        if data_fim:
            query = query.where(Caixa.data_abertura <= data_fim)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def registrar_movimentacao(
        self,
        caixa_id: int,
        tipo: TipoMovimentacaoCaixa,
        valor: float,
        descricao: Optional[str] = None,
        venda_id: Optional[int] = None,
    ) -> MovimentacaoCaixa:
        """
        Registra uma movimentação no caixa

        Args:
            caixa_id: ID do caixa
            tipo: Tipo de movimentação
            valor: Valor da movimentação
            descricao: Descrição (opcional)
            venda_id: ID da venda (opcional)

        Returns:
            Movimentação criada
        """
        movimentacao = MovimentacaoCaixa(
            caixa_id=caixa_id,
            tipo=tipo,
            valor=valor,
            descricao=descricao,
            venda_id=venda_id,
        )
        self.session.add(movimentacao)
        await self.session.flush()
        await self.session.refresh(movimentacao)
        return movimentacao

    async def get_movimentacoes_caixa(
        self, caixa_id: int, tipo: Optional[TipoMovimentacaoCaixa] = None
    ) -> List[MovimentacaoCaixa]:
        """
        Busca movimentações de um caixa

        Args:
            caixa_id: ID do caixa
            tipo: Filtrar por tipo (opcional)

        Returns:
            Lista de movimentações
        """
        query = select(MovimentacaoCaixa).where(MovimentacaoCaixa.caixa_id == caixa_id)

        if tipo:
            query = query.where(MovimentacaoCaixa.tipo == tipo)

        query = query.order_by(MovimentacaoCaixa.created_at.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def calcular_saldo_caixa(self, caixa_id: int) -> dict:
        """
        Calcula o saldo do caixa

        Args:
            caixa_id: ID do caixa

        Returns:
            Dicionário com totais por tipo de movimentação
        """
        # Busca todas as movimentações do caixa
        movimentacoes = await self.get_movimentacoes_caixa(caixa_id)

        # Inicializa totais
        totais = {
            "entradas": 0.0,
            "saidas": 0.0,
            "sangrias": 0.0,
            "suprimentos": 0.0,
        }

        # Calcula totais
        for mov in movimentacoes:
            if mov.tipo == TipoMovimentacaoCaixa.ENTRADA:
                totais["entradas"] += float(mov.valor)
            elif mov.tipo == TipoMovimentacaoCaixa.SAIDA:
                totais["saidas"] += float(mov.valor)
            elif mov.tipo == TipoMovimentacaoCaixa.SANGRIA:
                totais["sangrias"] += float(mov.valor)
            elif mov.tipo == TipoMovimentacaoCaixa.SUPRIMENTO:
                totais["suprimentos"] += float(mov.valor)

        return totais

    async def get_total_por_tipo(
        self, caixa_id: int, tipo: TipoMovimentacaoCaixa
    ) -> float:
        """
        Calcula total de movimentações de um tipo específico

        Args:
            caixa_id: ID do caixa
            tipo: Tipo de movimentação

        Returns:
            Total de movimentações do tipo
        """
        result = await self.session.execute(
            select(func.sum(MovimentacaoCaixa.valor)).where(
                and_(
                    MovimentacaoCaixa.caixa_id == caixa_id,
                    MovimentacaoCaixa.tipo == tipo,
                )
            )
        )
        total = result.scalar_one_or_none()
        return float(total) if total else 0.0
