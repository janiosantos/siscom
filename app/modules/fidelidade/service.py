"""
Service para Programa de Fidelidade
"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fidelidade.models import (
    ProgramaFidelidade,
    SaldoPontos,
    MovimentacaoPontos,
    TipoMovimentacaoPontos,
)
from app.modules.fidelidade.schemas import (
    ProgramaFidelidadeCreate,
    ProgramaFidelidadeUpdate,
    ProgramaFidelidadeResponse,
    SaldoPontosResponse,
    ConsultarSaldoResponse,
    MovimentacaoPontosResponse,
    AcumularPontosRequest,
    ResgatarPontosRequest,
    ResgatarPontosResponse,
    ExtratoResponse,
)
from app.modules.clientes.repository import ClienteRepository
from app.core.exceptions import NotFoundException, ValidationException


class FidelidadeService:
    """Service para programa de fidelidade"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.cliente_repository = ClienteRepository(session)

    # ==================== PROGRAMA ====================

    async def criar_programa(
        self, data: ProgramaFidelidadeCreate
    ) -> ProgramaFidelidadeResponse:
        """Cria programa de fidelidade"""
        programa = ProgramaFidelidade(**data.model_dump())
        self.session.add(programa)
        await self.session.flush()
        await self.session.refresh(programa)
        return ProgramaFidelidadeResponse.model_validate(programa)

    async def get_programa(self, programa_id: int) -> ProgramaFidelidadeResponse:
        """Busca programa por ID"""
        query = select(ProgramaFidelidade).where(ProgramaFidelidade.id == programa_id)
        result = await self.session.execute(query)
        programa = result.scalar_one_or_none()

        if not programa:
            raise NotFoundException(f"Programa {programa_id} não encontrado")

        return ProgramaFidelidadeResponse.model_validate(programa)

    async def get_programa_ativo(self) -> ProgramaFidelidade:
        """Retorna programa ativo (primeiro encontrado)"""
        query = select(ProgramaFidelidade).where(ProgramaFidelidade.ativo == True).limit(1)
        result = await self.session.execute(query)
        programa = result.scalar_one_or_none()

        if not programa:
            raise NotFoundException("Nenhum programa de fidelidade ativo encontrado")

        return programa

    # ==================== SALDO ====================

    async def get_ou_criar_saldo(
        self, cliente_id: int, programa_id: Optional[int] = None
    ) -> SaldoPontos:
        """Busca ou cria saldo de pontos do cliente"""
        # Verifica cliente
        cliente = await self.cliente_repository.get_by_id(cliente_id)
        if not cliente:
            raise NotFoundException(f"Cliente {cliente_id} não encontrado")

        # Busca programa
        if not programa_id:
            programa = await self.get_programa_ativo()
            programa_id = programa.id

        # Busca saldo existente
        query = select(SaldoPontos).where(
            and_(
                SaldoPontos.cliente_id == cliente_id,
                SaldoPontos.programa_id == programa_id,
            )
        )
        result = await self.session.execute(query)
        saldo = result.scalar_one_or_none()

        # Cria se não existir
        if not saldo:
            saldo = SaldoPontos(
                cliente_id=cliente_id,
                programa_id=programa_id,
                pontos_disponiveis=0,
                pontos_acumulados_total=0,
                pontos_resgatados_total=0,
            )
            self.session.add(saldo)
            await self.session.flush()
            await self.session.refresh(saldo)

        return saldo

    async def consultar_saldo(self, cliente_id: int) -> ConsultarSaldoResponse:
        """Consulta saldo de pontos do cliente"""
        saldo = await self.get_ou_criar_saldo(cliente_id)
        programa = await self.get_programa(saldo.programa_id)

        valor_disponivel = saldo.pontos_disponiveis * float(programa.valor_ponto_resgate)

        return ConsultarSaldoResponse(
            cliente_id=cliente_id,
            pontos_disponiveis=saldo.pontos_disponiveis,
            valor_disponivel_resgate=round(valor_disponivel, 2),
            pontos_acumulados_total=saldo.pontos_acumulados_total,
            pontos_resgatados_total=saldo.pontos_resgatados_total,
        )

    # ==================== ACUMULAR PONTOS ====================

    async def acumular_pontos(
        self, data: AcumularPontosRequest
    ) -> MovimentacaoPontosResponse:
        """
        Acumula pontos para um cliente baseado em valor de compra

        Regras:
        - Pontos = valor_compra * programa.pontos_por_real
        - Se programa tem validade, define data_validade
        """
        # Busca saldo
        saldo = await self.get_ou_criar_saldo(data.cliente_id)
        programa = await self.get_programa(saldo.programa_id)

        # Calcula pontos
        pontos = int(data.valor_compra * float(programa.pontos_por_real))

        if pontos <= 0:
            raise ValidationException("Valor de compra insuficiente para gerar pontos")

        # Calcula data de validade
        data_validade = None
        if programa.dias_validade_pontos:
            data_validade = datetime.utcnow() + timedelta(days=programa.dias_validade_pontos)

        # Registra movimentação
        saldo_anterior = saldo.pontos_disponiveis
        saldo.pontos_disponiveis += pontos
        saldo.pontos_acumulados_total += pontos
        saldo.ultima_movimentacao = datetime.utcnow()

        movimentacao = MovimentacaoPontos(
            cliente_id=data.cliente_id,
            programa_id=programa.id,
            tipo=TipoMovimentacaoPontos.ACUMULO,
            pontos=pontos,
            venda_id=data.venda_id,
            descricao=data.descricao or f"Acúmulo por compra de R$ {data.valor_compra:.2f}",
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo.pontos_disponiveis,
            data_validade=data_validade,
        )
        self.session.add(movimentacao)

        await self.session.flush()
        await self.session.refresh(movimentacao)
        await self.session.refresh(saldo)

        return MovimentacaoPontosResponse.model_validate(movimentacao)

    # ==================== RESGATAR PONTOS ====================

    async def resgatar_pontos(
        self, data: ResgatarPontosRequest
    ) -> ResgatarPontosResponse:
        """
        Resgata pontos do cliente para desconto

        Regras:
        - Cliente deve ter saldo suficiente
        - Pontos >= programa.pontos_minimo_resgate
        - Valor desconto = pontos * programa.valor_ponto_resgate
        """
        # Busca saldo
        saldo = await self.get_ou_criar_saldo(data.cliente_id)
        programa = await self.get_programa(saldo.programa_id)

        # Valida pontos mínimos
        if data.pontos < programa.pontos_minimo_resgate:
            raise ValidationException(
                f"Mínimo de {programa.pontos_minimo_resgate} pontos para resgate"
            )

        # Valida saldo
        if saldo.pontos_disponiveis < data.pontos:
            raise ValidationException(
                f"Saldo insuficiente. Disponível: {saldo.pontos_disponiveis} pontos"
            )

        # Calcula desconto
        valor_desconto = data.pontos * float(programa.valor_ponto_resgate)

        # Registra movimentação
        saldo_anterior = saldo.pontos_disponiveis
        saldo.pontos_disponiveis -= data.pontos
        saldo.pontos_resgatados_total += data.pontos
        saldo.ultima_movimentacao = datetime.utcnow()

        movimentacao = MovimentacaoPontos(
            cliente_id=data.cliente_id,
            programa_id=programa.id,
            tipo=TipoMovimentacaoPontos.RESGATE,
            pontos=-data.pontos,  # Negativo para resgate
            venda_id=data.venda_id,
            descricao=data.descricao or f"Resgate de {data.pontos} pontos",
            saldo_anterior=saldo_anterior,
            saldo_posterior=saldo.pontos_disponiveis,
        )
        self.session.add(movimentacao)

        await self.session.flush()
        await self.session.refresh(movimentacao)
        await self.session.refresh(saldo)

        return ResgatarPontosResponse(
            pontos_resgatados=data.pontos,
            valor_desconto=round(valor_desconto, 2),
            saldo_anterior=saldo_anterior,
            saldo_atual=saldo.pontos_disponiveis,
            movimentacao=MovimentacaoPontosResponse.model_validate(movimentacao),
        )

    # ==================== EXTRATO ====================

    async def extrato_pontos(
        self, cliente_id: int, limit: int = 50
    ) -> ExtratoResponse:
        """Retorna extrato de movimentações do cliente"""
        saldo = await self.get_ou_criar_saldo(cliente_id)

        # Busca movimentações
        query = (
            select(MovimentacaoPontos)
            .where(MovimentacaoPontos.cliente_id == cliente_id)
            .order_by(MovimentacaoPontos.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        movimentacoes = list(result.scalars().all())

        # Count total
        count_query = select(func.count(MovimentacaoPontos.id)).where(
            MovimentacaoPontos.cliente_id == cliente_id
        )
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        return ExtratoResponse(
            cliente_id=cliente_id,
            saldo_atual=saldo.pontos_disponiveis,
            movimentacoes=[
                MovimentacaoPontosResponse.model_validate(m) for m in movimentacoes
            ],
            total_movimentacoes=total,
        )
