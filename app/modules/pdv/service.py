"""
Service Layer para PDV
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pdv.repository import CaixaRepository
from app.modules.pdv.models import StatusCaixa, TipoMovimentacaoCaixa
from app.modules.pdv.schemas import (
    AbrirCaixaCreate,
    FecharCaixaCreate,
    CaixaResponse,
    MovimentacaoCaixaCreate,
    MovimentacaoCaixaResponse,
    MovimentacoesCaixaList,
    VendaPDVCreate,
    SangriaCreate,
    SuprimentoCreate,
    SaldoCaixaResponse,
)
from app.modules.vendas.service import VendasService
from app.modules.vendas.schemas import VendaCreate, VendaResponse
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


class PDVService:
    """Service para regras de negócio de PDV"""

    def __init__(self, session: AsyncSession):
        self.repository = CaixaRepository(session)
        self.vendas_service = VendasService(session)
        self.session = session

    async def abrir_caixa(self, caixa_data: AbrirCaixaCreate) -> CaixaResponse:
        """
        Abre um novo caixa

        Regras:
        - Não pode haver outro caixa aberto para o mesmo operador
        - Valor de abertura não pode ser negativo

        Args:
            caixa_data: Dados do caixa

        Returns:
            CaixaResponse com o caixa criado

        Raises:
            BusinessRuleException: Se já há caixa aberto para o operador
        """
        # Verifica se já existe caixa aberto para o operador
        caixa_aberto = await self.repository.get_caixa_aberto(caixa_data.operador_id)
        if caixa_aberto:
            raise BusinessRuleException(
                f"Operador {caixa_data.operador_id} já possui um caixa aberto (ID: {caixa_aberto.id})"
            )

        # Abre o caixa
        caixa = await self.repository.abrir_caixa(caixa_data)

        await self.session.flush()

        return CaixaResponse.model_validate(caixa)

    async def fechar_caixa(
        self, operador_id: int, fechamento_data: FecharCaixaCreate
    ) -> CaixaResponse:
        """
        Fecha o caixa aberto do operador

        Regras:
        - Deve existir um caixa aberto para o operador
        - Calcula saldo esperado e compara com valor informado
        - Altera status para FECHADO

        Args:
            operador_id: ID do operador
            fechamento_data: Dados de fechamento

        Returns:
            CaixaResponse com o caixa fechado

        Raises:
            NotFoundException: Se não há caixa aberto para o operador
        """
        # Busca caixa aberto
        caixa = await self.repository.get_caixa_aberto(operador_id)
        if not caixa:
            raise NotFoundException(
                f"Não há caixa aberto para o operador {operador_id}"
            )

        # Calcula saldo esperado
        saldo = await self.calcular_saldo_caixa(caixa.id)

        # Fecha o caixa
        caixa_fechado = await self.repository.fechar_caixa(
            caixa.id, fechamento_data.valor_fechamento
        )

        await self.session.flush()

        return CaixaResponse.model_validate(caixa_fechado)

    async def get_caixa_atual(self, operador_id: int) -> CaixaResponse:
        """
        Retorna o caixa aberto do operador

        Args:
            operador_id: ID do operador

        Returns:
            CaixaResponse com o caixa aberto

        Raises:
            NotFoundException: Se não há caixa aberto para o operador
        """
        caixa = await self.repository.get_caixa_aberto(operador_id)
        if not caixa:
            raise NotFoundException(
                f"Não há caixa aberto para o operador {operador_id}"
            )

        return CaixaResponse.model_validate(caixa)

    async def registrar_venda_pdv(
        self, operador_id: int, venda_data: VendaPDVCreate
    ) -> VendaResponse:
        """
        Registra uma venda no PDV

        Regras:
        - Deve existir um caixa aberto para o operador
        - Cria a venda através do VendasService
        - Registra movimentação de entrada no caixa

        Args:
            operador_id: ID do operador
            venda_data: Dados da venda

        Returns:
            VendaResponse com a venda criada

        Raises:
            NotFoundException: Se não há caixa aberto para o operador
        """
        # Busca caixa aberto
        caixa = await self.repository.get_caixa_aberto(operador_id)
        if not caixa:
            raise BusinessRuleException(
                f"Não há caixa aberto para o operador {operador_id}. Abra o caixa antes de realizar vendas."
            )

        # Cria a venda através do VendasService
        venda_create = VendaCreate(
            cliente_id=venda_data.cliente_id,
            vendedor_id=operador_id,
            forma_pagamento=venda_data.forma_pagamento,
            desconto=venda_data.desconto,
            observacoes=venda_data.observacoes,
            itens=venda_data.itens,
        )

        venda = await self.vendas_service.criar_venda(venda_create)

        # Registra movimentação de entrada no caixa
        await self.repository.registrar_movimentacao(
            caixa_id=caixa.id,
            tipo=TipoMovimentacaoCaixa.ENTRADA,
            valor=venda.valor_total,
            descricao=f"Venda #{venda.id} - {venda.forma_pagamento}",
            venda_id=venda.id,
        )

        await self.session.flush()

        return venda

    async def registrar_sangria(
        self, operador_id: int, sangria_data: SangriaCreate
    ) -> MovimentacaoCaixaResponse:
        """
        Registra uma sangria no caixa

        Regras:
        - Deve existir um caixa aberto para o operador
        - Registra movimentação de sangria
        - Descrição é obrigatória

        Args:
            operador_id: ID do operador
            sangria_data: Dados da sangria

        Returns:
            MovimentacaoCaixaResponse com a movimentação criada

        Raises:
            NotFoundException: Se não há caixa aberto para o operador
        """
        # Busca caixa aberto
        caixa = await self.repository.get_caixa_aberto(operador_id)
        if not caixa:
            raise BusinessRuleException(
                f"Não há caixa aberto para o operador {operador_id}"
            )

        # Registra sangria
        movimentacao = await self.repository.registrar_movimentacao(
            caixa_id=caixa.id,
            tipo=TipoMovimentacaoCaixa.SANGRIA,
            valor=sangria_data.valor,
            descricao=sangria_data.descricao,
        )

        await self.session.flush()

        return MovimentacaoCaixaResponse.model_validate(movimentacao)

    async def registrar_suprimento(
        self, operador_id: int, suprimento_data: SuprimentoCreate
    ) -> MovimentacaoCaixaResponse:
        """
        Registra um suprimento no caixa

        Regras:
        - Deve existir um caixa aberto para o operador
        - Registra movimentação de suprimento
        - Descrição é obrigatória

        Args:
            operador_id: ID do operador
            suprimento_data: Dados do suprimento

        Returns:
            MovimentacaoCaixaResponse com a movimentação criada

        Raises:
            NotFoundException: Se não há caixa aberto para o operador
        """
        # Busca caixa aberto
        caixa = await self.repository.get_caixa_aberto(operador_id)
        if not caixa:
            raise BusinessRuleException(
                f"Não há caixa aberto para o operador {operador_id}"
            )

        # Registra suprimento
        movimentacao = await self.repository.registrar_movimentacao(
            caixa_id=caixa.id,
            tipo=TipoMovimentacaoCaixa.SUPRIMENTO,
            valor=suprimento_data.valor,
            descricao=suprimento_data.descricao,
        )

        await self.session.flush()

        return MovimentacaoCaixaResponse.model_validate(movimentacao)

    async def get_movimentacoes_caixa(
        self, caixa_id: int
    ) -> MovimentacoesCaixaList:
        """
        Retorna todas as movimentações de um caixa

        Args:
            caixa_id: ID do caixa

        Returns:
            MovimentacoesCaixaList com as movimentações

        Raises:
            NotFoundException: Se caixa não existe
        """
        # Verifica se caixa existe
        caixa = await self.repository.get_by_id(caixa_id)
        if not caixa:
            raise NotFoundException(f"Caixa {caixa_id} não encontrado")

        # Busca movimentações
        movimentacoes = await self.repository.get_movimentacoes_caixa(caixa_id)

        return MovimentacoesCaixaList(
            items=[
                MovimentacaoCaixaResponse.model_validate(m) for m in movimentacoes
            ],
            total=len(movimentacoes),
        )

    async def calcular_saldo_caixa(self, caixa_id: int) -> SaldoCaixaResponse:
        """
        Calcula o saldo atual do caixa

        Args:
            caixa_id: ID do caixa

        Returns:
            SaldoCaixaResponse com os totais e saldo

        Raises:
            NotFoundException: Se caixa não existe
        """
        # Busca caixa
        caixa = await self.repository.get_by_id(caixa_id)
        if not caixa:
            raise NotFoundException(f"Caixa {caixa_id} não encontrado")

        # Calcula totais por tipo
        totais = await self.repository.calcular_saldo_caixa(caixa_id)

        # Calcula saldo esperado
        # Saldo = Valor Abertura + Entradas + Suprimentos - Saídas - Sangrias
        saldo_esperado = (
            float(caixa.valor_abertura)
            + totais["entradas"]
            + totais["suprimentos"]
            - totais["saidas"]
            - totais["sangrias"]
        )

        # Saldo atual é o mesmo que o esperado se caixa está aberto
        # Se está fechado, usa o valor de fechamento
        saldo_atual = (
            float(caixa.valor_fechamento)
            if caixa.status == StatusCaixa.FECHADO and caixa.valor_fechamento
            else saldo_esperado
        )

        return SaldoCaixaResponse(
            caixa_id=caixa.id,
            operador_id=caixa.operador_id,
            data_abertura=caixa.data_abertura,
            valor_abertura=float(caixa.valor_abertura),
            total_entradas=totais["entradas"],
            total_saidas=totais["saidas"],
            total_sangrias=totais["sangrias"],
            total_suprimentos=totais["suprimentos"],
            saldo_atual=round(saldo_atual, 2),
            saldo_esperado=round(saldo_esperado, 2),
            status=caixa.status.value,
        )

    async def get_caixa_by_id(self, caixa_id: int) -> CaixaResponse:
        """
        Busca caixa por ID

        Args:
            caixa_id: ID do caixa

        Returns:
            CaixaResponse com o caixa

        Raises:
            NotFoundException: Se caixa não existe
        """
        caixa = await self.repository.get_by_id(caixa_id)
        if not caixa:
            raise NotFoundException(f"Caixa {caixa_id} não encontrado")

        return CaixaResponse.model_validate(caixa)
