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

        # Mock da resposta da Cielo (deve incluir Payment object)
        mock_response = {
            "Payment": {
                "PaymentId": "abc-123-def",
                "Tid": "TID123456",
                "Status": 2,  # Capturada (int, não string)
                "Amount": 15000,  # R$ 150,00 em centavos
                "Installments": 3,
                "Capture": True,
                "AuthorizationCode": "AUTH123456",
                "ReturnCode": "4",
                "ReturnMessage": "Operacao realizada com sucesso"
            }
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
            "Payment": {
                "PaymentId": "pre-auth-123",
                "Status": 1,  # Autorizada (int)
                "Amount": 20000,
                "Installments": 1,
                "Capture": False,
                "AuthorizationCode": "AUTH789"
            }
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
            "Payment": {
                "PaymentId": "cap-123",
                "Status": 2,  # Capturada (int)
                "Capture": True,
                "Amount": 30000
            }
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
            "Payment": {
                "PaymentId": "cancel-123",
                "Status": 10,  # Cancelada (int)
                "Amount": 10000
            }
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
            "Payment": {
                "PaymentId": "query-123",
                "Status": 2,  # int
                "Amount": 15000
            }
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
            "Payment": {
                "PaymentId": "denied-123",
                "Status": 3,  # Negada (int)
                "Amount": 10000,
                "ReturnCode": "05"
            }
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


# ============================================
# TESTES DE MAPEAMENTO DE STATUS
# ============================================

class TestStatusMapping:
    """Testes de mapeamento de status entre gateways"""

    def test_map_cielo_status(self, payment_service):
        """Mapear todos os status Cielo"""
        assert payment_service._map_cielo_status("0") == PaymentStatus.PENDING
        assert payment_service._map_cielo_status("1") == PaymentStatus.AUTHORIZED
        assert payment_service._map_cielo_status("2") == PaymentStatus.CAPTURED
        assert payment_service._map_cielo_status("3") == PaymentStatus.DENIED
        assert payment_service._map_cielo_status("10") == PaymentStatus.CANCELLED
        assert payment_service._map_cielo_status("11") == PaymentStatus.REFUNDED
        assert payment_service._map_cielo_status("12") == PaymentStatus.PENDING
        assert payment_service._map_cielo_status("13") == PaymentStatus.CANCELLED
        # Status desconhecido
        assert payment_service._map_cielo_status("99") == PaymentStatus.PENDING

    def test_map_getnet_status(self, payment_service):
        """Mapear todos os status GetNet"""
        assert payment_service._map_getnet_status("PENDING") == PaymentStatus.PENDING
        assert payment_service._map_getnet_status("AUTHORIZED") == PaymentStatus.AUTHORIZED
        assert payment_service._map_getnet_status("APPROVED") == PaymentStatus.CAPTURED
        assert payment_service._map_getnet_status("DENIED") == PaymentStatus.DENIED
        assert payment_service._map_getnet_status("CANCELED") == PaymentStatus.CANCELLED
        assert payment_service._map_getnet_status("REFUNDED") == PaymentStatus.REFUNDED
        # Status desconhecido (ERROR, UNKNOWN, etc) mapeia para PENDING
        assert payment_service._map_getnet_status("ERROR") == PaymentStatus.PENDING
        assert payment_service._map_getnet_status("UNKNOWN") == PaymentStatus.PENDING

    def test_map_mercadopago_status(self, payment_service):
        """Mapear todos os status Mercado Pago"""
        assert payment_service._map_mercadopago_status("pending") == PaymentStatus.PENDING
        assert payment_service._map_mercadopago_status("approved") == PaymentStatus.CAPTURED
        assert payment_service._map_mercadopago_status("authorized") == PaymentStatus.AUTHORIZED
        assert payment_service._map_mercadopago_status("rejected") == PaymentStatus.DENIED
        assert payment_service._map_mercadopago_status("cancelled") == PaymentStatus.CANCELLED
        assert payment_service._map_mercadopago_status("refunded") == PaymentStatus.REFUNDED
        # Status desconhecido
        assert payment_service._map_mercadopago_status("unknown") == PaymentStatus.PENDING


# ============================================
# TESTES DE NORMALIZAÇÃO DE RESPOSTAS
# ============================================

class TestResponseNormalization:
    """Testes de normalização de respostas dos gateways"""

    def test_normalize_cielo_response(self, payment_service):
        """Normalizar resposta Cielo com Payment object"""
        raw_response = {
            "Payment": {
                "PaymentId": "cielo-abc-123",
                "Tid": "TID987654",
                "Status": 2,
                "Amount": 25000,  # R$ 250,00 em centavos
                "Installments": 5,
                "Capture": True,
                "AuthorizationCode": "AUTH-XYZ",
                "QrCodeString": None
            }
        }

        normalized = payment_service._normalize_response(
            PaymentGateway.CIELO,
            raw_response
        )

        assert normalized["gateway"] == "cielo"
        assert normalized["payment_id"] == "cielo-abc-123"
        assert normalized["transaction_id"] == "TID987654"
        assert normalized["status"] == PaymentStatus.CAPTURED
        assert normalized["amount"] == 250.0
        assert normalized["installments"] == 5
        assert normalized["captured"] is True
        assert normalized["authorization_code"] == "AUTH-XYZ"
        assert "created_at" in normalized

    def test_normalize_getnet_response(self, payment_service):
        """Normalizar resposta GetNet"""
        raw_response = {
            "payment_id": "getnet-xyz-789",
            "order_id": "ORDER-999",
            "status": "APPROVED",
            "amount": 18500,
            "installments": 3,
            "authorization_code": "GN-AUTH-123",
            "qr_code": None
        }

        normalized = payment_service._normalize_response(
            PaymentGateway.GETNET,
            raw_response
        )

        assert normalized["gateway"] == "getnet"
        assert normalized["payment_id"] == "getnet-xyz-789"
        assert normalized["transaction_id"] == "ORDER-999"
        assert normalized["status"] == PaymentStatus.CAPTURED
        assert normalized["amount"] == 185.0
        assert normalized["installments"] == 3

    def test_normalize_mercadopago_response(self, payment_service):
        """Normalizar resposta Mercado Pago"""
        raw_response = {
            "id": 987654321,
            "external_reference": "EXT-REF-001",
            "status": "approved",
            "valor": Decimal("320.00"),
            "installments": 6,
            "qr_code": "MP-QR-CODE-123"
        }

        normalized = payment_service._normalize_response(
            PaymentGateway.MERCADOPAGO,
            raw_response
        )

        assert normalized["gateway"] == "mercadopago"
        assert normalized["payment_id"] == "987654321"
        assert normalized["transaction_id"] == "EXT-REF-001"
        assert normalized["status"] == PaymentStatus.CAPTURED
        assert normalized["amount"] == 320.0
        assert normalized["pix_qrcode"] == "MP-QR-CODE-123"


# ============================================
# TESTES DE TOKENIZAÇÃO
# ============================================

class TestTokenization:
    """Testes de tokenização de cartão"""

    @pytest.mark.asyncio
    async def test_tokenize_cielo_card_success(self, payment_service):
        """Tokenizar cartão na Cielo com sucesso"""
        # CieloClient.tokenize_card retorna diretamente a string do token
        mock_token = "TOKEN-CIELO-ABC123"

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
                    "holder": "JOAO SILVA",
                    "expiration": "12/2028",
                    "brand": "visa"
                }
            )

        assert result["gateway"] == "cielo"
        assert result["card_token"] == "TOKEN-CIELO-ABC123"
        assert result["last_digits"] == "0000"
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_tokenize_getnet_card_success(self, payment_service):
        """Tokenizar cartão na GetNet com sucesso"""
        # GetNetClient.tokenize_card retorna diretamente a string do token
        mock_token = "TOKEN-GETNET-XYZ789"

        with patch.object(
            payment_service.getnet,
            'tokenize_card',
            new_callable=AsyncMock,
            return_value=mock_token
        ):
            result = await payment_service.tokenize_card(
                gateway=PaymentGateway.GETNET,
                card_data={
                    "number": "5555555555555555"
                },
                customer_data={
                    "customer_id": "CUST-123"
                }
            )

        assert result["card_token"] == "TOKEN-GETNET-XYZ789"
        assert result["last_digits"] == "5555"

    @pytest.mark.asyncio
    async def test_tokenize_card_no_number(self, payment_service):
        """Deve exigir número do cartão"""
        from app.core.exceptions import ValidationException

        with pytest.raises(ValidationException, match="Número do cartão"):
            await payment_service.tokenize_card(
                gateway=PaymentGateway.CIELO,
                card_data={
                    "holder": "TEST",
                    "expiration": "12/2028"
                }
            )

    @pytest.mark.asyncio
    async def test_tokenize_cielo_missing_required(self, payment_service):
        """Cielo requer holder, expiration e brand"""
        from app.core.exceptions import ValidationException

        with pytest.raises(ValidationException, match="Campos obrigatórios"):
            await payment_service.tokenize_card(
                gateway=PaymentGateway.CIELO,
                card_data={
                    "number": "4532000000000000"
                    # Faltando: holder, expiration, brand
                }
            )

    @pytest.mark.asyncio
    async def test_tokenize_unsupported_gateway(self, payment_service):
        """Gateway não suporta tokenização"""
        with pytest.raises(BusinessRuleException, match="não suporta tokenização"):
            await payment_service.tokenize_card(
                gateway=PaymentGateway.MERCADOPAGO,
                card_data={"number": "4532000000000000"}
            )


# ============================================
# TESTES DE DÉBITO
# ============================================

class TestDebitCards:
    """Testes específicos de cartão de débito"""

    @pytest.mark.asyncio
    async def test_cielo_debit_card_with_return_url(self, payment_service):
        """Débito Cielo com URL de retorno"""
        mock_response = {
            "Payment": {
                "PaymentId": "debit-123",
                "Status": 1,  # Autorizado
                "Amount": 8000,
                "AuthenticationUrl": "https://auth.cielo.com.br/..."
            }
        }

        with patch.object(
            payment_service.cielo,
            'create_debit_card_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.DEBIT_CARD,
                amount=Decimal("80.00"),
                order_id="DEBIT-001",
                customer_data={"name": "Test"},
                card_data={
                    "number": "4532111111111111",
                    "holder": "TEST",
                    "expiration": "06/2027",
                    "cvv": "456",
                    "brand": "visa"
                },
                metadata={"return_url": "https://loja.com/retorno"}
            )

        assert result["status"] == PaymentStatus.AUTHORIZED

    @pytest.mark.asyncio
    async def test_getnet_debit_card(self, payment_service):
        """Débito GetNet"""
        mock_response = {
            "payment_id": "debit-gn-456",
            "status": "APPROVED",
            "amount": 12000
        }

        with patch.object(
            payment_service.getnet,
            'create_debit_card_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.GETNET,
                payment_method=PaymentMethod.DEBIT_CARD,
                amount=Decimal("120.00"),
                order_id="DEBIT-GN-001",
                customer_data={"name": "Test", "cpf": "12345678900"},
                card_data={
                    "number": "5555666677778888",
                    "holder": "TEST DEBIT",
                    "expiration": "09/2026",
                    "cvv": "789",
                    "brand": "mastercard"
                }
            )

        assert result["status"] == PaymentStatus.CAPTURED


# ============================================
# TESTES DE BANDEIRAS DE CARTÃO
# ============================================

class TestCardBrands:
    """Testes de diferentes bandeiras de cartão"""

    @pytest.mark.asyncio
    async def test_visa_card(self, payment_service):
        """Pagamento com Visa"""
        mock_response = {
            "Payment": {"PaymentId": "visa-123", "Status": 2, "Amount": 10000}
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
                amount=Decimal("100.00"),
                order_id="VISA-001",
                customer_data={"name": "Test"},
                card_data={
                    "number": "4532000000000000",
                    "holder": "TEST",
                    "expiration": "12/2028",
                    "cvv": "123",
                    "brand": "visa"
                }
            )

        assert result["status"] == PaymentStatus.CAPTURED

    @pytest.mark.asyncio
    async def test_mastercard(self, payment_service):
        """Pagamento com Mastercard"""
        mock_response = {
            "Payment": {"PaymentId": "mc-456", "Status": 2, "Amount": 15000}
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
                order_id="MC-001",
                customer_data={"name": "Test"},
                card_data={
                    "number": "5555555555555555",
                    "holder": "TEST",
                    "expiration": "12/2028",
                    "cvv": "456",
                    "brand": "mastercard"
                }
            )

        assert result["status"] == PaymentStatus.CAPTURED

    @pytest.mark.asyncio
    async def test_elo_card(self, payment_service):
        """Pagamento com Elo"""
        mock_response = {
            "Payment": {"PaymentId": "elo-789", "Status": 2, "Amount": 20000}
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
                order_id="ELO-001",
                customer_data={"name": "Test"},
                card_data={
                    "number": "6362970000457013",
                    "holder": "TEST",
                    "expiration": "12/2028",
                    "cvv": "789",
                    "brand": "elo"
                }
            )

        assert result["status"] == PaymentStatus.CAPTURED
