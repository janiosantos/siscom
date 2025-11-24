"""
Repository para Financeiro
"""
from typing import Optional, List, Tuple
from datetime import date, datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.financeiro.models import ContaPagar, ContaReceber, StatusFinanceiro
from app.modules.financeiro.schemas import (
    ContaPagarCreate,
    ContaPagarUpdate,
    ContaReceberCreate,
    ContaReceberUpdate,
    BaixaPagamentoCreate,
    BaixaRecebimentoCreate,
)


class ContaPagarRepository:
    """Repository para operações de banco de dados de Contas a Pagar"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conta_data: ContaPagarCreate) -> ContaPagar:
        """Cria uma nova conta a pagar"""
        conta = ContaPagar(**conta_data.model_dump())
        conta.status = StatusFinanceiro.PENDENTE
        conta.valor_pago = 0.0
        self.session.add(conta)
        await self.session.flush()
        await self.session.refresh(conta)
        return conta

    async def get_by_id(self, conta_id: int) -> Optional[ContaPagar]:
        """Busca conta a pagar por ID"""
        result = await self.session.execute(
            select(ContaPagar).where(ContaPagar.id == conta_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        fornecedor_id: Optional[int] = None,
        status: Optional[StatusFinanceiro] = None,
        categoria: Optional[str] = None,
    ) -> List[ContaPagar]:
        """Lista todas as contas a pagar com filtros"""
        query = select(ContaPagar)

        if fornecedor_id:
            query = query.where(ContaPagar.fornecedor_id == fornecedor_id)

        if status:
            query = query.where(ContaPagar.status == status)

        if categoria:
            query = query.where(ContaPagar.categoria_financeira == categoria)

        query = query.offset(skip).limit(limit).order_by(ContaPagar.data_vencimento)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        fornecedor_id: Optional[int] = None,
        status: Optional[StatusFinanceiro] = None,
        categoria: Optional[str] = None,
    ) -> int:
        """Conta total de contas a pagar"""
        query = select(func.count(ContaPagar.id))

        if fornecedor_id:
            query = query.where(ContaPagar.fornecedor_id == fornecedor_id)

        if status:
            query = query.where(ContaPagar.status == status)

        if categoria:
            query = query.where(ContaPagar.categoria_financeira == categoria)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(
        self, conta_id: int, conta_data: ContaPagarUpdate
    ) -> Optional[ContaPagar]:
        """Atualiza uma conta a pagar"""
        conta = await self.get_by_id(conta_id)
        if not conta:
            return None

        update_data = conta_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conta, field, value)

        await self.session.flush()
        await self.session.refresh(conta)
        return conta

    async def baixar_pagamento(
        self, conta_id: int, baixa_data: BaixaPagamentoCreate
    ) -> Optional[ContaPagar]:
        """Registra pagamento de conta a pagar"""
        conta = await self.get_by_id(conta_id)
        if not conta:
            return None

        # Atualiza valor pago
        conta.valor_pago += baixa_data.valor_pago
        conta.data_pagamento = baixa_data.data_pagamento

        # Atualiza observações se fornecidas
        if baixa_data.observacoes:
            if conta.observacoes:
                conta.observacoes += f"\n{baixa_data.observacoes}"
            else:
                conta.observacoes = baixa_data.observacoes

        # Atualiza status
        if conta.valor_pago >= conta.valor_original:
            conta.status = StatusFinanceiro.PAGA
        else:
            # Se pagamento parcial, mantém status atual ou define como PENDENTE
            if conta.status != StatusFinanceiro.ATRASADA:
                conta.status = StatusFinanceiro.PENDENTE

        await self.session.flush()
        await self.session.refresh(conta)
        return conta

    async def cancelar(self, conta_id: int) -> Optional[ContaPagar]:
        """Cancela uma conta a pagar"""
        conta = await self.get_by_id(conta_id)
        if not conta:
            return None

        conta.status = StatusFinanceiro.CANCELADA
        await self.session.flush()
        await self.session.refresh(conta)
        return conta

    async def get_pendentes(
        self, skip: int = 0, limit: int = 100
    ) -> List[ContaPagar]:
        """Lista contas a pagar pendentes"""
        query = (
            select(ContaPagar)
            .where(ContaPagar.status == StatusFinanceiro.PENDENTE)
            .offset(skip)
            .limit(limit)
            .order_by(ContaPagar.data_vencimento)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_vencidas(
        self, skip: int = 0, limit: int = 100
    ) -> List[ContaPagar]:
        """Lista contas a pagar vencidas"""
        hoje = date.today()
        query = (
            select(ContaPagar)
            .where(
                and_(
                    ContaPagar.status.in_([StatusFinanceiro.PENDENTE, StatusFinanceiro.ATRASADA]),
                    ContaPagar.data_vencimento < hoje
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(ContaPagar.data_vencimento)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_por_periodo(
        self, data_inicio: date, data_fim: date
    ) -> List[ContaPagar]:
        """Lista contas a pagar por período de vencimento"""
        query = (
            select(ContaPagar)
            .where(
                and_(
                    ContaPagar.data_vencimento >= data_inicio,
                    ContaPagar.data_vencimento <= data_fim
                )
            )
            .order_by(ContaPagar.data_vencimento)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def calcular_totais_periodo(
        self, data_inicio: date, data_fim: date
    ) -> Tuple[float, float]:
        """Calcula totais a pagar e pago no período"""
        # Total a pagar (pendentes no período)
        query_a_pagar = select(func.sum(ContaPagar.valor_original - ContaPagar.valor_pago)).where(
            and_(
                ContaPagar.data_vencimento >= data_inicio,
                ContaPagar.data_vencimento <= data_fim,
                ContaPagar.status.in_([StatusFinanceiro.PENDENTE, StatusFinanceiro.ATRASADA])
            )
        )
        result_a_pagar = await self.session.execute(query_a_pagar)
        total_a_pagar = result_a_pagar.scalar_one() or 0.0

        # Total pago no período
        query_pago = select(func.sum(ContaPagar.valor_pago)).where(
            and_(
                ContaPagar.data_pagamento >= data_inicio,
                ContaPagar.data_pagamento <= data_fim,
                ContaPagar.status == StatusFinanceiro.PAGA
            )
        )
        result_pago = await self.session.execute(query_pago)
        total_pago = result_pago.scalar_one() or 0.0

        return total_a_pagar, total_pago


class ContaReceberRepository:
    """Repository para operações de banco de dados de Contas a Receber"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, conta_data: ContaReceberCreate) -> ContaReceber:
        """Cria uma nova conta a receber"""
        conta = ContaReceber(**conta_data.model_dump())
        conta.status = StatusFinanceiro.PENDENTE
        conta.valor_recebido = 0.0
        self.session.add(conta)
        await self.session.flush()
        await self.session.refresh(conta)
        return conta

    async def get_by_id(self, conta_id: int) -> Optional[ContaReceber]:
        """Busca conta a receber por ID"""
        result = await self.session.execute(
            select(ContaReceber).where(ContaReceber.id == conta_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        cliente_id: Optional[int] = None,
        status: Optional[StatusFinanceiro] = None,
        categoria: Optional[str] = None,
    ) -> List[ContaReceber]:
        """Lista todas as contas a receber com filtros"""
        query = select(ContaReceber)

        if cliente_id:
            query = query.where(ContaReceber.cliente_id == cliente_id)

        if status:
            query = query.where(ContaReceber.status == status)

        if categoria:
            query = query.where(ContaReceber.categoria_financeira == categoria)

        query = query.offset(skip).limit(limit).order_by(ContaReceber.data_vencimento)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        cliente_id: Optional[int] = None,
        status: Optional[StatusFinanceiro] = None,
        categoria: Optional[str] = None,
    ) -> int:
        """Conta total de contas a receber"""
        query = select(func.count(ContaReceber.id))

        if cliente_id:
            query = query.where(ContaReceber.cliente_id == cliente_id)

        if status:
            query = query.where(ContaReceber.status == status)

        if categoria:
            query = query.where(ContaReceber.categoria_financeira == categoria)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(
        self, conta_id: int, conta_data: ContaReceberUpdate
    ) -> Optional[ContaReceber]:
        """Atualiza uma conta a receber"""
        conta = await self.get_by_id(conta_id)
        if not conta:
            return None

        update_data = conta_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conta, field, value)

        await self.session.flush()
        await self.session.refresh(conta)
        return conta

    async def baixar_recebimento(
        self, conta_id: int, baixa_data: BaixaRecebimentoCreate
    ) -> Optional[ContaReceber]:
        """Registra recebimento de conta a receber"""
        conta = await self.get_by_id(conta_id)
        if not conta:
            return None

        # Atualiza valor recebido
        conta.valor_recebido += baixa_data.valor_recebido
        conta.data_recebimento = baixa_data.data_recebimento

        # Atualiza observações se fornecidas
        if baixa_data.observacoes:
            if conta.observacoes:
                conta.observacoes += f"\n{baixa_data.observacoes}"
            else:
                conta.observacoes = baixa_data.observacoes

        # Atualiza status
        if conta.valor_recebido >= conta.valor_original:
            conta.status = StatusFinanceiro.RECEBIDA
        else:
            # Se recebimento parcial, mantém status atual ou define como PENDENTE
            if conta.status != StatusFinanceiro.ATRASADA:
                conta.status = StatusFinanceiro.PENDENTE

        await self.session.flush()
        await self.session.refresh(conta)
        return conta

    async def cancelar(self, conta_id: int) -> Optional[ContaReceber]:
        """Cancela uma conta a receber"""
        conta = await self.get_by_id(conta_id)
        if not conta:
            return None

        conta.status = StatusFinanceiro.CANCELADA
        await self.session.flush()
        await self.session.refresh(conta)
        return conta

    async def get_pendentes(
        self, skip: int = 0, limit: int = 100
    ) -> List[ContaReceber]:
        """Lista contas a receber pendentes"""
        query = (
            select(ContaReceber)
            .where(ContaReceber.status == StatusFinanceiro.PENDENTE)
            .offset(skip)
            .limit(limit)
            .order_by(ContaReceber.data_vencimento)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_vencidas(
        self, skip: int = 0, limit: int = 100
    ) -> List[ContaReceber]:
        """Lista contas a receber vencidas"""
        hoje = date.today()
        query = (
            select(ContaReceber)
            .where(
                and_(
                    ContaReceber.status.in_([StatusFinanceiro.PENDENTE, StatusFinanceiro.ATRASADA]),
                    ContaReceber.data_vencimento < hoje
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(ContaReceber.data_vencimento)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_por_periodo(
        self, data_inicio: date, data_fim: date
    ) -> List[ContaReceber]:
        """Lista contas a receber por período de vencimento"""
        query = (
            select(ContaReceber)
            .where(
                and_(
                    ContaReceber.data_vencimento >= data_inicio,
                    ContaReceber.data_vencimento <= data_fim
                )
            )
            .order_by(ContaReceber.data_vencimento)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def calcular_totais_periodo(
        self, data_inicio: date, data_fim: date
    ) -> Tuple[float, float]:
        """Calcula totais a receber e recebido no período"""
        # Total a receber (pendentes no período)
        query_a_receber = select(func.sum(ContaReceber.valor_original - ContaReceber.valor_recebido)).where(
            and_(
                ContaReceber.data_vencimento >= data_inicio,
                ContaReceber.data_vencimento <= data_fim,
                ContaReceber.status.in_([StatusFinanceiro.PENDENTE, StatusFinanceiro.ATRASADA])
            )
        )
        result_a_receber = await self.session.execute(query_a_receber)
        total_a_receber = result_a_receber.scalar_one() or 0.0

        # Total recebido no período
        query_recebido = select(func.sum(ContaReceber.valor_recebido)).where(
            and_(
                ContaReceber.data_recebimento >= data_inicio,
                ContaReceber.data_recebimento <= data_fim,
                ContaReceber.status == StatusFinanceiro.RECEBIDA
            )
        )
        result_recebido = await self.session.execute(query_recebido)
        total_recebido = result_recebido.scalar_one() or 0.0

        return total_a_receber, total_recebido
