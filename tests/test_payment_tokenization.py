"""
Testes para Tokenização de Cartões - Payment Gateway Service

Valida funcionalidade de tokenização PCI-compliant para Cielo e GetNet
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.services.payment_gateway_service import (
    PaymentGatewayService,
    PaymentGateway
)
from app.core.exceptions import ValidationException, BusinessRuleException
from app.integrations.cielo import CieloCardBrand


@pytest.fixture
def payment_service():
    """Fixture de serviço de pagamento"""
    return PaymentGatewayService()


# ============================================
# TESTES DE TOKENIZAÇÃO - CIELO
# ============================================

@pytest.mark.asyncio
async def test_tokenize_cielo_card_success(payment_service):
    """Teste de tokenização bem-sucedida na Cielo"""
    mock_token = "TOKEN-CIELO-ABC123XYZ456"

    with patch.object(
        payment_service.cielo,
        'tokenize_card',
        new_callable=AsyncMock,
        return_value=mock_token
    ):
        result = await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "4532000000000000",
                "holder": "JOÃO SILVA",
                "expiration": "12/2028",
                "brand": "Visa"
            }
        )

    assert result["gateway"] == "cielo"
    assert result["card_token"] == mock_token
    assert result["last_digits"] == "0000"
    assert "created_at" in result


@pytest.mark.asyncio
async def test_tokenize_cielo_card_with_enum_brand(payment_service):
    """Teste de tokenização Cielo com brand como Enum"""
    mock_token = "TOKEN-CIELO-MASTER123"

    with patch.object(
        payment_service.cielo,
        'tokenize_card',
        new_callable=AsyncMock,
        return_value=mock_token
    ):
        result = await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "5555 4444 3333 2222",
                "holder": "MARIA SANTOS",
                "expiration": "06/2027",
                "brand": CieloCardBrand.MASTER
            }
        )

    assert result["card_token"] == mock_token
    assert result["last_digits"] == "2222"


@pytest.mark.asyncio
async def test_tokenize_cielo_card_with_string_brand_variations(payment_service):
    """Teste de tokenização Cielo com variações de nome de bandeira"""
    mock_token = "TOKEN-CIELO-ELO789"

    # Testar diferentes variações
    brands_to_test = ["ELO", "elo", "Elo"]

    for brand in brands_to_test:
        with patch.object(
            payment_service.cielo,
            'tokenize_card',
            new_callable=AsyncMock,
            return_value=mock_token
        ):
            result = await payment_service.tokenize_card(
                gateway=PaymentGateway.CIELO,
                card_data={
                    "number": "6362000000000005",
                    "holder": "PEDRO OLIVEIRA",
                    "expiration": "03/2029",
                    "brand": brand
                }
            )

        assert result["card_token"] == mock_token


@pytest.mark.asyncio
async def test_tokenize_cielo_card_missing_holder(payment_service):
    """Teste de tokenização Cielo sem titular (deve falhar)"""
    with pytest.raises(ValidationException) as exc_info:
        await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "4532000000000000",
                "expiration": "12/2028",
                "brand": "Visa"
            }
        )

    assert "holder" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_tokenize_cielo_card_missing_expiration(payment_service):
    """Teste de tokenização Cielo sem data de expiração (deve falhar)"""
    with pytest.raises(ValidationException) as exc_info:
        await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "4532000000000000",
                "holder": "JOÃO SILVA",
                "brand": "Visa"
            }
        )

    assert "expiration" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_tokenize_cielo_card_missing_brand(payment_service):
    """Teste de tokenização Cielo sem bandeira (deve falhar)"""
    with pytest.raises(ValidationException) as exc_info:
        await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "4532000000000000",
                "holder": "JOÃO SILVA",
                "expiration": "12/2028"
            }
        )

    assert "brand" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_tokenize_cielo_card_invalid_brand(payment_service):
    """Teste de tokenização Cielo com bandeira inválida"""
    with pytest.raises(ValidationException) as exc_info:
        await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "4532000000000000",
                "holder": "JOÃO SILVA",
                "expiration": "12/2028",
                "brand": "InvalidBrand"
            }
        )

    assert "inválida" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_tokenize_cielo_card_with_formatted_number(payment_service):
    """Teste de tokenização com número formatado (espaços e hífens)"""
    mock_token = "TOKEN-CIELO-FORMATTED"

    with patch.object(
        payment_service.cielo,
        'tokenize_card',
        new_callable=AsyncMock,
        return_value=mock_token
    ):
        result = await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "4532-0000-0000-0000",
                "holder": "TESTE FORMATAÇÃO",
                "expiration": "12/2028",
                "brand": "Visa"
            }
        )

    assert result["last_digits"] == "0000"


# ============================================
# TESTES DE TOKENIZAÇÃO - GETNET
# ============================================

@pytest.mark.asyncio
async def test_tokenize_getnet_card_success(payment_service):
    """Teste de tokenização bem-sucedida na GetNet"""
    mock_token = "TOKEN-GETNET-XYZ789ABC123"

    with patch.object(
        payment_service.getnet,
        'tokenize_card',
        new_callable=AsyncMock,
        return_value=mock_token
    ):
        result = await payment_service.tokenize_card(
            gateway=PaymentGateway.GETNET,
            card_data={
                "number": "5555444433332222"
            },
            customer_data={
                "customer_id": "CUST-001"
            }
        )

    assert result["gateway"] == "getnet"
    assert result["card_token"] == mock_token
    assert result["last_digits"] == "2222"
    assert "created_at" in result


@pytest.mark.asyncio
async def test_tokenize_getnet_card_missing_customer_id(payment_service):
    """Teste de tokenização GetNet sem customer_id (deve falhar)"""
    with pytest.raises(ValidationException) as exc_info:
        await payment_service.tokenize_card(
            gateway=PaymentGateway.GETNET,
            card_data={
                "number": "5555444433332222"
            }
        )

    assert "customer_id" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_tokenize_getnet_card_customer_data_without_id(payment_service):
    """Teste de tokenização GetNet com customer_data mas sem ID"""
    with pytest.raises(ValidationException) as exc_info:
        await payment_service.tokenize_card(
            gateway=PaymentGateway.GETNET,
            card_data={
                "number": "5555444433332222"
            },
            customer_data={
                "name": "Cliente Teste"
            }
        )

    assert "customer_id" in str(exc_info.value).lower()


# ============================================
# TESTES DE VALIDAÇÃO GERAL
# ============================================

@pytest.mark.asyncio
async def test_tokenize_card_missing_number(payment_service):
    """Teste de tokenização sem número do cartão (deve falhar)"""
    with pytest.raises(ValidationException) as exc_info:
        await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "holder": "JOÃO SILVA",
                "expiration": "12/2028",
                "brand": "Visa"
            }
        )

    assert "número" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_tokenize_card_unsupported_gateway(payment_service):
    """Teste de tokenização com gateway não suportado"""
    with pytest.raises(BusinessRuleException) as exc_info:
        await payment_service.tokenize_card(
            gateway=PaymentGateway.MERCADOPAGO,
            card_data={
                "number": "4532000000000000"
            }
        )

    assert "não suporta tokenização" in str(exc_info.value).lower()


# ============================================
# TESTES DE INTEGRAÇÃO COM PAGAMENTO
# ============================================

@pytest.mark.asyncio
async def test_tokenize_and_use_for_payment(payment_service):
    """Teste de fluxo completo: tokenizar e usar token para pagamento"""
    # 1. Tokenizar cartão
    mock_token = "TOKEN-ABC123"

    with patch.object(
        payment_service.cielo,
        'tokenize_card',
        new_callable=AsyncMock,
        return_value=mock_token
    ):
        token_result = await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "4532000000000000",
                "holder": "JOÃO SILVA",
                "expiration": "12/2028",
                "brand": "Visa"
            }
        )

    assert token_result["card_token"] == mock_token

    # 2. Usar token para criar pagamento
    mock_payment = {
        "PaymentId": "PAY-123",
        "Status": "2",  # Captured
        "Amount": 10000,
        "Captured": True
    }

    with patch.object(
        payment_service.cielo,
        'create_credit_card_payment',
        new_callable=AsyncMock,
        return_value=mock_payment
    ):
        from app.services.payment_gateway_service import PaymentMethod
        payment_result = await payment_service.create_payment(
            gateway=PaymentGateway.CIELO,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("100.00"),
            order_id="ORDER-001",
            customer_data={"name": "João Silva"},
            card_data={
                "token": token_result["card_token"],
                "last_digits": token_result["last_digits"]
            }
        )

    # Verificar que pagamento foi criado
    assert payment_result["payment_id"] == "PAY-123"


@pytest.mark.asyncio
async def test_tokenize_card_security_no_full_number_in_response(payment_service):
    """Teste de segurança: número completo não deve aparecer na resposta"""
    mock_token = "TOKEN-SECURITY-TEST"

    with patch.object(
        payment_service.cielo,
        'tokenize_card',
        new_callable=AsyncMock,
        return_value=mock_token
    ):
        result = await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "4532111122223333",
                "holder": "SECURITY TEST",
                "expiration": "12/2028",
                "brand": "Visa"
            }
        )

    # Verificar que resposta não contém número completo
    assert "4532111122223333" not in str(result)

    # Apenas últimos 4 dígitos
    assert result["last_digits"] == "3333"

    # Token presente
    assert result["card_token"] == mock_token


# ============================================
# TESTES DE PERFORMANCE E EDGE CASES
# ============================================

@pytest.mark.asyncio
async def test_tokenize_multiple_cards_same_customer(payment_service):
    """Teste de tokenização de múltiplos cartões para mesmo cliente"""
    mock_tokens = ["TOKEN-1", "TOKEN-2", "TOKEN-3"]

    for i, token in enumerate(mock_tokens):
        with patch.object(
            payment_service.getnet,
            'tokenize_card',
            new_callable=AsyncMock,
            return_value=token
        ):
            result = await payment_service.tokenize_card(
                gateway=PaymentGateway.GETNET,
                card_data={
                    "number": f"555544443333{i:04d}"
                },
                customer_data={
                    "customer_id": "CUST-001"
                }
            )

        assert result["card_token"] == token
        assert result["last_digits"] == f"{i:04d}"


@pytest.mark.asyncio
async def test_tokenize_card_all_supported_cielo_brands(payment_service):
    """Teste de tokenização com todas as bandeiras suportadas pela Cielo"""
    brands = [
        "Visa", "Master", "Elo", "Amex", "Diners",
        "Discover", "JCB", "Aura"
    ]

    for brand in brands:
        mock_token = f"TOKEN-{brand.upper()}"

        with patch.object(
            payment_service.cielo,
            'tokenize_card',
            new_callable=AsyncMock,
            return_value=mock_token
        ):
            result = await payment_service.tokenize_card(
                gateway=PaymentGateway.CIELO,
                card_data={
                    "number": "4532000000000000",
                    "holder": f"TESTE {brand}",
                    "expiration": "12/2028",
                    "brand": brand
                }
            )

        assert result["card_token"] == mock_token
