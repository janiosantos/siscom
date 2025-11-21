"""
Testes do Payment Gateway Service - Versão Simplificada

Valida integração com:
- Cielo (Cartão de Crédito e Débito)
- GetNet (Cartão e PIX)
- Mercado Pago (PIX e Cartão)
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from app.services.payment_gateway_service import (
    PaymentGatewayService,
    PaymentGateway,
    PaymentMethod,
    PaymentStatus
)
from app.core.exceptions import BusinessRuleException


@pytest.fixture
def payment_service():
    """Fixture do serviço de pagamento"""
    service = PaymentGatewayService()
    service.initialize_mercadopago(
        access_token="TEST-ACCESS-TOKEN",
        public_key="TEST-PUBLIC-KEY"
    )
    return service


# ============================================
# TESTES CIELO - CARTÃO DE CRÉDITO
# ============================================

class TestCieloCreditCard:
    """Testes Cielo - Cartão de Crédito"""

    @pytest.mark.asyncio
    async def test_cielo_credit_card_success(self, payment_service):
        """Teste de pagamento com cartão Cielo - Sucesso"""

        # Mock da resposta da Cielo
        mock_response = {
            "PaymentId": "abc-123-def",
            "Tid": "TID123456",
            "Status": "2",  # Capturada
            "Amount": 15000,  # R$ 150,00 em centavos
            "Installments": 3,
            "Captured": True,
            "AuthorizationCode": "AUTH123456",
            "ReturnCode": "4",
            "ReturnMessage": "Operacao realizada com sucesso"
        }

        with patch.object(
            payment_service.cielo,
            'create_credit_card_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("150.00"),
                order_id="ORDER-001",
                customer_data={"name": "João Silva"},
                card_data={
                    "number": "4532000000000000",
                    "holder": "JOAO SILVA",
                    "expiration": "12/2028",
                    "cvv": "123",
                    "brand": "Visa"
                },
                installments=3,
                capture=True
            )

        # Validações
        assert result["gateway"] == "cielo"
        assert result["status"] == PaymentStatus.CAPTURED
        assert result["amount"] == 150.00
        assert result["installments"] == 3
        assert result["captured"] is True
        assert result["payment_id"] == "abc-123-def"

    @pytest.mark.asyncio
    async def test_cielo_credit_card_pre_auth(self, payment_service):
        """Teste de pré-autorização Cielo"""

        mock_response = {
            "PaymentId": "pre-auth-123",
            "Status": "1",  # Autorizada
            "Amount": 20000,
            "Installments": 1,
            "Captured": False,
            "AuthorizationCode": "AUTH789"
        }

        with patch.object(
            payment_service.cielo,
            'create_credit_card_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("200.00"),
                order_id="ORDER-002",
                customer_data={"name": "Maria Santos"},
                card_data={
                    "number": "4532000000000000",
                    "holder": "MARIA SANTOS",
                    "expiration": "12/2028",
                    "cvv": "123"
                },
                capture=False  # Pré-autorização
            )

        assert result["status"] == PaymentStatus.AUTHORIZED
        assert result["captured"] is False


# ============================================
# TESTES GETNET - PIX E CARTÃO
# ============================================

class TestGetNetPayments:
    """Testes GetNet - PIX e Cartão"""

    @pytest.mark.asyncio
    async def test_getnet_pix_payment(self, payment_service):
        """Teste de pagamento PIX GetNet"""

        mock_response = {
            "payment_id": "pix-getnet-123",
            "order_id": "ORDER-PIX-001",
            "status": "PENDING",
            "amount": 25000,  # R$ 250,00 em centavos
            "qr_code": "00020126580014BR.GOV.BCB.PIX0136123456789012",
            "qr_code_image": "iVBORw0KGgo...",
        }

        with patch.object(
            payment_service.getnet,
            'create_pix_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.GETNET,
                payment_method=PaymentMethod.PIX,
                amount=Decimal("250.00"),
                order_id="ORDER-PIX-001",
                customer_data={
                    "name": "Carlos Silva",
                    "cpf": "12345678900"
                }
            )

        assert result["gateway"] == "getnet"
        assert result["status"] == PaymentStatus.PENDING
        assert result["pix_qrcode"] is not None
        assert "00020126" in result["pix_qrcode"]

    @pytest.mark.asyncio
    async def test_getnet_credit_card(self, payment_service):
        """Teste de cartão de crédito GetNet"""

        mock_response = {
            "payment_id": "card-getnet-456",
            "order_id": "ORDER-003",
            "status": "APPROVED",
            "amount": 18000,
            "installments": 2,
            "credit": {
                "authorization_code": "AUTH-GN-123"
            }
        }

        with patch.object(
            payment_service.getnet,
            'create_credit_card_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.GETNET,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("180.00"),
                order_id="ORDER-003",
                customer_data={
                    "name": "Ana Oliveira",
                    "cpf": "98765432100"
                },
                card_data={
                    "number": "5555555555555555",
                    "holder": "ANA OLIVEIRA",
                    "expiration": "12/28",
                    "cvv": "123"
                },
                installments=2
            )

        assert result["status"] == PaymentStatus.CAPTURED
        assert result["installments"] == 2


# ============================================
# TESTES MERCADO PAGO
# ============================================

class TestMercadoPagoPayments:
    """Testes Mercado Pago"""

    @pytest.mark.asyncio
    async def test_mercadopago_pix(self, payment_service):
        """Teste PIX Mercado Pago"""

        mock_response = {
            "id": 123456789,
            "status": "pending",
            "transaction_amount": 350.00,
            "qr_code": "00020126580014BR.GOV.BCB.PIX9876543210",
            "point_of_interaction": {
                "transaction_data": {
                    "qr_code": "00020126580014BR.GOV.BCB.PIX9876543210"
                }
            },
            "valor": Decimal("350.00")
        }

        with patch.object(
            payment_service.mercadopago,
            'criar_pagamento_pix',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.MERCADOPAGO,
                payment_method=PaymentMethod.PIX,
                amount=Decimal("350.00"),
                order_id="ORDER-MP-001",
                customer_data={
                    "name": "Pedro Costa",
                    "email": "pedro@email.com"
                }
            )

        assert result["gateway"] == "mercadopago"
        assert result["status"] == PaymentStatus.PENDING
        assert result["pix_qrcode"] is not None

    @pytest.mark.asyncio
    async def test_mercadopago_credit_card(self, payment_service):
        """Teste cartão Mercado Pago"""

        mock_response = {
            "id": 987654321,
            "status": "approved",
            "transaction_amount": 280.00,
            "installments": 4,
            "valor": Decimal("280.00")
        }

        with patch.object(
            payment_service.mercadopago,
            'criar_pagamento_cartao',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.MERCADOPAGO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("280.00"),
                order_id="ORDER-MP-002",
                customer_data={
                    "name": "Lucia Ferreira",
                    "email": "lucia@email.com"
                },
                card_data={
                    "token": "CARD_TOKEN_ABC123"
                },
                installments=4
            )

        assert result["status"] == PaymentStatus.CAPTURED
        assert result["installments"] == 4


# ============================================
# TESTES DE OPERAÇÕES
# ============================================

class TestPaymentOperations:
    """Testes de captura, cancelamento e consulta"""

    @pytest.mark.asyncio
    async def test_capture_payment(self, payment_service):
        """Teste de captura de pagamento"""

        mock_response = {
            "PaymentId": "cap-123",
            "Status": "2",  # Capturada
            "Captured": True,
            "Amount": 30000
        }

        with patch.object(
            payment_service.cielo,
            'capture_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.capture_payment(
                gateway=PaymentGateway.CIELO,
                payment_id="pre-auth-123",
                amount=Decimal("300.00")
            )

        assert result["status"] == PaymentStatus.CAPTURED

    @pytest.mark.asyncio
    async def test_cancel_payment(self, payment_service):
        """Teste de cancelamento"""

        mock_response = {
            "PaymentId": "cancel-123",
            "Status": "10",  # Cancelada
            "VoidedAmount": 10000
        }

        with patch.object(
            payment_service.cielo,
            'cancel_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.cancel_payment(
                gateway=PaymentGateway.CIELO,
                payment_id="payment-123"
            )

        assert result["status"] == PaymentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_query_payment(self, payment_service):
        """Teste de consulta"""

        mock_response = {
            "PaymentId": "query-123",
            "Status": "2",
            "Amount": 15000
        }

        with patch.object(
            payment_service.cielo,
            'query_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.query_payment(
                gateway=PaymentGateway.CIELO,
                payment_id="query-123"
            )

        assert result["payment_id"] == "query-123"


# ============================================
# TESTES DE VALIDAÇÃO
# ============================================

class TestValidations:
    """Testes de validações de negócio"""

    @pytest.mark.asyncio
    async def test_minimum_amount_validation(self, payment_service):
        """Valor mínimo R$ 0,01"""

        with pytest.raises(BusinessRuleException, match="Valor mínimo"):
            await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("0.00"),
                order_id="INVALID",
                customer_data={"name": "Test"},
                card_data={"number": "123"}
            )

    @pytest.mark.asyncio
    async def test_installments_validation(self, payment_service):
        """Parcelas entre 1 e 12"""

        with pytest.raises(BusinessRuleException, match="parcelas"):
            await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("100.00"),
                order_id="INVALID",
                customer_data={"name": "Test"},
                card_data={"number": "123"},
                installments=15  # Inválido
            )

    @pytest.mark.asyncio
    async def test_card_data_required(self, payment_service):
        """Dados do cartão obrigatórios"""

        with pytest.raises(BusinessRuleException, match="Dados do cartão"):
            await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("100.00"),
                order_id="INVALID",
                customer_data={"name": "Test"},
                card_data=None  # Faltando
            )

    @pytest.mark.asyncio
    async def test_pix_not_available_cielo(self, payment_service):
        """PIX não disponível na Cielo"""

        with pytest.raises(BusinessRuleException, match="PIX não disponível"):
            await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.PIX,
                amount=Decimal("100.00"),
                order_id="INVALID",
                customer_data={"name": "Test"}
            )


# ============================================
# TESTES DE CENÁRIOS COMPLEXOS
# ============================================

class TestComplexScenarios:
    """Cenários complexos e edge cases"""

    @pytest.mark.asyncio
    async def test_gateway_fallback(self, payment_service):
        """Teste de fallback entre gateways"""

        # Mock Cielo negando
        cielo_response = {
            "PaymentId": "denied-123",
            "Status": "3",  # Negada
            "ReturnCode": "05"
        }

        # Mock GetNet aprovando
        getnet_response = {
            "payment_id": "approved-456",
            "status": "APPROVED",
            "amount": 10000
        }

        with patch.object(payment_service.cielo, 'create_credit_card_payment',
                         new_callable=AsyncMock, return_value=cielo_response):
            cielo_result = await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("100.00"),
                order_id="RETRY-001",
                customer_data={"name": "Test"},
                card_data={
                    "number": "4532000000000000",
                    "holder": "TEST",
                    "expiration": "12/28",
                    "cvv": "123"
                }
            )

        with patch.object(payment_service.getnet, 'create_credit_card_payment',
                         new_callable=AsyncMock, return_value=getnet_response):
            getnet_result = await payment_service.create_payment(
                gateway=PaymentGateway.GETNET,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("100.00"),
                order_id="RETRY-001",
                customer_data={"name": "Test", "cpf": "12345678900"},
                card_data={
                    "number": "5555555555555555",
                    "holder": "TEST",
                    "expiration": "12/28",
                    "cvv": "123"
                }
            )

        # Validações
        assert cielo_result["status"] == PaymentStatus.DENIED
        assert getnet_result["status"] == PaymentStatus.CAPTURED

    @pytest.mark.asyncio
    async def test_pix_all_supported_gateways(self, payment_service):
        """PIX em todos os gateways que suportam"""

        # GetNet PIX
        getnet_mock = {
            "payment_id": "pix-gn",
            "status": "PENDING",
            "amount": 10000,
            "qr_code": "00020126580014BR.GOV.BCB.PIXGN"
        }

        # MercadoPago PIX
        mp_mock = {
            "id": 123,
            "status": "pending",
            "transaction_amount": 100.00,
            "qr_code": "00020126580014BR.GOV.BCB.PIXMP",
            "valor": Decimal("100.00")
        }

        with patch.object(payment_service.getnet, 'create_pix_payment',
                         new_callable=AsyncMock, return_value=getnet_mock):
            gn_result = await payment_service.create_payment(
                gateway=PaymentGateway.GETNET,
                payment_method=PaymentMethod.PIX,
                amount=Decimal("100.00"),
                order_id="PIX-GN",
                customer_data={"name": "Test", "cpf": "12345678900"}
            )

        with patch.object(payment_service.mercadopago, 'criar_pagamento_pix',
                         new_callable=AsyncMock, return_value=mp_mock):
            mp_result = await payment_service.create_payment(
                gateway=PaymentGateway.MERCADOPAGO,
                payment_method=PaymentMethod.PIX,
                amount=Decimal("100.00"),
                order_id="PIX-MP",
                customer_data={"name": "Test", "email": "test@test.com"}
            )

        # Ambos retornam PIX pending
        assert gn_result["status"] == PaymentStatus.PENDING
        assert mp_result["status"] == PaymentStatus.PENDING
        assert gn_result["pix_qrcode"] is not None
        assert mp_result["pix_qrcode"] is not None
