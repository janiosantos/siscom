"""
Testes da integração Sicoob
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.integrations.sicoob import (
    SicoobClient,
    SicoobEnvironment
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sicoob_client():
    """Client Sicoob para testes"""
    return SicoobClient(
        client_id="TEST_CLIENT_ID",
        client_secret="TEST_CLIENT_SECRET",
        environment=SicoobEnvironment.SANDBOX
    )


@pytest.fixture
def mock_pix_charge_response():
    """Response simulado de cobrança PIX"""
    return {
        "txid": "abc123def456ghi789012345678901",
        "revisao": 0,
        "loc": {
            "id": 1,
            "location": "pix.example.com/qr/v2/abc123",
            "tipoCob": "cob"
        },
        "location": "pix.example.com/qr/v2/abc123",
        "status": "ATIVA",
        "calendario": {
            "criacao": "2025-11-20T10:00:00Z",
            "expiracao": 1800
        },
        "valor": {
            "original": "100.00"
        },
        "chave": "test@example.com",
        "pixCopiaECola": "00020126580014br.gov.bcb.pix0136...",
        "devedor": {
            "cpf": "12345678909",
            "nome": "João Silva"
        }
    }


@pytest.fixture
def mock_boleto_response():
    """Response simulado de boleto"""
    return {
        "nossoNumero": "12345678901",
        "linhaDigitavel": "75691234500000100001234567890100012345678901",
        "codigoBarras": "75691234500000100001234567890100012345678901",
        "situacao": "EMITIDO",
        "valor": 100.00,
        "dataVencimento": "2025-12-31"
    }


# ============================================================================
# TESTES DO CLIENT
# ============================================================================

def test_sicoob_client_initialization(sicoob_client):
    """Teste de inicialização do client"""
    assert sicoob_client.client_id == "TEST_CLIENT_ID"
    assert sicoob_client.client_secret == "TEST_CLIENT_SECRET"
    assert sicoob_client.environment == SicoobEnvironment.SANDBOX
    assert "sandbox" in sicoob_client.base_url.lower()


def test_sicoob_client_urls():
    """Teste de URLs sandbox vs produção"""
    # Sandbox
    sandbox_client = SicoobClient(environment=SicoobEnvironment.SANDBOX)
    assert "sandbox" in sandbox_client.base_url.lower()

    # Produção
    prod_client = SicoobClient(environment=SicoobEnvironment.PRODUCTION)
    assert "sandbox" not in prod_client.base_url.lower()


# ============================================================================
# TESTES DE FORMATAÇÃO DE STATUS
# ============================================================================

def test_format_pix_status(sicoob_client):
    """Teste de formatação de status PIX"""
    assert sicoob_client.format_pix_status("ATIVA") == "Ativa (Aguardando Pagamento)"
    assert sicoob_client.format_pix_status("CONCLUIDA") == "Concluída (Paga)"
    assert sicoob_client.format_pix_status("REMOVIDA_PELO_USUARIO_RECEBEDOR") == "Removida pelo Recebedor"


def test_is_pix_paid(sicoob_client, mock_pix_charge_response):
    """Teste de verificação de pagamento PIX"""
    # Não pago
    assert sicoob_client.is_pix_paid(mock_pix_charge_response) is False

    # Pago
    paid_response = mock_pix_charge_response.copy()
    paid_response["status"] = "CONCLUIDA"
    assert sicoob_client.is_pix_paid(paid_response) is True


def test_format_boleto_status(sicoob_client):
    """Teste de formatação de status boleto"""
    assert sicoob_client.format_boleto_status("EMITIDO") == "Emitido"
    assert sicoob_client.format_boleto_status("PAGO") == "Pago"
    assert sicoob_client.format_boleto_status("CANCELADO") == "Cancelado"
    assert sicoob_client.format_boleto_status("VENCIDO") == "Vencido"


# ============================================================================
# TESTES DE OAUTH2
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_get_access_token(mock_client, sicoob_client):
    """Teste de obtenção de access token"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "access_token": "test_token_12345",
        "token_type": "Bearer",
        "expires_in": 3600
    }
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    token = await sicoob_client._get_access_token()

    assert token == "test_token_12345"
    assert sicoob_client._access_token == "test_token_12345"


# ============================================================================
# TESTES DE COBRANÇA PIX (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_create_pix_charge_success(mock_client, sicoob_client, mock_pix_charge_response):
    """Teste de criação de cobrança PIX"""
    # Mock OAuth2
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    # Mock PIX charge
    mock_charge_response = Mock()
    mock_charge_response.json.return_value = mock_pix_charge_response
    mock_charge_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(return_value=mock_auth_response)
    mock_instance.put = AsyncMock(return_value=mock_charge_response)
    mock_instance.request = AsyncMock(return_value=mock_charge_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    result = await sicoob_client.create_pix_charge(
        amount=100.00,
        payer_cpf="12345678909",
        payer_name="João Silva",
        expiration_seconds=1800
    )

    assert result is not None
    assert result["txid"] is not None
    assert result["status"] == "ATIVA"
    assert "pixCopiaECola" in result


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_create_pix_static_qr(mock_client, sicoob_client):
    """Teste de criação de QR Code estático"""
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    mock_qr_response = Mock()
    mock_qr_response.json.return_value = {
        "pixCopiaECola": "00020126580014br.gov.bcb.pix...",
        "qrcode": "iVBORw0KGgo..."
    }
    mock_qr_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(side_effect=[mock_auth_response, mock_qr_response])
    mock_instance.request = AsyncMock(return_value=mock_qr_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    result = await sicoob_client.create_pix_static_qr(
        amount=50.00,
        description="Pagamento teste"
    )

    assert result is not None
    assert "pixCopiaECola" in result


# ============================================================================
# TESTES DE CONSULTA PIX (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_query_pix_charge(mock_client, sicoob_client, mock_pix_charge_response):
    """Teste de consulta de cobrança PIX"""
    mock_response = Mock()
    mock_response.json.return_value = mock_pix_charge_response
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_instance.request = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    # Set token
    sicoob_client._access_token = "test_token"

    mock_client.return_value = mock_instance

    result = await sicoob_client.query_pix_charge("abc123def456ghi789012345678901")

    assert result["txid"] == "abc123def456ghi789012345678901"
    assert result["status"] == "ATIVA"


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_query_pix_payment(mock_client, sicoob_client):
    """Teste de consulta de pagamento PIX"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "endToEndId": "E12345678202511201000123456789",
        "txid": "abc123",
        "valor": "100.00",
        "horario": "2025-11-20T10:00:00Z",
        "pagador": {
            "cpf": "12345678909",
            "nome": "Maria Silva"
        }
    }
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_instance.request = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    sicoob_client._access_token = "test_token"

    mock_client.return_value = mock_instance

    result = await sicoob_client.query_pix_payment("E12345678202511201000123456789")

    assert result["txid"] == "abc123"
    assert "pagador" in result


# ============================================================================
# TESTES DE DEVOLUÇÃO PIX (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_refund_pix_payment(mock_client, sicoob_client):
    """Teste de devolução PIX"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "refund123",
        "rtrId": "D12345678202511201000123456789",
        "valor": "50.00",
        "status": "EM_PROCESSAMENTO"
    }
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.put = AsyncMock(return_value=mock_response)
    mock_instance.request = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    sicoob_client._access_token = "test_token"

    mock_client.return_value = mock_instance

    result = await sicoob_client.refund_pix_payment(
        e2e_id="E12345678202511201000123456789",
        refund_id="refund123",
        amount=50.00,
        reason="Devolução solicitada pelo cliente"
    )

    assert result["status"] == "EM_PROCESSAMENTO"


# ============================================================================
# TESTES DE BOLETO (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_create_boleto(mock_client, sicoob_client, mock_boleto_response):
    """Teste de criação de boleto"""
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    mock_boleto_create = Mock()
    mock_boleto_create.json.return_value = mock_boleto_response
    mock_boleto_create.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(side_effect=[mock_auth_response, mock_boleto_create])
    mock_instance.request = AsyncMock(return_value=mock_boleto_create)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    due_date = datetime.now() + timedelta(days=30)

    result = await sicoob_client.create_boleto(
        amount=100.00,
        due_date=due_date,
        payer_name="João Silva",
        payer_document="12345678909",
        payer_address={
            "logradouro": "Rua Teste",
            "numero": "123",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "uf": "SP",
            "cep": "01234567"
        },
        fine_percentage=2.0,
        interest_percentage=1.0
    )

    assert result["nossoNumero"] == "12345678901"
    assert result["linhaDigitavel"] is not None
    assert result["situacao"] == "EMITIDO"


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_query_boleto(mock_client, sicoob_client, mock_boleto_response):
    """Teste de consulta de boleto"""
    mock_response = Mock()
    mock_response.json.return_value = mock_boleto_response
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_instance.request = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    sicoob_client._access_token = "test_token"

    mock_client.return_value = mock_instance

    result = await sicoob_client.query_boleto("12345678901")

    assert result["nossoNumero"] == "12345678901"
    assert result["situacao"] == "EMITIDO"


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_cancel_boleto(mock_client, sicoob_client):
    """Teste de cancelamento de boleto"""
    mock_response = Mock()
    mock_response.json.return_value = {}
    mock_response.status_code = 204
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.delete = AsyncMock(return_value=mock_response)
    mock_instance.request = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    sicoob_client._access_token = "test_token"

    mock_client.return_value = mock_instance

    result = await sicoob_client.cancel_boleto("12345678901")

    # Status 204 retorna dict vazio
    assert isinstance(result, dict)


# ============================================================================
# TESTES DE INTEGRAÇÃO COMPLETO
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_full_pix_flow(mock_client, sicoob_client, mock_pix_charge_response):
    """Teste de fluxo completo PIX: criar, consultar, receber, devolver"""
    # Setup mocks
    mock_auth = Mock()
    mock_auth.json.return_value = {"access_token": "test_token"}
    mock_auth.raise_for_status = Mock()

    mock_charge = Mock()
    mock_charge.json.return_value = mock_pix_charge_response
    mock_charge.raise_for_status = Mock()

    mock_query = Mock()
    paid_response = mock_pix_charge_response.copy()
    paid_response["status"] = "CONCLUIDA"
    mock_query.json.return_value = paid_response
    mock_query.raise_for_status = Mock()

    mock_refund = Mock()
    mock_refund.json.return_value = {"status": "EM_PROCESSAMENTO"}
    mock_refund.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(return_value=mock_auth)
    mock_instance.put = AsyncMock(side_effect=[mock_charge, mock_refund])
    mock_instance.get = AsyncMock(return_value=mock_query)
    mock_instance.request = AsyncMock(side_effect=[mock_charge, mock_query, mock_refund])
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    # 1. Criar cobrança
    charge = await sicoob_client.create_pix_charge(
        amount=100.00,
        payer_cpf="12345678909"
    )
    txid = charge["txid"]
    assert txid is not None

    # 2. Consultar cobrança (paga)
    query = await sicoob_client.query_pix_charge(txid)
    assert query["status"] == "CONCLUIDA"

    # 3. Devolver
    refund = await sicoob_client.refund_pix_payment(
        e2e_id="E12345678",
        refund_id="ref123",
        amount=50.00
    )
    assert refund["status"] == "EM_PROCESSAMENTO"
