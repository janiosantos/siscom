"""
Testes de integração para Payment Gateway Service

Valida integração com:
- Cielo
- GetNet
- Mercado Pago

Usa mocks realistas que simulam comportamento dos SDKs reais
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.payment_gateway_service import (
    PaymentGatewayService,
    PaymentGateway,
    PaymentMethod,
    PaymentStatus
)
from app.core.exceptions import BusinessRuleException
from tests.mocks.payment_gateway_mock import PaymentGatewayMock


@pytest.fixture
def gateway_mock():
    """Fixture do mock de gateways"""
    mock = PaymentGatewayMock()
    yield mock
    mock.reset()


@pytest.fixture
def payment_service():
    """Fixture do serviço de pagamento"""
    service = PaymentGatewayService()
    service.initialize_mercadopago(
        access_token="TEST-123456789",
        public_key="TEST-PUB-123456789"
    )
    return service


# ============================================
# TESTES CIELO
# ============================================

class TestCieloIntegration:
    """Testes de integração com Cielo"""

    @pytest.mark.asyncio
    async def test_cielo_credit_card_payment_success(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de pagamento com cartão de crédito na Cielo - sucesso"""

        # Mock da chamada para Cielo
        mock_response = gateway_mock.cielo_create_card_payment(
            amount=150.00,
            installments=3,
            merchant_order_id="ORDER-001",
            customer_name="João Silva",
            capture=True
        )

        with patch.object(
            payment_service.cielo,
            'create_card_payment',
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
        assert result["payment_id"] is not None
        assert result["transaction_id"] is not None
        assert result["authorization_code"] is not None

    @pytest.mark.asyncio
    async def test_cielo_credit_card_payment_pre_authorization(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de pré-autorização (sem captura imediata) na Cielo"""

        mock_response = gateway_mock.cielo_create_card_payment(
            amount=200.00,
            installments=1,
            merchant_order_id="ORDER-002",
            capture=False  # Pré-autorização
        )

        with patch.object(
            payment_service.cielo,
            'create_card_payment',
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
                    "cvv": "123",
                    "brand": "Visa"
                },
                installments=1,
                capture=False  # Pré-autorização
            )

        # Validações
        assert result["status"] == PaymentStatus.AUTHORIZED
        assert result["captured"] is False
        assert result["amount"] == 200.00

    @pytest.mark.asyncio
    async def test_cielo_capture_pre_authorized_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de captura de pagamento pré-autorizado na Cielo"""

        # 1. Cria pagamento pré-autorizado
        create_response = gateway_mock.cielo_create_card_payment(
            amount=300.00,
            capture=False
        )
        payment_id = create_response["PaymentId"]

        # 2. Captura pagamento
        capture_response = gateway_mock.cielo_capture_payment(payment_id)

        with patch.object(
            payment_service.cielo,
            'capture_payment',
            new_callable=AsyncMock,
            return_value=capture_response
        ):
            result = await payment_service.capture_payment(
                gateway=PaymentGateway.CIELO,
                payment_id=payment_id,
                amount=Decimal("300.00")
            )

        # Validações
        assert result["status"] == PaymentStatus.CAPTURED
        assert result["captured"] is True

    @pytest.mark.asyncio
    async def test_cielo_cancel_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de cancelamento de pagamento na Cielo"""

        # 1. Cria pagamento
        create_response = gateway_mock.cielo_create_card_payment(
            amount=100.00,
            capture=True
        )
        payment_id = create_response["PaymentId"]

        # 2. Cancela pagamento
        cancel_response = gateway_mock.cielo_cancel_payment(payment_id)

        with patch.object(
            payment_service.cielo,
            'cancel_payment',
            new_callable=AsyncMock,
            return_value=cancel_response
        ):
            result = await payment_service.cancel_payment(
                gateway=PaymentGateway.CIELO,
                payment_id=payment_id
            )

        # Validações
        assert result["status"] == PaymentStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cielo_pix_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de pagamento PIX na Cielo"""

        mock_response = gateway_mock.cielo_create_pix_payment(
            amount=250.00,
            merchant_order_id="ORDER-PIX-001",
            customer_name="Pedro Costa"
        )

        with patch.object(
            payment_service.cielo,
            'create_pix_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.PIX,
                amount=Decimal("250.00"),
                order_id="ORDER-PIX-001",
                customer_data={"name": "Pedro Costa"}
            )

        # Validações
        assert result["gateway"] == "cielo"
        assert result["status"] == PaymentStatus.PENDING
        assert result["pix_qrcode"] is not None
        assert "00020126" in result["pix_qrcode"]  # Início do QR Code PIX padrão

    @pytest.mark.asyncio
    async def test_cielo_query_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de consulta de pagamento na Cielo"""

        # 1. Cria pagamento
        create_response = gateway_mock.cielo_create_card_payment(amount=100.00)
        payment_id = create_response["PaymentId"]

        # 2. Consulta pagamento
        query_response = gateway_mock.cielo_query_payment(payment_id)

        with patch.object(
            payment_service.cielo,
            'query_payment',
            new_callable=AsyncMock,
            return_value=query_response
        ):
            result = await payment_service.query_payment(
                gateway=PaymentGateway.CIELO,
                payment_id=payment_id
            )

        # Validações
        assert result["payment_id"] == payment_id
        assert result["gateway"] == "cielo"


# ============================================
# TESTES GETNET
# ============================================

class TestGetNetIntegration:
    """Testes de integração com GetNet"""

    @pytest.mark.asyncio
    async def test_getnet_credit_card_payment_success(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de pagamento com cartão de crédito na GetNet - sucesso"""

        mock_response = gateway_mock.getnet_create_card_payment(
            amount=180.00,
            installments=2,
            order_id="ORDER-GN-001",
            customer_name="Ana Oliveira",
            customer_document="12345678900",
            payment_type="credit"
        )

        with patch.object(
            payment_service.getnet,
            'create_card_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.GETNET,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("180.00"),
                order_id="ORDER-GN-001",
                customer_data={
                    "name": "Ana Oliveira",
                    "cpf": "12345678900"
                },
                card_data={
                    "number": "5555555555555555",
                    "holder": "ANA OLIVEIRA",
                    "expiration": "12/28",
                    "cvv": "123"
                },
                installments=2
            )

        # Validações
        assert result["gateway"] == "getnet"
        assert result["status"] == PaymentStatus.CAPTURED
        assert result["amount"] == 180.00
        assert result["installments"] == 2

    @pytest.mark.asyncio
    async def test_getnet_debit_card_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de pagamento com cartão de débito na GetNet"""

        mock_response = gateway_mock.getnet_create_card_payment(
            amount=75.00,
            installments=1,
            order_id="ORDER-GN-002",
            payment_type="debit"
        )

        with patch.object(
            payment_service.getnet,
            'create_card_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.GETNET,
                payment_method=PaymentMethod.DEBIT_CARD,
                amount=Decimal("75.00"),
                order_id="ORDER-GN-002",
                customer_data={
                    "name": "Carlos Silva",
                    "cpf": "98765432100"
                },
                card_data={
                    "number": "5555555555555555",
                    "holder": "CARLOS SILVA",
                    "expiration": "12/28",
                    "cvv": "123"
                },
                installments=1
            )

        # Validações
        assert result["status"] == PaymentStatus.CAPTURED
        assert result["installments"] == 1

    @pytest.mark.asyncio
    async def test_getnet_pix_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de pagamento PIX na GetNet"""

        mock_response = gateway_mock.getnet_create_pix_payment(
            amount=320.00,
            order_id="ORDER-GN-PIX-001",
            customer_name="Fernanda Lima",
            customer_document="11122233344"
        )

        with patch.object(
            payment_service.getnet,
            'create_pix_payment',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.GETNET,
                payment_method=PaymentMethod.PIX,
                amount=Decimal("320.00"),
                order_id="ORDER-GN-PIX-001",
                customer_data={
                    "name": "Fernanda Lima",
                    "cpf": "11122233344"
                }
            )

        # Validações
        assert result["gateway"] == "getnet"
        assert result["status"] == PaymentStatus.PENDING
        assert result["pix_qrcode"] is not None

    @pytest.mark.asyncio
    async def test_getnet_cancel_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de cancelamento na GetNet"""

        # 1. Cria pagamento
        create_response = gateway_mock.getnet_create_card_payment(amount=150.00)
        payment_id = create_response["payment_id"]

        # 2. Cancela
        cancel_response = gateway_mock.getnet_cancel_payment(payment_id)

        with patch.object(
            payment_service.getnet,
            'cancel_payment',
            new_callable=AsyncMock,
            return_value=cancel_response
        ):
            result = await payment_service.cancel_payment(
                gateway=PaymentGateway.GETNET,
                payment_id=payment_id
            )

        # Validações
        assert result["status"] == PaymentStatus.CANCELLED


# ============================================
# TESTES MERCADO PAGO
# ============================================

class TestMercadoPagoIntegration:
    """Testes de integração com Mercado Pago"""

    @pytest.mark.asyncio
    async def test_mercadopago_pix_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de pagamento PIX no Mercado Pago"""

        mock_response = gateway_mock.mercadopago_create_pix_payment(
            valor=Decimal("450.00"),
            descricao="Pedido #MP-001",
            email_pagador="cliente@email.com",
            external_reference="MP-001"
        )

        with patch.object(
            payment_service.mercadopago,
            'criar_pagamento_pix',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.MERCADOPAGO,
                payment_method=PaymentMethod.PIX,
                amount=Decimal("450.00"),
                order_id="MP-001",
                customer_data={
                    "name": "Roberto Santos",
                    "email": "cliente@email.com"
                }
            )

        # Validações
        assert result["gateway"] == "mercadopago"
        assert result["status"] == PaymentStatus.PENDING
        assert result["amount"] == 450.00
        assert result["pix_qrcode"] is not None

    @pytest.mark.asyncio
    async def test_mercadopago_credit_card_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de pagamento com cartão no Mercado Pago"""

        mock_response = gateway_mock.mercadopago_create_card_payment(
            valor=Decimal("380.00"),
            parcelas=6,
            descricao="Pedido #MP-002",
            email_pagador="cliente2@email.com",
            card_token="CARD_TOKEN_123",
            external_reference="MP-002"
        )

        with patch.object(
            payment_service.mercadopago,
            'criar_pagamento_cartao',
            new_callable=AsyncMock,
            return_value=mock_response
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.MERCADOPAGO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("380.00"),
                order_id="MP-002",
                customer_data={
                    "name": "Lucia Ferreira",
                    "email": "cliente2@email.com"
                },
                card_data={
                    "token": "CARD_TOKEN_123"
                },
                installments=6
            )

        # Validações
        assert result["gateway"] == "mercadopago"
        assert result["status"] == PaymentStatus.CAPTURED
        assert result["amount"] == 380.00
        assert result["installments"] == 6

    @pytest.mark.asyncio
    async def test_mercadopago_cancel_payment(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de cancelamento no Mercado Pago"""

        # 1. Cria pagamento
        create_response = gateway_mock.mercadopago_create_card_payment(
            valor=Decimal("200.00"),
            parcelas=1,
            descricao="Teste"
        )
        payment_id = str(create_response["id"])

        # 2. Cancela
        cancel_response = gateway_mock.mercadopago_cancel_payment(int(payment_id))

        with patch.object(
            payment_service.mercadopago,
            'cancelar_pagamento',
            new_callable=AsyncMock,
            return_value=cancel_response
        ):
            result = await payment_service.cancel_payment(
                gateway=PaymentGateway.MERCADOPAGO,
                payment_id=payment_id
            )

        # Validações
        assert result["status"] == PaymentStatus.CANCELLED


# ============================================
# TESTES DE VALIDAÇÃO
# ============================================

class TestPaymentValidations:
    """Testes de validações de negócio"""

    @pytest.mark.asyncio
    async def test_minimum_amount_validation(self, payment_service: PaymentGatewayService):
        """Teste de validação de valor mínimo"""

        with pytest.raises(BusinessRuleException, match="Valor mínimo"):
            await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("0.00"),  # Valor inválido
                order_id="ORDER-001",
                customer_data={"name": "Teste"},
                card_data={"number": "123"}
            )

    @pytest.mark.asyncio
    async def test_installments_validation(self, payment_service: PaymentGatewayService):
        """Teste de validação de parcelas"""

        with pytest.raises(BusinessRuleException, match="parcelas"):
            await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("100.00"),
                order_id="ORDER-001",
                customer_data={"name": "Teste"},
                card_data={"number": "123"},
                installments=15  # Acima do limite (12)
            )

    @pytest.mark.asyncio
    async def test_card_data_required_for_card_payment(self, payment_service: PaymentGatewayService):
        """Teste de obrigatoriedade dos dados do cartão"""

        with pytest.raises(BusinessRuleException, match="Dados do cartão"):
            await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("100.00"),
                order_id="ORDER-001",
                customer_data={"name": "Teste"},
                card_data=None  # Dados do cartão obrigatórios
            )


# ============================================
# TESTES DE CENÁRIOS COMPLEXOS
# ============================================

class TestComplexScenarios:
    """Testes de cenários complexos e edge cases"""

    @pytest.mark.asyncio
    async def test_multiple_gateways_same_order(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de múltiplos gateways para mesma ordem (retry)"""

        # Tenta Cielo (falha simulada)
        cielo_mock = gateway_mock.cielo_create_card_payment(amount=100.00)
        cielo_mock["Status"] = "3"  # Negada

        # Tenta GetNet (sucesso)
        getnet_mock = gateway_mock.getnet_create_card_payment(amount=100.00)

        with patch.object(payment_service.cielo, 'create_card_payment', new_callable=AsyncMock, return_value=cielo_mock):
            cielo_result = await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("100.00"),
                order_id="ORDER-RETRY-001",
                customer_data={"name": "Teste"},
                card_data={"number": "123", "holder": "TEST", "expiration": "12/28", "cvv": "123"}
            )

        with patch.object(payment_service.getnet, 'create_card_payment', new_callable=AsyncMock, return_value=getnet_mock):
            getnet_result = await payment_service.create_payment(
                gateway=PaymentGateway.GETNET,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("100.00"),
                order_id="ORDER-RETRY-001",
                customer_data={"name": "Teste", "cpf": "12345678900"},
                card_data={"number": "123", "holder": "TEST", "expiration": "12/28", "cvv": "123"}
            )

        # Validações: Cielo falhou, GetNet sucedeu
        assert cielo_result["status"] == PaymentStatus.DENIED
        assert getnet_result["status"] == PaymentStatus.CAPTURED

    @pytest.mark.asyncio
    async def test_pix_payment_simulation_all_gateways(self, payment_service: PaymentGatewayService, gateway_mock: PaymentGatewayMock):
        """Teste de PIX em todos os gateways"""

        gateways_to_test = [
            (PaymentGateway.CIELO, "cielo"),
            (PaymentGateway.GETNET, "getnet"),
            (PaymentGateway.MERCADOPAGO, "mercadopago")
        ]

        for gateway, gateway_str in gateways_to_test:
            # Mock específico de cada gateway
            if gateway == PaymentGateway.CIELO:
                mock_response = gateway_mock.cielo_create_pix_payment(amount=100.00)
                with patch.object(payment_service.cielo, 'create_pix_payment', new_callable=AsyncMock, return_value=mock_response):
                    result = await payment_service.create_payment(
                        gateway=gateway,
                        payment_method=PaymentMethod.PIX,
                        amount=Decimal("100.00"),
                        order_id=f"ORDER-PIX-{gateway_str.upper()}",
                        customer_data={"name": "Teste"}
                    )
            elif gateway == PaymentGateway.GETNET:
                mock_response = gateway_mock.getnet_create_pix_payment(amount=100.00)
                with patch.object(payment_service.getnet, 'create_pix_payment', new_callable=AsyncMock, return_value=mock_response):
                    result = await payment_service.create_payment(
                        gateway=gateway,
                        payment_method=PaymentMethod.PIX,
                        amount=Decimal("100.00"),
                        order_id=f"ORDER-PIX-{gateway_str.upper()}",
                        customer_data={"name": "Teste", "cpf": "12345678900"}
                    )
            else:  # MERCADOPAGO
                mock_response = gateway_mock.mercadopago_create_pix_payment(
                    valor=Decimal("100.00"),
                    descricao="Teste"
                )
                with patch.object(payment_service.mercadopago, 'criar_pagamento_pix', new_callable=AsyncMock, return_value=mock_response):
                    result = await payment_service.create_payment(
                        gateway=gateway,
                        payment_method=PaymentMethod.PIX,
                        amount=Decimal("100.00"),
                        order_id=f"ORDER-PIX-{gateway_str.upper()}",
                        customer_data={"name": "Teste", "email": "test@test.com"}
                    )

            # Validações comuns
            assert result["gateway"] == gateway_str
            assert result["status"] == PaymentStatus.PENDING
            assert result["pix_qrcode"] is not None
            assert "00020126" in result["pix_qrcode"]  # QR Code PIX válido
