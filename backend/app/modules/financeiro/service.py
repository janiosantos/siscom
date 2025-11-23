"""
Service Layer para Financeiro
"""
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.financeiro.repository import ContaPagarRepository, ContaReceberRepository
from app.modules.financeiro.models import StatusFinanceiro
from app.modules.financeiro.schemas import (
    ContaPagarCreate,
    ContaPagarUpdate,
    ContaPagarResponse,
    ContaPagarList,
    ContaReceberCreate,
    ContaReceberUpdate,
    ContaReceberResponse,
    ContaReceberList,
    BaixaPagamentoCreate,
    BaixaRecebimentoCreate,
    FluxoCaixaResponse,
    FluxoCaixaPeriodoResponse,
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


class FinanceiroService:
    """Service para regras de negócio de Financeiro"""

    def __init__(self, session: AsyncSession):
        self.conta_pagar_repo = ContaPagarRepository(session)
        self.conta_receber_repo = ContaReceberRepository(session)
        self.session = session

    # ============================================
    # CONTAS A PAGAR
    # ============================================

    async def criar_conta_pagar(self, conta_data: ContaPagarCreate) -> ContaPagarResponse:
        """
        Cria uma nova conta a pagar

        Regras:
        - Data de vencimento não pode ser anterior à emissão
        - Valor original deve ser positivo
        """
        # Validações já são feitas no schema Pydantic
        conta = await self.conta_pagar_repo.create(conta_data)

        # Verifica se já está vencida
        await self._atualizar_status_vencimento_pagar(conta)

        return ContaPagarResponse.model_validate(conta)

    async def get_conta_pagar(self, conta_id: int) -> ContaPagarResponse:
        """Busca conta a pagar por ID"""
        conta = await self.conta_pagar_repo.get_by_id(conta_id)
        if not conta:
            raise NotFoundException(f"Conta a pagar {conta_id} não encontrada")

        # Atualiza status se necessário
        await self._atualizar_status_vencimento_pagar(conta)

        return ContaPagarResponse.model_validate(conta)

    async def list_contas_pagar(
        self,
        page: int = 1,
        page_size: int = 50,
        fornecedor_id: Optional[int] = None,
        status: Optional[str] = None,
        categoria: Optional[str] = None,
    ) -> ContaPagarList:
        """Lista contas a pagar com paginação e filtros"""
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Converte status string para enum se fornecido
        status_enum = None
        if status:
            try:
                status_enum = StatusFinanceiro[status]
            except KeyError:
                raise ValidationException(f"Status '{status}' inválido")

        # Busca contas e total
        contas = await self.conta_pagar_repo.get_all(
            skip, page_size, fornecedor_id, status_enum, categoria
        )
        total = await self.conta_pagar_repo.count(fornecedor_id, status_enum, categoria)

        # Atualiza status de vencimento
        for conta in contas:
            await self._atualizar_status_vencimento_pagar(conta)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return ContaPagarList(
            items=[ContaPagarResponse.model_validate(c) for c in contas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def update_conta_pagar(
        self, conta_id: int, conta_data: ContaPagarUpdate
    ) -> ContaPagarResponse:
        """
        Atualiza uma conta a pagar

        Regras:
        - Não pode atualizar conta já paga ou cancelada
        """
        conta = await self.conta_pagar_repo.get_by_id(conta_id)
        if not conta:
            raise NotFoundException(f"Conta a pagar {conta_id} não encontrada")

        if conta.status in [StatusFinanceiro.PAGA, StatusFinanceiro.CANCELADA]:
            raise BusinessRuleException(
                f"Não é possível atualizar conta com status '{conta.status.value}'"
            )

        conta_atualizada = await self.conta_pagar_repo.update(conta_id, conta_data)

        # Atualiza status se necessário
        await self._atualizar_status_vencimento_pagar(conta_atualizada)

        return ContaPagarResponse.model_validate(conta_atualizada)

    async def baixar_pagamento(
        self, conta_id: int, baixa_data: BaixaPagamentoCreate
    ) -> ContaPagarResponse:
        """
        Registra pagamento de conta a pagar

        Regras:
        - Não pode pagar conta cancelada
        - Valor pago total não pode exceder valor original
        - Atualiza status automaticamente
        """
        conta = await self.conta_pagar_repo.get_by_id(conta_id)
        if not conta:
            raise NotFoundException(f"Conta a pagar {conta_id} não encontrada")

        if conta.status == StatusFinanceiro.CANCELADA:
            raise BusinessRuleException("Não é possível pagar conta cancelada")

        # Valida que valor pago total não excede o original
        total_pago = conta.valor_pago + baixa_data.valor_pago
        if total_pago > conta.valor_original:
            raise ValidationException(
                f"Valor total pago (R$ {total_pago:.2f}) não pode exceder valor original (R$ {conta.valor_original:.2f})"
            )

        # Registra pagamento
        conta_atualizada = await self.conta_pagar_repo.baixar_pagamento(conta_id, baixa_data)

        return ContaPagarResponse.model_validate(conta_atualizada)

    async def cancelar_conta_pagar(self, conta_id: int) -> ContaPagarResponse:
        """
        Cancela uma conta a pagar

        Regras:
        - Não pode cancelar conta já paga
        """
        conta = await self.conta_pagar_repo.get_by_id(conta_id)
        if not conta:
            raise NotFoundException(f"Conta a pagar {conta_id} não encontrada")

        if conta.status == StatusFinanceiro.PAGA:
            raise BusinessRuleException("Não é possível cancelar conta já paga")

        conta_cancelada = await self.conta_pagar_repo.cancelar(conta_id)

        return ContaPagarResponse.model_validate(conta_cancelada)

    async def get_contas_pagar_pendentes(
        self, page: int = 1, page_size: int = 50
    ) -> ContaPagarList:
        """Lista contas a pagar pendentes"""
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        contas = await self.conta_pagar_repo.get_pendentes(skip, page_size)
        total = await self.conta_pagar_repo.count(status=StatusFinanceiro.PENDENTE)

        # Atualiza status de vencimento
        for conta in contas:
            await self._atualizar_status_vencimento_pagar(conta)

        pages = math.ceil(total / page_size) if total > 0 else 1

        return ContaPagarList(
            items=[ContaPagarResponse.model_validate(c) for c in contas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_contas_pagar_vencidas(
        self, page: int = 1, page_size: int = 50
    ) -> ContaPagarList:
        """Lista contas a pagar vencidas (vencimento < hoje e status PENDENTE)"""
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        contas = await self.conta_pagar_repo.get_vencidas(skip, page_size)

        # Atualiza status para ATRASADA
        for conta in contas:
            await self._atualizar_status_vencimento_pagar(conta)

        # Conta novamente após atualizar status
        total_contas = await self.conta_pagar_repo.get_vencidas(0, 10000)
        total = len(total_contas)

        pages = math.ceil(total / page_size) if total > 0 else 1

        return ContaPagarList(
            items=[ContaPagarResponse.model_validate(c) for c in contas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # ============================================
    # CONTAS A RECEBER
    # ============================================

    async def criar_conta_receber(self, conta_data: ContaReceberCreate) -> ContaReceberResponse:
        """
        Cria uma nova conta a receber

        Regras:
        - Data de vencimento não pode ser anterior à emissão
        - Valor original deve ser positivo
        - Pode ser vinculada a uma venda (opcional)
        """
        # Validações já são feitas no schema Pydantic
        conta = await self.conta_receber_repo.create(conta_data)

        # Verifica se já está vencida
        await self._atualizar_status_vencimento_receber(conta)

        return ContaReceberResponse.model_validate(conta)

    async def get_conta_receber(self, conta_id: int) -> ContaReceberResponse:
        """Busca conta a receber por ID"""
        conta = await self.conta_receber_repo.get_by_id(conta_id)
        if not conta:
            raise NotFoundException(f"Conta a receber {conta_id} não encontrada")

        # Atualiza status se necessário
        await self._atualizar_status_vencimento_receber(conta)

        return ContaReceberResponse.model_validate(conta)

    async def list_contas_receber(
        self,
        page: int = 1,
        page_size: int = 50,
        cliente_id: Optional[int] = None,
        status: Optional[str] = None,
        categoria: Optional[str] = None,
    ) -> ContaReceberList:
        """Lista contas a receber com paginação e filtros"""
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Converte status string para enum se fornecido
        status_enum = None
        if status:
            try:
                status_enum = StatusFinanceiro[status]
            except KeyError:
                raise ValidationException(f"Status '{status}' inválido")

        # Busca contas e total
        contas = await self.conta_receber_repo.get_all(
            skip, page_size, cliente_id, status_enum, categoria
        )
        total = await self.conta_receber_repo.count(cliente_id, status_enum, categoria)

        # Atualiza status de vencimento
        for conta in contas:
            await self._atualizar_status_vencimento_receber(conta)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return ContaReceberList(
            items=[ContaReceberResponse.model_validate(c) for c in contas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def update_conta_receber(
        self, conta_id: int, conta_data: ContaReceberUpdate
    ) -> ContaReceberResponse:
        """
        Atualiza uma conta a receber

        Regras:
        - Não pode atualizar conta já recebida ou cancelada
        """
        conta = await self.conta_receber_repo.get_by_id(conta_id)
        if not conta:
            raise NotFoundException(f"Conta a receber {conta_id} não encontrada")

        if conta.status in [StatusFinanceiro.RECEBIDA, StatusFinanceiro.CANCELADA]:
            raise BusinessRuleException(
                f"Não é possível atualizar conta com status '{conta.status.value}'"
            )

        conta_atualizada = await self.conta_receber_repo.update(conta_id, conta_data)

        # Atualiza status se necessário
        await self._atualizar_status_vencimento_receber(conta_atualizada)

        return ContaReceberResponse.model_validate(conta_atualizada)

    async def baixar_recebimento(
        self, conta_id: int, baixa_data: BaixaRecebimentoCreate
    ) -> ContaReceberResponse:
        """
        Registra recebimento de conta a receber

        Regras:
        - Não pode receber conta cancelada
        - Valor recebido total não pode exceder valor original
        - Atualiza status automaticamente
        """
        conta = await self.conta_receber_repo.get_by_id(conta_id)
        if not conta:
            raise NotFoundException(f"Conta a receber {conta_id} não encontrada")

        if conta.status == StatusFinanceiro.CANCELADA:
            raise BusinessRuleException("Não é possível receber conta cancelada")

        # Valida que valor recebido total não excede o original
        total_recebido = conta.valor_recebido + baixa_data.valor_recebido
        if total_recebido > conta.valor_original:
            raise ValidationException(
                f"Valor total recebido (R$ {total_recebido:.2f}) não pode exceder valor original (R$ {conta.valor_original:.2f})"
            )

        # Registra recebimento
        conta_atualizada = await self.conta_receber_repo.baixar_recebimento(conta_id, baixa_data)

        return ContaReceberResponse.model_validate(conta_atualizada)

    async def cancelar_conta_receber(self, conta_id: int) -> ContaReceberResponse:
        """
        Cancela uma conta a receber

        Regras:
        - Não pode cancelar conta já recebida
        """
        conta = await self.conta_receber_repo.get_by_id(conta_id)
        if not conta:
            raise NotFoundException(f"Conta a receber {conta_id} não encontrada")

        if conta.status == StatusFinanceiro.RECEBIDA:
            raise BusinessRuleException("Não é possível cancelar conta já recebida")

        conta_cancelada = await self.conta_receber_repo.cancelar(conta_id)

        return ContaReceberResponse.model_validate(conta_cancelada)

    async def get_contas_receber_pendentes(
        self, page: int = 1, page_size: int = 50
    ) -> ContaReceberList:
        """Lista contas a receber pendentes"""
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        contas = await self.conta_receber_repo.get_pendentes(skip, page_size)
        total = await self.conta_receber_repo.count(status=StatusFinanceiro.PENDENTE)

        # Atualiza status de vencimento
        for conta in contas:
            await self._atualizar_status_vencimento_receber(conta)

        pages = math.ceil(total / page_size) if total > 0 else 1

        return ContaReceberList(
            items=[ContaReceberResponse.model_validate(c) for c in contas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_contas_receber_vencidas(
        self, page: int = 1, page_size: int = 50
    ) -> ContaReceberList:
        """Lista contas a receber vencidas (vencimento < hoje e status PENDENTE)"""
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        contas = await self.conta_receber_repo.get_vencidas(skip, page_size)

        # Atualiza status para ATRASADA
        for conta in contas:
            await self._atualizar_status_vencimento_receber(conta)

        # Conta novamente após atualizar status
        total_contas = await self.conta_receber_repo.get_vencidas(0, 10000)
        total = len(total_contas)

        pages = math.ceil(total / page_size) if total > 0 else 1

        return ContaReceberList(
            items=[ContaReceberResponse.model_validate(c) for c in contas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # ============================================
    # FLUXO DE CAIXA
    # ============================================

    async def get_fluxo_caixa(self) -> FluxoCaixaResponse:
        """
        Retorna resumo do fluxo de caixa atual

        Retorna:
        - Total a pagar (contas pendentes)
        - Total a receber (contas pendentes)
        - Saldo projetado (a receber - a pagar)
        - Total pago
        - Total recebido
        - Contas vencidas
        """
        # Busca todas as contas pendentes
        contas_pagar_pendentes = await self.conta_pagar_repo.get_all(
            skip=0, limit=10000, status=StatusFinanceiro.PENDENTE
        )
        contas_receber_pendentes = await self.conta_receber_repo.get_all(
            skip=0, limit=10000, status=StatusFinanceiro.PENDENTE
        )

        # Busca contas atrasadas
        contas_pagar_atrasadas = await self.conta_pagar_repo.get_vencidas(skip=0, limit=10000)
        contas_receber_atrasadas = await self.conta_receber_repo.get_vencidas(skip=0, limit=10000)

        # Calcula totais
        total_a_pagar = sum(
            c.valor_original - c.valor_pago
            for c in contas_pagar_pendentes
        )
        total_a_receber = sum(
            c.valor_original - c.valor_recebido
            for c in contas_receber_pendentes
        )

        # Busca contas pagas e recebidas
        contas_pagas = await self.conta_pagar_repo.get_all(
            skip=0, limit=10000, status=StatusFinanceiro.PAGA
        )
        contas_recebidas = await self.conta_receber_repo.get_all(
            skip=0, limit=10000, status=StatusFinanceiro.RECEBIDA
        )

        total_pago = sum(c.valor_pago for c in contas_pagas)
        total_recebido = sum(c.valor_recebido for c in contas_recebidas)

        # Calcula valores vencidos
        valor_vencido_pagar = sum(
            c.valor_original - c.valor_pago
            for c in contas_pagar_atrasadas
        )
        valor_vencido_receber = sum(
            c.valor_original - c.valor_recebido
            for c in contas_receber_atrasadas
        )

        return FluxoCaixaResponse(
            total_a_pagar=total_a_pagar,
            total_a_receber=total_a_receber,
            saldo_projetado=total_a_receber - total_a_pagar,
            total_pago=total_pago,
            total_recebido=total_recebido,
            contas_vencidas_pagar=len(contas_pagar_atrasadas),
            contas_vencidas_receber=len(contas_receber_atrasadas),
            valor_vencido_pagar=valor_vencido_pagar,
            valor_vencido_receber=valor_vencido_receber,
        )

    async def get_fluxo_periodo(
        self, data_inicio: date, data_fim: date
    ) -> FluxoCaixaPeriodoResponse:
        """
        Retorna fluxo de caixa por período

        Args:
            data_inicio: Data de início do período
            data_fim: Data de fim do período

        Retorna:
            Fluxo de caixa detalhado do período
        """
        # Valida período
        if data_fim < data_inicio:
            raise ValidationException("Data fim não pode ser anterior à data início")

        # Busca contas do período
        contas_pagar = await self.conta_pagar_repo.get_por_periodo(data_inicio, data_fim)
        contas_receber = await self.conta_receber_repo.get_por_periodo(data_inicio, data_fim)

        # Calcula totais
        total_a_pagar, total_pago = await self.conta_pagar_repo.calcular_totais_periodo(
            data_inicio, data_fim
        )
        total_a_receber, total_recebido = await self.conta_receber_repo.calcular_totais_periodo(
            data_inicio, data_fim
        )

        saldo_periodo = total_recebido - total_pago

        return FluxoCaixaPeriodoResponse(
            data_inicio=data_inicio,
            data_fim=data_fim,
            total_a_pagar=total_a_pagar,
            total_a_receber=total_a_receber,
            total_pago=total_pago,
            total_recebido=total_recebido,
            saldo_periodo=saldo_periodo,
            contas_pagar=[ContaPagarResponse.model_validate(c) for c in contas_pagar],
            contas_receber=[ContaReceberResponse.model_validate(c) for c in contas_receber],
        )

    # ============================================
    # MÉTODOS AUXILIARES PRIVADOS
    # ============================================

    async def _atualizar_status_vencimento_pagar(self, conta) -> None:
        """Atualiza status da conta a pagar se estiver vencida"""
        hoje = date.today()

        if (
            conta.status == StatusFinanceiro.PENDENTE
            and conta.data_vencimento < hoje
        ):
            conta.status = StatusFinanceiro.ATRASADA
            await self.session.flush()

    async def _atualizar_status_vencimento_receber(self, conta) -> None:
        """Atualiza status da conta a receber se estiver vencida"""
        hoje = date.today()

        if (
            conta.status == StatusFinanceiro.PENDENTE
            and conta.data_vencimento < hoje
        ):
            conta.status = StatusFinanceiro.ATRASADA
            await self.session.flush()
