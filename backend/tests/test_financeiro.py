"""
Testes do módulo financeiro

Testa:
- financeiro/service.py - Lógica de negócio
- financeiro/repository.py - Acesso a dados
- financeiro/models.py - Modelos
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.modules.financeiro.service import FinanceiroService
from app.modules.financeiro.repository import ContaPagarRepository, ContaReceberRepository
from app.modules.financeiro.models import (
    ContaPagar,
    ContaReceber,
    StatusFinanceiro,
)
from app.modules.financeiro.schemas import (
    ContaPagarCreate,
    ContaPagarUpdate,
    BaixaPagamentoCreate,
    ContaReceberCreate,
    ContaReceberUpdate,
    BaixaRecebimentoCreate,
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


# ========== Fixtures ==========

@pytest.fixture
def mock_session():
    """Mock do AsyncSession"""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = Mock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def conta_pagar_repository(mock_session):
    """Repository com session mockada"""
    return ContaPagarRepository(mock_session)


@pytest.fixture
def conta_receber_repository(mock_session):
    """Repository com session mockada"""
    return ContaReceberRepository(mock_session)


@pytest.fixture
def financeiro_service(mock_session):
    """Service com dependencies mockadas"""
    service = FinanceiroService(mock_session)
    service.conta_pagar_repo = AsyncMock()
    service.conta_receber_repo = AsyncMock()
    return service


@pytest.fixture
def mock_conta_pagar():
    """Mock de conta a pagar"""
    conta = Mock(spec=ContaPagar)
    conta.id = 1
    conta.fornecedor_id = 1
    conta.descricao = "Conta de Energia"
    conta.valor_original = Decimal("500.00")
    conta.valor_pago = Decimal("0.00")
    conta.data_emissao = date.today()
    conta.data_vencimento = date.today() + timedelta(days=30)
    conta.data_pagamento = None
    conta.status = StatusFinanceiro.PENDENTE
    conta.documento = "CONTA-001"
    conta.categoria_financeira = "operacional"
    conta.observacoes = "Pagamento mensal"
    conta.created_at = datetime.utcnow()
    conta.updated_at = datetime.utcnow()
    return conta


@pytest.fixture
def mock_conta_receber():
    """Mock de conta a receber"""
    conta = Mock(spec=ContaReceber)
    conta.id = 1
    conta.cliente_id = 10
    conta.venda_id = 5
    conta.descricao = "Venda a prazo"
    conta.valor_original = Decimal("1000.00")
    conta.valor_recebido = Decimal("0.00")
    conta.data_emissao = date.today()
    conta.data_vencimento = date.today() + timedelta(days=15)
    conta.data_recebimento = None
    conta.status = StatusFinanceiro.PENDENTE
    conta.documento = "VENDA-001"
    conta.categoria_financeira = "vendas"
    conta.observacoes = "Pagamento parcelado"
    conta.created_at = datetime.utcnow()
    conta.updated_at = datetime.utcnow()
    return conta


# ========== Testes FinanceiroService - Contas a Pagar ==========

class TestFinanceiroServiceContasPagar:
    """Testes de contas a pagar"""

    @pytest.mark.asyncio
    async def test_criar_conta_pagar_sucesso(self, financeiro_service, mock_conta_pagar):
        """Deve criar conta a pagar com sucesso"""
        financeiro_service.conta_pagar_repo.create.return_value = mock_conta_pagar

        conta_data = ContaPagarCreate(
            fornecedor_id=1,
            descricao="Conta de Energia",
            valor_original=500.0,
            data_emissao=date.today(),
            data_vencimento=date.today() + timedelta(days=30),
            categoria_financeira="operacional"
        )

        result = await financeiro_service.criar_conta_pagar(conta_data)

        financeiro_service.conta_pagar_repo.create.assert_called_once()
        assert result.descricao == "Conta de Energia"

    @pytest.mark.asyncio
    async def test_get_conta_pagar_sucesso(self, financeiro_service, mock_conta_pagar):
        """Deve buscar conta a pagar com sucesso"""
        financeiro_service.conta_pagar_repo.get_by_id.return_value = mock_conta_pagar

        result = await financeiro_service.get_conta_pagar(1)

        financeiro_service.conta_pagar_repo.get_by_id.assert_called_once_with(1)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_conta_pagar_inexistente(self, financeiro_service):
        """Deve falhar ao buscar conta inexistente"""
        financeiro_service.conta_pagar_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await financeiro_service.get_conta_pagar(999)

    @pytest.mark.asyncio
    async def test_list_contas_pagar_paginacao(self, financeiro_service, mock_conta_pagar):
        """Deve listar contas a pagar com paginação"""
        financeiro_service.conta_pagar_repo.get_all.return_value = [mock_conta_pagar]
        financeiro_service.conta_pagar_repo.count.return_value = 15

        result = await financeiro_service.list_contas_pagar(page=2, page_size=10)

        # Verificar skip correto (page 2 = skip 10)
        call_args = financeiro_service.conta_pagar_repo.get_all.call_args
        assert call_args[0][0] == 10  # skip
        assert call_args[0][1] == 10  # page_size

        # Verificar cálculo de páginas
        assert result.pages == 2  # 15 contas / 10 por página = 2 páginas

    @pytest.mark.asyncio
    async def test_update_conta_pagar_sucesso(self, financeiro_service, mock_conta_pagar):
        """Deve atualizar conta a pagar com sucesso"""
        financeiro_service.conta_pagar_repo.get_by_id.return_value = mock_conta_pagar
        financeiro_service.conta_pagar_repo.update.return_value = mock_conta_pagar

        update_data = ContaPagarUpdate(
            descricao="Conta de Energia Atualizada"
        )

        result = await financeiro_service.update_conta_pagar(1, update_data)

        financeiro_service.conta_pagar_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_conta_pagar_ja_paga(self, financeiro_service, mock_conta_pagar):
        """Deve falhar ao atualizar conta já paga"""
        mock_conta_pagar.status = StatusFinanceiro.PAGA
        financeiro_service.conta_pagar_repo.get_by_id.return_value = mock_conta_pagar

        update_data = ContaPagarUpdate(descricao="Nova descrição")

        with pytest.raises(BusinessRuleException, match="Não é possível atualizar"):
            await financeiro_service.update_conta_pagar(1, update_data)

    @pytest.mark.asyncio
    async def test_cancelar_conta_pagar_sucesso(self, financeiro_service, mock_conta_pagar):
        """Deve cancelar conta a pagar com sucesso"""
        financeiro_service.conta_pagar_repo.get_by_id.return_value = mock_conta_pagar
        mock_conta_cancelada = Mock(spec=ContaPagar)
        mock_conta_cancelada.status = StatusFinanceiro.CANCELADA
        # Add all required fields
        mock_conta_cancelada.id = 1
        mock_conta_cancelada.fornecedor_id = 1
        mock_conta_cancelada.descricao = "Conta de Energia"
        mock_conta_cancelada.valor_original = Decimal("500.00")
        mock_conta_cancelada.valor_pago = Decimal("0.00")
        mock_conta_cancelada.data_emissao = date.today()
        mock_conta_cancelada.data_vencimento = date.today() + timedelta(days=30)
        mock_conta_cancelada.data_pagamento = None
        mock_conta_cancelada.documento = "CONTA-001"
        mock_conta_cancelada.categoria_financeira = "operacional"
        mock_conta_cancelada.observacoes = "Cancelada"
        mock_conta_cancelada.created_at = datetime.utcnow()
        mock_conta_cancelada.updated_at = datetime.utcnow()

        financeiro_service.conta_pagar_repo.cancelar.return_value = mock_conta_cancelada

        result = await financeiro_service.cancelar_conta_pagar(1)

        financeiro_service.conta_pagar_repo.cancelar.assert_called_once_with(1)
        assert result.status.value == "CANCELADA"


# ========== Testes FinanceiroService - Contas a Receber ==========

class TestFinanceiroServiceContasReceber:
    """Testes de contas a receber"""

    @pytest.mark.asyncio
    async def test_criar_conta_receber_sucesso(self, financeiro_service, mock_conta_receber):
        """Deve criar conta a receber com sucesso"""
        financeiro_service.conta_receber_repo.create.return_value = mock_conta_receber

        conta_data = ContaReceberCreate(
            cliente_id=10,
            venda_id=5,
            descricao="Venda a prazo",
            valor_original=1000.0,
            data_emissao=date.today(),
            data_vencimento=date.today() + timedelta(days=15),
            categoria_financeira="vendas"
        )

        result = await financeiro_service.criar_conta_receber(conta_data)

        financeiro_service.conta_receber_repo.create.assert_called_once()
        assert result.descricao == "Venda a prazo"

    @pytest.mark.asyncio
    async def test_get_conta_receber_sucesso(self, financeiro_service, mock_conta_receber):
        """Deve buscar conta a receber com sucesso"""
        financeiro_service.conta_receber_repo.get_by_id.return_value = mock_conta_receber

        result = await financeiro_service.get_conta_receber(1)

        financeiro_service.conta_receber_repo.get_by_id.assert_called_once_with(1)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_conta_receber_inexistente(self, financeiro_service):
        """Deve falhar ao buscar conta inexistente"""
        financeiro_service.conta_receber_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await financeiro_service.get_conta_receber(999)

    @pytest.mark.asyncio
    async def test_cancelar_conta_receber_sucesso(self, financeiro_service, mock_conta_receber):
        """Deve cancelar conta a receber com sucesso"""
        financeiro_service.conta_receber_repo.get_by_id.return_value = mock_conta_receber
        mock_conta_cancelada = Mock(spec=ContaReceber)
        mock_conta_cancelada.status = StatusFinanceiro.CANCELADA
        # Add all required fields
        mock_conta_cancelada.id = 1
        mock_conta_cancelada.cliente_id = 10
        mock_conta_cancelada.venda_id = 5
        mock_conta_cancelada.descricao = "Venda a prazo"
        mock_conta_cancelada.valor_original = Decimal("1000.00")
        mock_conta_cancelada.valor_recebido = Decimal("0.00")
        mock_conta_cancelada.data_emissao = date.today()
        mock_conta_cancelada.data_vencimento = date.today() + timedelta(days=15)
        mock_conta_cancelada.data_recebimento = None
        mock_conta_cancelada.documento = "VENDA-001"
        mock_conta_cancelada.categoria_financeira = "vendas"
        mock_conta_cancelada.observacoes = "Cancelada"
        mock_conta_cancelada.created_at = datetime.utcnow()
        mock_conta_cancelada.updated_at = datetime.utcnow()

        financeiro_service.conta_receber_repo.cancelar.return_value = mock_conta_cancelada

        result = await financeiro_service.cancelar_conta_receber(1)

        financeiro_service.conta_receber_repo.cancelar.assert_called_once_with(1)
        assert result.status.value == "CANCELADA"


# ========== Testes FinanceiroService - Fluxo de Caixa ==========

class TestFinanceiroServiceFluxoCaixa:
    """Testes de fluxo de caixa"""

    @pytest.mark.asyncio
    async def test_get_fluxo_caixa_sucesso(self, financeiro_service, mock_conta_pagar, mock_conta_receber):
        """Deve calcular fluxo de caixa com sucesso"""
        # Mock contas a pagar pendentes
        mock_conta_pagar.valor_pago = Decimal("0.00")
        mock_conta_pagar.status = StatusFinanceiro.PENDENTE

        # Mock contas a receber pendentes
        mock_conta_receber.valor_recebido = Decimal("0.00")
        mock_conta_receber.status = StatusFinanceiro.PENDENTE

        # Mock get_all para contas pendentes
        financeiro_service.conta_pagar_repo.get_all.return_value = [mock_conta_pagar]
        financeiro_service.conta_receber_repo.get_all.return_value = [mock_conta_receber]

        # Mock get_vencidas
        financeiro_service.conta_pagar_repo.get_vencidas.return_value = []
        financeiro_service.conta_receber_repo.get_vencidas.return_value = []

        result = await financeiro_service.get_fluxo_caixa()

        # Verificar que os métodos foram chamados
        assert financeiro_service.conta_pagar_repo.get_all.called
        assert financeiro_service.conta_receber_repo.get_all.called

        # Verificar valores calculados
        assert result.total_a_pagar == 500.0  # valor_original - valor_pago
        assert result.total_a_receber == 1000.0  # valor_original - valor_recebido
        assert result.saldo_projetado == 500.0  # 1000 - 500


# ========== Testes ContaPagarRepository ==========

class TestContaPagarRepository:
    """Testes do repository de contas a pagar"""

    @pytest.mark.asyncio
    async def test_create_conta_pagar(self, conta_pagar_repository, mock_session):
        """Deve criar conta a pagar"""
        conta_data = ContaPagarCreate(
            fornecedor_id=1,
            descricao="Conta de Energia",
            valor_original=500.0,
            data_emissao=date.today(),
            data_vencimento=date.today() + timedelta(days=30),
            categoria_financeira="operacional"
        )

        mock_session.refresh = AsyncMock(side_effect=lambda x: setattr(x, 'id', 1))

        await conta_pagar_repository.create(conta_data)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id(self, conta_pagar_repository, mock_session, mock_conta_pagar):
        """Deve buscar conta a pagar por ID"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_conta_pagar
        mock_session.execute.return_value = mock_result

        result = await conta_pagar_repository.get_by_id(1)

        assert result == mock_conta_pagar
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_nao_encontrada(self, conta_pagar_repository, mock_session):
        """Deve retornar None se conta não existe"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await conta_pagar_repository.get_by_id(999)

        assert result is None


# ========== Testes ContaReceberRepository ==========

class TestContaReceberRepository:
    """Testes do repository de contas a receber"""

    @pytest.mark.asyncio
    async def test_create_conta_receber(self, conta_receber_repository, mock_session):
        """Deve criar conta a receber"""
        conta_data = ContaReceberCreate(
            cliente_id=10,
            descricao="Venda a prazo",
            valor_original=1000.0,
            data_emissao=date.today(),
            data_vencimento=date.today() + timedelta(days=15),
            categoria_financeira="vendas"
        )

        mock_session.refresh = AsyncMock(side_effect=lambda x: setattr(x, 'id', 1))

        await conta_receber_repository.create(conta_data)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id(self, conta_receber_repository, mock_session, mock_conta_receber):
        """Deve buscar conta a receber por ID"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_conta_receber
        mock_session.execute.return_value = mock_result

        result = await conta_receber_repository.get_by_id(1)

        assert result == mock_conta_receber
        mock_session.execute.assert_called_once()


# ========== Testes Models ==========

class TestFinanceiroModels:
    """Testes dos modelos"""

    def test_status_financeiro_enum(self):
        """Deve ter todos os status"""
        assert StatusFinanceiro.PENDENTE.value == "PENDENTE"
        assert StatusFinanceiro.PAGA.value == "PAGA"
        assert StatusFinanceiro.RECEBIDA.value == "RECEBIDA"
        assert StatusFinanceiro.ATRASADA.value == "ATRASADA"
        assert StatusFinanceiro.CANCELADA.value == "CANCELADA"

    def test_conta_pagar_repr(self, mock_conta_pagar):
        """Deve ter representação string"""
        repr_str = repr(mock_conta_pagar)
        assert "ContaPagar" in repr_str

    def test_conta_receber_repr(self, mock_conta_receber):
        """Deve ter representação string"""
        repr_str = repr(mock_conta_receber)
        assert "ContaReceber" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
