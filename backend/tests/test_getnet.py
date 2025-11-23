"""
Testes da integração GetNet
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.integrations.getnet import (
    GetNetClient,
    GetNetEnvironment,
    GetNetCardBrand,
    GetNetPaymentType
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def getnet_client():
    """Client GetNet para testes"""
    return GetNetClient(
        seller_id="TEST_SELLER_ID",
        client_id="TEST_CLIENT_ID",
        client_secret="TEST_CLIENT_SECRET",
        environment=GetNetEnvironment.SANDBOX
    )


@pytest.fixture
def mock_credit_card_response():
    """Response simulado de pagamento com cartão de crédito"""
    return {
        "payment_id": "abc123-def456-ghi789",
        "seller_id": "TEST_SELLER_ID",
        "amount": 10000,
        "currency": "BRL",
        "order": {
            "order_id": "ORD-20251120-001",
            "sales_tax": 0,
            "product_type": "service"
        },
        "status": "AUTHORIZED",
        "credit": {
            "delayed": False,
            "transaction_type": "FULL",
            "number_installments": 1,
            "card": {
                "brand": "Visa",
                "first_digits": "411111",
                "last_digits": "1111"
            }
        },
        "authorization_code": "123456",
        "authorized_at": "2025-11-20T10:00:00Z"
    }


@pytest.fixture
def mock_pix_response():
    """Response simulado de pagamento PIX"""
    return {
        "payment_id": "pix-abc123",
        "seller_id": "TEST_SELLER_ID",
        "amount": 5000,
        "currency": "BRL",
        "order": {
            "order_id": "ORD-20251120-002"
        },
        "status": "PENDING",
        "qr_code": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "emv": "00020126580014br.gov.bcb.pix0136...",
        "pix": {
            "expiration_time": 30
        }
    }


# ============================================================================
# TESTES DO CLIENT
# ============================================================================

def test_getnet_client_initialization(getnet_client):
    """Teste de inicialização do client"""
    assert getnet_client.seller_id == "TEST_SELLER_ID"
    assert getnet_client.client_id == "TEST_CLIENT_ID"
    assert getnet_client.client_secret == "TEST_CLIENT_SECRET"
    assert getnet_client.environment == GetNetEnvironment.SANDBOX
    assert "sandbox" in getnet_client.base_url.lower()


def test_getnet_client_urls():
    """Teste de URLs sandbox vs produção"""
    # Sandbox
    sandbox_client = GetNetClient(environment=GetNetEnvironment.SANDBOX)
    assert "sandbox" in sandbox_client.base_url.lower()
    assert "sandbox" in sandbox_client.auth_url.lower()

    # Produção
    prod_client = GetNetClient(environment=GetNetEnvironment.PRODUCTION)
    assert "sandbox" not in prod_client.base_url.lower()
    assert "sandbox" not in prod_client.auth_url.lower()


# ============================================================================
# TESTES DE DETECÇÃO DE BANDEIRA
# ============================================================================

def test_detect_card_brand_visa(getnet_client):
    """Teste de detecção de bandeira Visa"""
    brand = getnet_client._detect_card_brand("4111111111111111")
    assert brand == GetNetCardBrand.VISA.value


def test_detect_card_brand_mastercard(getnet_client):
    """Teste de detecção de bandeira Mastercard"""
    brand = getnet_client._detect_card_brand("5200000000001096")
    assert brand == GetNetCardBrand.MASTERCARD.value


def test_detect_card_brand_amex(getnet_client):
    """Teste de detecção de bandeira Amex"""
    brand = getnet_client._detect_card_brand("371449635398431")
    assert brand == GetNetCardBrand.AMEX.value


def test_detect_card_brand_elo(getnet_client):
    """Teste de detecção de bandeira Elo"""
    brand = getnet_client._detect_card_brand("4011111111111111")
    assert brand == GetNetCardBrand.ELO.value


# ============================================================================
# TESTES DE FORMATAÇÃO DE STATUS
# ============================================================================

def test_format_status(getnet_client):
    """Teste de formatação de status"""
    assert getnet_client.format_status("PENDING") == "Pendente"
    assert getnet_client.format_status("AUTHORIZED") == "Autorizado"
    assert getnet_client.format_status("CONFIRMED") == "Confirmado"
    assert getnet_client.format_status("CANCELED") == "Cancelado"
    assert getnet_client.format_status("DENIED") == "Negado"


def test_is_success(getnet_client, mock_credit_card_response):
    """Teste de verificação de sucesso"""
    # Sucesso
    assert getnet_client.is_success(mock_credit_card_response) is True

    # Falha
    failed_response = mock_credit_card_response.copy()
    failed_response["status"] = "DENIED"
    assert getnet_client.is_success(failed_response) is False


# ============================================================================
# TESTES DE OAUTH2
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_get_access_token(mock_client, getnet_client):
    """Teste de obtenção de access token"""
    # Mock do HTTP client
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

    # Obter token
    token = await getnet_client._get_access_token()

    assert token == "test_token_12345"
    assert getnet_client._access_token == "test_token_12345"


# ============================================================================
# TESTES DE PAGAMENTO CARTÃO DE CRÉDITO (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_create_credit_card_payment_success(mock_client, getnet_client, mock_credit_card_response):
    """Teste de criação de pagamento com cartão de crédito"""
    # Mock OAuth2
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    # Mock payment response
    mock_payment_response = Mock()
    mock_payment_response.json.return_value = mock_credit_card_response
    mock_payment_response.raise_for_status = Mock()

    mock_instance = Mock()
    # Primeiro post é OAuth, segundo é pagamento
    mock_instance.post = AsyncMock(side_effect=[mock_auth_response, mock_payment_response])
    mock_instance.request = AsyncMock(return_value=mock_payment_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    # Criar pagamento
    result = await getnet_client.create_credit_card_payment(
        amount=100.00,
        order_id="ORD-001",
        customer_id="CUST-001",
        card_number="4111111111111111",
        card_holder_name="João Silva",
        card_expiration_month="12",
        card_expiration_year="25",
        card_cvv="123",
        installments=1,
        capture=True
    )

    # Verificar resultado
    assert result is not None
    assert result["payment_id"] == "abc123-def456-ghi789"
    assert result["status"] == "AUTHORIZED"


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_create_credit_card_payment_with_installments(mock_client, getnet_client, mock_credit_card_response):
    """Teste de pagamento parcelado"""
    # Mock OAuth2
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    # Mock payment
    mock_credit_card_response["credit"]["number_installments"] = 3
    mock_payment_response = Mock()
    mock_payment_response.json.return_value = mock_credit_card_response
    mock_payment_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(side_effect=[mock_auth_response, mock_payment_response])
    mock_instance.request = AsyncMock(return_value=mock_payment_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    result = await getnet_client.create_credit_card_payment(
        amount=300.00,
        order_id="ORD-002",
        customer_id="CUST-001",
        card_number="4111111111111111",
        card_holder_name="João Silva",
        card_expiration_month="12",
        card_expiration_year="25",
        card_cvv="123",
        installments=3
    )

    assert result["credit"]["number_installments"] == 3


# ============================================================================
# TESTES DE PIX (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_create_pix_payment(mock_client, getnet_client, mock_pix_response):
    """Teste de criação de pagamento PIX"""
    # Mock OAuth2
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    # Mock PIX
    mock_payment_response = Mock()
    mock_payment_response.json.return_value = mock_pix_response
    mock_payment_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(side_effect=[mock_auth_response, mock_payment_response])
    mock_instance.request = AsyncMock(return_value=mock_payment_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    result = await getnet_client.create_pix_payment(
        amount=50.00,
        order_id="ORD-PIX-001",
        customer_id="CUST-001",
        customer_name="João Silva",
        customer_document="12345678909",
        expiration_minutes=30
    )

    assert result is not None
    assert result["payment_id"] == "pix-abc123"
    assert result["status"] == "PENDING"
    assert "qr_code" in result
    assert "emv" in result


# ============================================================================
# TESTES DE VALIDAÇÃO
# ============================================================================

@pytest.mark.asyncio
async def test_credit_card_payment_invalid_installments(getnet_client):
    """Teste de validação de parcelas inválidas"""
    with pytest.raises(ValueError, match="Parcelas devem estar entre 1 e 12"):
        await getnet_client.create_credit_card_payment(
            amount=100.00,
            order_id="ORD-001",
            customer_id="CUST-001",
            card_number="4111111111111111",
            card_holder_name="João Silva",
            card_expiration_month="12",
            card_expiration_year="25",
            card_cvv="123",
            installments=15  # Inválido
        )


@pytest.mark.asyncio
async def test_credit_card_payment_missing_data(getnet_client):
    """Teste com dados do cartão incompletos"""
    with pytest.raises(ValueError, match="Dados do cartão incompletos"):
        await getnet_client.create_credit_card_payment(
            amount=100.00,
            order_id="ORD-001",
            customer_id="CUST-001",
            card_number="4111111111111111",
            # Faltando dados
            card_holder_name=None,
            card_expiration_month=None,
            card_expiration_year=None,
            card_cvv=None,
            card_token=None  # E sem token também
        )


# ============================================================================
# TESTES DE TOKENIZAÇÃO (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_tokenize_card(mock_client, getnet_client):
    """Teste de tokenização de cartão"""
    # Mock OAuth2
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    # Mock tokenization
    mock_token_response = Mock()
    mock_token_response.json.return_value = {
        "number_token": "TOKEN-ABC123XYZ789"
    }
    mock_token_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(side_effect=[mock_auth_response, mock_token_response])
    mock_instance.request = AsyncMock(return_value=mock_token_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    token = await getnet_client.tokenize_card(
        card_number="4111111111111111",
        customer_id="CUST-001"
    )

    assert token == "TOKEN-ABC123XYZ789"


# ============================================================================
# TESTES DE CAPTURA E CANCELAMENTO (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_capture_payment(mock_client, getnet_client):
    """Teste de captura de pagamento"""
    # Mock OAuth2
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    # Mock capture
    mock_capture_response = Mock()
    mock_capture_response.json.return_value = {
        "payment_id": "abc123",
        "status": "CONFIRMED"
    }
    mock_capture_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(return_value=mock_capture_response)
    mock_instance.request = AsyncMock(return_value=mock_capture_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    # Set token to avoid OAuth call
    getnet_client._access_token = "test_token"

    mock_client.return_value = mock_instance

    result = await getnet_client.capture_payment("abc123")

    assert result["status"] == "CONFIRMED"


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_cancel_payment(mock_client, getnet_client):
    """Teste de cancelamento de pagamento"""
    # Mock OAuth2
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    # Mock cancel
    mock_cancel_response = Mock()
    mock_cancel_response.json.return_value = {
        "payment_id": "abc123",
        "status": "CANCELED"
    }
    mock_cancel_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(return_value=mock_cancel_response)
    mock_instance.request = AsyncMock(return_value=mock_cancel_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    # Set token
    getnet_client._access_token = "test_token"

    mock_client.return_value = mock_instance

    result = await getnet_client.cancel_payment("abc123")

    assert result["status"] == "CANCELED"


# ============================================================================
# TESTES DE CONSULTA (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_query_payment(mock_client, getnet_client, mock_credit_card_response):
    """Teste de consulta de pagamento"""
    mock_response = Mock()
    mock_response.json.return_value = mock_credit_card_response
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_instance.request = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    # Set token
    getnet_client._access_token = "test_token"

    mock_client.return_value = mock_instance

    result = await getnet_client.query_payment("abc123-def456-ghi789")

    assert "payment_id" in result
    assert result["payment_id"] == "abc123-def456-ghi789"


# ============================================================================
# TESTES DE EDGE CASES
# ============================================================================

def test_format_card_number(getnet_client):
    """Teste de formatação de número de cartão"""
    # Números com espaços e traços devem ser limpos internamente
    cards = [
        "4111 1111 1111 1111",
        "4111-1111-1111-1111",
        "4111111111111111"
    ]

    for card in cards:
        brand = getnet_client._detect_card_brand(card)
        assert brand == GetNetCardBrand.VISA.value


# ============================================================================
# TESTES DE INTEGRAÇÃO MOCK COMPLETO
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_full_payment_flow(mock_client, getnet_client, mock_credit_card_response):
    """Teste de fluxo completo: criar, capturar, consultar"""
    # Setup mocks
    mock_auth_response = Mock()
    mock_auth_response.json.return_value = {"access_token": "test_token"}
    mock_auth_response.raise_for_status = Mock()

    mock_payment_create = Mock()
    mock_payment_create.json.return_value = mock_credit_card_response
    mock_payment_create.raise_for_status = Mock()

    mock_capture_response = Mock()
    captured_response = mock_credit_card_response.copy()
    captured_response["status"] = "CONFIRMED"
    mock_capture_response.json.return_value = captured_response
    mock_capture_response.raise_for_status = Mock()

    mock_query_response = Mock()
    mock_query_response.json.return_value = captured_response
    mock_query_response.raise_for_status = Mock()

    mock_instance = Mock()
    # Auth + Create payment
    mock_instance.post = AsyncMock(side_effect=[mock_auth_response, mock_payment_create, mock_capture_response])
    mock_instance.request = AsyncMock(side_effect=[mock_payment_create, mock_capture_response, mock_query_response])
    mock_instance.get = AsyncMock(return_value=mock_query_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    # 1. Criar pagamento
    payment = await getnet_client.create_credit_card_payment(
        amount=100.00,
        order_id="ORD-FLOW-001",
        customer_id="CUST-001",
        card_number="4111111111111111",
        card_holder_name="João Silva",
        card_expiration_month="12",
        card_expiration_year="25",
        card_cvv="123",
        capture=False  # Sem captura automática
    )

    payment_id = payment["payment_id"]
    assert payment_id is not None

    # 2. Capturar pagamento
    capture_result = await getnet_client.capture_payment(payment_id)
    assert capture_result["status"] == "CONFIRMED"

    # 3. Consultar pagamento
    query_result = await getnet_client.query_payment(payment_id)
    assert query_result["status"] == "CONFIRMED"
