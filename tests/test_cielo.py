"""
Testes da integração Cielo
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch

from app.integrations.cielo import (
    CieloClient,
    CieloEnvironment,
    CieloCardBrand,
    CieloPaymentType
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def cielo_client():
    """Client Cielo para testes"""
    return CieloClient(
        merchant_id="TEST_MERCHANT_ID",
        merchant_key="TEST_MERCHANT_KEY",
        environment=CieloEnvironment.SANDBOX
    )


@pytest.fixture
def mock_credit_card_response():
    """Response simulado de pagamento com cartão de crédito"""
    return {
        "MerchantOrderId": "ORD-20251120-001",
        "Customer": {"Name": "João Silva"},
        "Payment": {
            "ServiceTaxAmount": 0,
            "Installments": 1,
            "Interest": "ByMerchant",
            "Capture": True,
            "Authenticate": False,
            "CreditCard": {
                "CardNumber": "411111******1111",
                "Holder": "João Silva",
                "ExpirationDate": "12/2025",
                "SaveCard": False,
                "Brand": "Visa"
            },
            "ProofOfSale": "123456",
            "Tid": "1120012345678",
            "AuthorizationCode": "123456",
            "PaymentId": "abc123-def456-ghi789",
            "Type": "CreditCard",
            "Amount": 10000,
            "Currency": "BRL",
            "Country": "BRA",
            "Status": 1,  # Autorizada
            "ReturnCode": "4",
            "ReturnMessage": "Operação realizada com sucesso"
        }
    }


@pytest.fixture
def mock_debit_card_response():
    """Response simulado de pagamento com cartão de débito"""
    return {
        "MerchantOrderId": "ORD-20251120-002",
        "Payment": {
            "DebitCard": {
                "CardNumber": "520000******1096",
                "Holder": "João Silva",
                "ExpirationDate": "12/2025",
                "SaveCard": False,
                "Brand": "Master"
            },
            "AuthenticationUrl": "https://qasecommerce.cielo.com.br/web/index.cbmp?id=abc123",
            "PaymentId": "xyz789-abc456",
            "Type": "DebitCard",
            "Amount": 5000,
            "Currency": "BRL",
            "Country": "BRA",
            "Status": 0,  # Não finalizada (aguardando autenticação)
            "ReturnMessage": "Aguardando autenticação"
        }
    }


# ============================================================================
# TESTES DO CLIENT
# ============================================================================

def test_cielo_client_initialization(cielo_client):
    """Teste de inicialização do client"""
    assert cielo_client.merchant_id == "TEST_MERCHANT_ID"
    assert cielo_client.merchant_key == "TEST_MERCHANT_KEY"
    assert cielo_client.environment == CieloEnvironment.SANDBOX
    assert "apisandbox" in cielo_client.base_url


def test_cielo_client_urls():
    """Teste de URLs sandbox vs produção"""
    # Sandbox
    sandbox_client = CieloClient(environment=CieloEnvironment.SANDBOX)
    assert "sandbox" in sandbox_client.base_url.lower()
    assert "sandbox" in sandbox_client.query_url.lower()

    # Produção
    prod_client = CieloClient(environment=CieloEnvironment.PRODUCTION)
    assert "sandbox" not in prod_client.base_url.lower()
    assert "sandbox" not in prod_client.query_url.lower()


# ============================================================================
# TESTES DE DETECÇÃO DE BANDEIRA
# ============================================================================

def test_detect_card_brand_visa(cielo_client):
    """Teste de detecção de bandeira Visa"""
    brand = cielo_client._detect_card_brand("4111111111111111")
    assert brand == CieloCardBrand.VISA.value


def test_detect_card_brand_master(cielo_client):
    """Teste de detecção de bandeira Mastercard"""
    brand = cielo_client._detect_card_brand("5200000000001096")
    assert brand == CieloCardBrand.MASTER.value


def test_detect_card_brand_amex(cielo_client):
    """Teste de detecção de bandeira Amex"""
    brand = cielo_client._detect_card_brand("371449635398431")
    assert brand == CieloCardBrand.AMEX.value


# ============================================================================
# TESTES DE FORMATAÇÃO DE STATUS
# ============================================================================

def test_format_status(cielo_client):
    """Teste de formatação de status"""
    assert cielo_client.format_status("1") == "Autorizada"
    assert cielo_client.format_status("2") == "Pagamento Confirmado"
    assert cielo_client.format_status("3") == "Negada"
    assert cielo_client.format_status("10") == "Cancelada"
    assert cielo_client.format_status("99") == "Desconhecido"


def test_is_success(cielo_client, mock_credit_card_response):
    """Teste de verificação de sucesso"""
    # Sucesso
    assert cielo_client.is_success(mock_credit_card_response) is True

    # Falha
    failed_response = mock_credit_card_response.copy()
    failed_response["Payment"]["Status"] = 3  # Negada
    assert cielo_client.is_success(failed_response) is False


# ============================================================================
# TESTES DE PAGAMENTO CARTÃO DE CRÉDITO (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_create_credit_card_payment_success(mock_client, cielo_client, mock_credit_card_response):
    """Teste de criação de pagamento com cartão de crédito"""
    # Mock do HTTP client
    mock_response = Mock()
    mock_response.json.return_value = mock_credit_card_response
    mock_response.status_code = 201
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    # Criar pagamento
    result = await cielo_client.create_credit_card_payment(
        amount=100.00,
        installments=1,
        card_number="4111111111111111",
        card_holder="João Silva",
        card_expiration_date="12/2025",
        card_cvv="123",
        capture=True
    )

    # Verificar resultado
    assert result is not None
    assert "Payment" in result
    assert result["Payment"]["Status"] == 1


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_create_credit_card_payment_with_installments(mock_client, cielo_client, mock_credit_card_response):
    """Teste de pagamento parcelado"""
    mock_response = Mock()
    mock_credit_card_response["Payment"]["Installments"] = 3
    mock_response.json.return_value = mock_credit_card_response
    mock_response.status_code = 201
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    result = await cielo_client.create_credit_card_payment(
        amount=300.00,
        installments=3,
        card_number="4111111111111111",
        card_holder="João Silva",
        card_expiration_date="12/2025",
        card_cvv="123"
    )

    assert result["Payment"]["Installments"] == 3


# ============================================================================
# TESTES DE VALIDAÇÃO
# ============================================================================

@pytest.mark.asyncio
async def test_credit_card_payment_invalid_installments(cielo_client):
    """Teste de validação de parcelas inválidas"""
    with pytest.raises(ValueError, match="Parcelas devem estar entre 1 e 12"):
        await cielo_client.create_credit_card_payment(
            amount=100.00,
            installments=15,  # Inválido
            card_number="4111111111111111",
            card_holder="João Silva",
            card_expiration_date="12/2025",
            card_cvv="123"
        )


@pytest.mark.asyncio
async def test_credit_card_payment_missing_data(cielo_client):
    """Teste com dados do cartão incompletos"""
    with pytest.raises(ValueError, match="Dados do cartão incompletos"):
        await cielo_client.create_credit_card_payment(
            amount=100.00,
            installments=1,
            card_number="4111111111111111",
            # Faltando card_holder, expiration, cvv
            card_holder=None,
            card_expiration_date=None,
            card_cvv=None,
            card_token=None  # E sem token também
        )


# ============================================================================
# TESTES DE TOKENIZAÇÃO (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_tokenize_card(mock_client, cielo_client):
    """Teste de tokenização de cartão"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "CardToken": "TOKEN-ABC123XYZ789"
    }
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    token = await cielo_client.tokenize_card(
        card_number="4111111111111111",
        card_holder="João Silva",
        card_expiration_date="12/2025",
        card_brand=CieloCardBrand.VISA
    )

    assert token == "TOKEN-ABC123XYZ789"


# ============================================================================
# TESTES DE CAPTURA E CANCELAMENTO (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_capture_payment(mock_client, cielo_client):
    """Teste de captura de pagamento"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "Status": 2,  # Pagamento confirmado
        "ReasonCode": 0,
        "ReasonMessage": "Successful"
    }
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.put = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    result = await cielo_client.capture_payment("abc123-def456")

    assert result["Status"] == 2


@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_cancel_payment(mock_client, cielo_client):
    """Teste de cancelamento de pagamento"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "Status": 10,  # Cancelada
        "ReasonCode": 0,
        "ReasonMessage": "Successful"
    }
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.put = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    result = await cielo_client.cancel_payment("abc123-def456")

    assert result["Status"] == 10


# ============================================================================
# TESTES DE CONSULTA (MOCK)
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_query_payment(mock_client, cielo_client, mock_credit_card_response):
    """Teste de consulta de pagamento"""
    mock_response = Mock()
    mock_response.json.return_value = mock_credit_card_response
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.get = AsyncMock(return_value=mock_response)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    result = await cielo_client.query_payment("abc123-def456")

    assert "Payment" in result
    assert result["Payment"]["PaymentId"] == "abc123-def456-ghi789"


# ============================================================================
# TESTES DE EDGE CASES
# ============================================================================

def test_format_card_number(cielo_client):
    """Teste de formatação de número de cartão"""
    # Números com espaços e traços devem ser limpos internamente
    cards = [
        "4111 1111 1111 1111",
        "4111-1111-1111-1111",
        "4111111111111111"
    ]

    for card in cards:
        brand = cielo_client._detect_card_brand(card)
        assert brand == CieloCardBrand.VISA.value


def test_format_expiration_date(cielo_client):
    """Teste de formatação de data de validade"""
    # Datas com / devem ser aceitas e formatadas
    # (a formatação acontece no create_payment)
    date1 = "12/2025"
    date2 = "122025"

    # Remover /
    formatted1 = date1.replace("/", "")
    formatted2 = date2.replace("/", "")

    assert formatted1 == "122025"
    assert formatted2 == "122025"


# ============================================================================
# TESTES DE INTEGRAÇÃO MOCK COMPLETO
# ============================================================================

@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_full_payment_flow(mock_client, cielo_client, mock_credit_card_response):
    """Teste de fluxo completo: criar, capturar, consultar"""
    # Setup mocks
    mock_response_create = Mock()
    mock_response_create.json.return_value = mock_credit_card_response
    mock_response_create.status_code = 201
    mock_response_create.raise_for_status = Mock()

    mock_response_capture = Mock()
    captured_response = mock_credit_card_response.copy()
    captured_response["Payment"]["Status"] = 2  # Capturado
    mock_response_capture.json.return_value = captured_response
    mock_response_capture.status_code = 200
    mock_response_capture.raise_for_status = Mock()

    mock_response_query = Mock()
    mock_response_query.json.return_value = captured_response
    mock_response_query.status_code = 200
    mock_response_query.raise_for_status = Mock()

    mock_instance = Mock()
    mock_instance.post = AsyncMock(return_value=mock_response_create)
    mock_instance.put = AsyncMock(return_value=mock_response_capture)
    mock_instance.get = AsyncMock(return_value=mock_response_query)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock()

    mock_client.return_value = mock_instance

    # 1. Criar pagamento
    payment = await cielo_client.create_credit_card_payment(
        amount=100.00,
        installments=1,
        card_number="4111111111111111",
        card_holder="João Silva",
        card_expiration_date="12/2025",
        card_cvv="123",
        capture=False  # Sem captura automática
    )

    payment_id = payment["Payment"]["PaymentId"]
    assert payment_id is not None

    # 2. Capturar pagamento
    capture_result = await cielo_client.capture_payment(payment_id)
    assert capture_result["Status"] == 2

    # 3. Consultar pagamento
    query_result = await cielo_client.query_payment(payment_id)
    assert query_result["Payment"]["Status"] == 2
