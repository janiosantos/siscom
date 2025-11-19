"""
Repository para Orçamentos
"""
from typing import Optional, List
from datetime import datetime, date, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.orcamentos.models import Orcamento, ItemOrcamento, StatusOrcamento
from app.modules.orcamentos.schemas import OrcamentoCreate, ItemOrcamentoCreate


class OrcamentoRepository:
    """Repository para operações de banco de dados de Orçamentos"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def calcular_data_validade(self, data_orcamento: datetime, validade_dias: int) -> date:
        """
        Calcula a data de validade do orçamento

        Args:
            data_orcamento: Data do orçamento
            validade_dias: Quantidade de dias de validade

        Returns:
            Data de validade
        """
        data_validade = data_orcamento + timedelta(days=validade_dias)
        return data_validade.date()

    async def create_orcamento(self, orcamento_data: OrcamentoCreate) -> Orcamento:
        """
        Cria um novo orçamento (sem itens)

        Args:
            orcamento_data: Dados do orçamento

        Returns:
            Orçamento criado
        """
        orcamento_dict = orcamento_data.model_dump(exclude={"itens"})

        # Calcula data de validade
        data_orcamento = datetime.utcnow()
        data_validade = self.calcular_data_validade(data_orcamento, orcamento_data.validade_dias)

        orcamento = Orcamento(
            **orcamento_dict,
            data_orcamento=data_orcamento,
            data_validade=data_validade
        )
        self.session.add(orcamento)
        await self.session.flush()
        await self.session.refresh(orcamento)
        return orcamento

    async def create_item_orcamento(
        self, orcamento_id: int, item_data: ItemOrcamentoCreate, total: float
    ) -> ItemOrcamento:
        """
        Cria um item de orçamento

        Args:
            orcamento_id: ID do orçamento
            item_data: Dados do item
            total: Total do item (quantidade * preco_unitario - desconto)

        Returns:
            Item criado
        """
        item = ItemOrcamento(
            orcamento_id=orcamento_id,
            produto_id=item_data.produto_id,
            quantidade=item_data.quantidade,
            preco_unitario=item_data.preco_unitario,
            desconto_item=item_data.desconto_item,
            total_item=total,
            observacao_item=item_data.observacao_item,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def get_by_id(self, orcamento_id: int) -> Optional[Orcamento]:
        """
        Busca orçamento por ID com seus itens

        Args:
            orcamento_id: ID do orçamento

        Returns:
            Orçamento com itens ou None
        """
        result = await self.session.execute(
            select(Orcamento)
            .options(selectinload(Orcamento.itens))
            .where(Orcamento.id == orcamento_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[StatusOrcamento] = None,
        cliente_id: Optional[int] = None,
        vendedor_id: Optional[int] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> List[Orcamento]:
        """
        Lista todos os orçamentos com paginação e filtros

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            status: Filtrar por status
            cliente_id: Filtrar por cliente
            vendedor_id: Filtrar por vendedor
            data_inicio: Data inicial do filtro
            data_fim: Data final do filtro

        Returns:
            Lista de orçamentos
        """
        query = select(Orcamento).options(selectinload(Orcamento.itens))

        if status:
            query = query.where(Orcamento.status == status)

        if cliente_id:
            query = query.where(Orcamento.cliente_id == cliente_id)

        if vendedor_id:
            query = query.where(Orcamento.vendedor_id == vendedor_id)

        if data_inicio:
            query = query.where(Orcamento.data_orcamento >= data_inicio)

        if data_fim:
            query = query.where(Orcamento.data_orcamento <= data_fim)

        query = query.offset(skip).limit(limit).order_by(Orcamento.data_orcamento.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        status: Optional[StatusOrcamento] = None,
        cliente_id: Optional[int] = None,
        vendedor_id: Optional[int] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> int:
        """
        Conta total de orçamentos

        Args:
            status: Filtrar por status
            cliente_id: Filtrar por cliente
            vendedor_id: Filtrar por vendedor
            data_inicio: Data inicial do filtro
            data_fim: Data final do filtro

        Returns:
            Total de orçamentos
        """
        query = select(func.count(Orcamento.id))

        if status:
            query = query.where(Orcamento.status == status)

        if cliente_id:
            query = query.where(Orcamento.cliente_id == cliente_id)

        if vendedor_id:
            query = query.where(Orcamento.vendedor_id == vendedor_id)

        if data_inicio:
            query = query.where(Orcamento.data_orcamento >= data_inicio)

        if data_fim:
            query = query.where(Orcamento.data_orcamento <= data_fim)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_por_cliente(
        self, cliente_id: int, skip: int = 0, limit: int = 100
    ) -> List[Orcamento]:
        """
        Busca orçamentos por cliente

        Args:
            cliente_id: ID do cliente
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de orçamentos do cliente
        """
        query = (
            select(Orcamento)
            .options(selectinload(Orcamento.itens))
            .where(Orcamento.cliente_id == cliente_id)
            .offset(skip)
            .limit(limit)
            .order_by(Orcamento.data_orcamento.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_por_status(
        self, status: StatusOrcamento, skip: int = 0, limit: int = 100
    ) -> List[Orcamento]:
        """
        Busca orçamentos por status

        Args:
            status: Status do orçamento
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de orçamentos com o status especificado
        """
        query = (
            select(Orcamento)
            .options(selectinload(Orcamento.itens))
            .where(Orcamento.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Orcamento.data_orcamento.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_por_vendedor(
        self, vendedor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Orcamento]:
        """
        Busca orçamentos por vendedor

        Args:
            vendedor_id: ID do vendedor
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de orçamentos do vendedor
        """
        query = (
            select(Orcamento)
            .options(selectinload(Orcamento.itens))
            .where(Orcamento.vendedor_id == vendedor_id)
            .offset(skip)
            .limit(limit)
            .order_by(Orcamento.data_orcamento.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_orcamentos_vencidos(
        self, skip: int = 0, limit: int = 100
    ) -> List[Orcamento]:
        """
        Busca orçamentos vencidos (data_validade < hoje e status = ABERTO ou APROVADO)

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de orçamentos vencidos
        """
        hoje = date.today()
        query = (
            select(Orcamento)
            .options(selectinload(Orcamento.itens))
            .where(
                and_(
                    Orcamento.data_validade < hoje,
                    Orcamento.status.in_([StatusOrcamento.ABERTO, StatusOrcamento.APROVADO])
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(Orcamento.data_validade.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_orcamentos_a_vencer(
        self, dias: int, skip: int = 0, limit: int = 100
    ) -> List[Orcamento]:
        """
        Busca orçamentos a vencer nos próximos N dias

        Args:
            dias: Quantidade de dias à frente para verificar
            skip: Quantidade de registros para pular
            limit: Limite de registros

        Returns:
            Lista de orçamentos a vencer
        """
        hoje = date.today()
        data_limite = hoje + timedelta(days=dias)

        query = (
            select(Orcamento)
            .options(selectinload(Orcamento.itens))
            .where(
                and_(
                    Orcamento.data_validade >= hoje,
                    Orcamento.data_validade <= data_limite,
                    Orcamento.status.in_([StatusOrcamento.ABERTO, StatusOrcamento.APROVADO])
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(Orcamento.data_validade.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def atualizar_status(
        self, orcamento_id: int, status: StatusOrcamento
    ) -> Optional[Orcamento]:
        """
        Atualiza o status de um orçamento

        Args:
            orcamento_id: ID do orçamento
            status: Novo status

        Returns:
            Orçamento atualizado ou None
        """
        orcamento = await self.get_by_id(orcamento_id)
        if not orcamento:
            return None

        orcamento.status = status
        await self.session.flush()
        await self.session.refresh(orcamento)
        return orcamento

    async def get_itens_orcamento(self, orcamento_id: int) -> List[ItemOrcamento]:
        """
        Busca itens de um orçamento

        Args:
            orcamento_id: ID do orçamento

        Returns:
            Lista de itens do orçamento
        """
        result = await self.session.execute(
            select(ItemOrcamento).where(ItemOrcamento.orcamento_id == orcamento_id)
        )
        return list(result.scalars().all())

    async def atualizar_totais_orcamento(
        self, orcamento_id: int, subtotal: float, desconto: float, valor_total: float
    ) -> Optional[Orcamento]:
        """
        Atualiza os totais de um orçamento

        Args:
            orcamento_id: ID do orçamento
            subtotal: Subtotal
            desconto: Desconto
            valor_total: Valor total

        Returns:
            Orçamento atualizado ou None
        """
        orcamento = await self.get_by_id(orcamento_id)
        if not orcamento:
            return None

        orcamento.subtotal = subtotal
        orcamento.desconto = desconto
        orcamento.valor_total = valor_total
        await self.session.flush()
        await self.session.refresh(orcamento)
        return orcamento

    async def atualizar_orcamento(
        self, orcamento_id: int, cliente_id: Optional[int] = None,
        validade_dias: Optional[int] = None, desconto: Optional[float] = None,
        observacoes: Optional[str] = None
    ) -> Optional[Orcamento]:
        """
        Atualiza um orçamento

        Args:
            orcamento_id: ID do orçamento
            cliente_id: Novo ID do cliente (opcional)
            validade_dias: Nova validade em dias (opcional)
            desconto: Novo desconto (opcional)
            observacoes: Novas observações (opcional)

        Returns:
            Orçamento atualizado ou None
        """
        orcamento = await self.get_by_id(orcamento_id)
        if not orcamento:
            return None

        if cliente_id is not None:
            orcamento.cliente_id = cliente_id

        if validade_dias is not None:
            orcamento.validade_dias = validade_dias
            # Recalcula data de validade
            orcamento.data_validade = self.calcular_data_validade(
                orcamento.data_orcamento, validade_dias
            )

        if desconto is not None:
            orcamento.desconto = desconto
            # Recalcula valor total
            orcamento.valor_total = orcamento.subtotal - desconto

        if observacoes is not None:
            orcamento.observacoes = observacoes

        await self.session.flush()
        await self.session.refresh(orcamento)
        return orcamento

    async def deletar_orcamento(self, orcamento_id: int) -> bool:
        """
        Deleta um orçamento

        Args:
            orcamento_id: ID do orçamento

        Returns:
            True se deletado, False se não encontrado
        """
        orcamento = await self.get_by_id(orcamento_id)
        if not orcamento:
            return False

        await self.session.delete(orcamento)
        await self.session.flush()
        return True
