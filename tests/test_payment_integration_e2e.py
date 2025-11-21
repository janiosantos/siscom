"""
Testes de Integração End-to-End com Payment Gateway Mock Service

Valida fluxos completos de pagamento com o microserviço mock rodando
"""

import pytest
import asyncio
import httpx
from decimal import Decimal
from typing import Dict, Any

from app.services.payment_gateway_service import (
    PaymentGatewayService,
    PaymentGateway,
    PaymentMethod,
    PaymentStatus
)
from app.integrations.cielo import CieloClient, CieloCardBrand
from app.integrations.getnet import GetNetClient
from app.integrations.mercadopago import MercadoPagoClient


# ============================================
# CONFIGURAÇÃO E FIXTURES
# ============================================

MOCK_SERVICE_URL = "http://localhost:8001"


@pytest.fixture
def cielo_client():
    """Cliente Cielo configurado para mock service"""
    client = CieloClient(
        merchant_id="mock-merchant-id",
        merchant_key="mock-merchant-key"
    )
    # Override URLs para apontar para mock service
    client.base_url = f"{MOCK_SERVICE_URL}/cielo"
    client.query_url = f"{MOCK_SERVICE_URL}/cielo"
    return client


@pytest.fixture
def getnet_client():
    """Cliente GetNet configurado para mock service"""
    client = GetNetClient(
        seller_id="mock-seller-id",
        client_id="mock-client-id",
        client_secret="mock-client-secret"
    )
    # Override base_url para apontar para mock service
    client.base_url = f"{MOCK_SERVICE_URL}/getnet"
    return client


@pytest.fixture
def mercadopago_client():
    """Cliente Mercado Pago configurado para mock service"""
    client = MercadoPagoClient(
        access_token="TEST-mock-access-token"
    )
    # Override base_url para apontar para mock service
    client.base_url = f"{MOCK_SERVICE_URL}/mercadopago"
    return client


@pytest.fixture
def payment_service(cielo_client, getnet_client, mercadopago_client):
    """PaymentGatewayService com clientes mockados"""
    service = PaymentGatewayService()
    service.cielo = cielo_client
    service.getnet = getnet_client
    service.mercadopago = mercadopago_client
    return service


@pytest.fixture(scope="module", autouse=True)
def verify_mock_service_running():
    """Verifica se mock service está rodando antes dos testes"""
    import requests
    try:
        response = requests.get(f"{MOCK_SERVICE_URL}/health", timeout=2)
        if response.status_code != 200:
            pytest.skip("Mock service não está rodando na porta 8001")
    except requests.exceptions.RequestException:
        pytest.skip("Mock service não está acessível em localhost:8001")


# ============================================
# TESTES E2E - CIELO CARTÃO DE CRÉDITO
# ============================================

class TestCieloE2EIntegration:
    """Testes end-to-end com Cielo"""

    @pytest.mark.asyncio
    async def test_cielo_credit_card_payment_full_flow(self, payment_service):
        """
        Teste E2E completo: criar pagamento → consultar → capturar
        """
        # 1. Criar pagamento com cartão de crédito
        result = await payment_service.create_payment(
            gateway=PaymentGateway.CIELO,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("150.00"),
            installments=3,
            customer_data={
                "name": "João Silva",
                "email": "joao@test.com",
                "cpf": "12345678900"
            },
            card_data={
                "number": "4532000000000000",
                "holder": "JOAO SILVA",
                "expiration": "12/2028",
                "cvv": "123",
                "brand": "visa"
            },
            order_id="E2E-TEST-001"
        )

        # Validar resposta de criação
        assert result["gateway"] == "cielo"
        assert result["status"] in [PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED]
        assert result["amount"] == 150.0
        assert result["installments"] == 3
        payment_id = result["payment_id"]
        assert payment_id is not None

        # 2. Consultar pagamento
        query_result = await payment_service.query_payment(
            gateway=PaymentGateway.CIELO,
            payment_id=payment_id
        )

        assert query_result["gateway"] == "cielo"
        assert query_result["payment_id"] == payment_id
        assert query_result["amount"] == 150.0

        # 3. Capturar pagamento (se estava apenas autorizado)
        if result["status"] == PaymentStatus.AUTHORIZED:
            capture_result = await payment_service.capture_payment(
                gateway=PaymentGateway.CIELO,
                payment_id=payment_id,
                amount=Decimal("150.00")
            )

            assert capture_result["gateway"] == "cielo"
            assert capture_result["status"] == PaymentStatus.CAPTURED

    @pytest.mark.asyncio
    async def test_cielo_credit_card_tokenization_flow(self, payment_service):
        """
        Teste E2E: tokenizar cartão → usar token para pagamento
        """
        # 1. Tokenizar cartão
        token_result = await payment_service.tokenize_card(
            gateway=PaymentGateway.CIELO,
            card_data={
                "number": "5555666677778884",
                "holder": "MARIA SANTOS",
                "expiration": "06/2027",
                "brand": "mastercard"
            }
        )

        assert token_result["gateway"] == "cielo"
        assert "card_token" in token_result
        assert token_result["last_digits"] == "8884"
        card_token = token_result["card_token"]

        # 2. Usar token para criar pagamento
        payment_result = await payment_service.create_payment(
            gateway=PaymentGateway.CIELO,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("99.90"),
            installments=1,
            customer_data={
                "name": "Maria Santos",
                "email": "maria@test.com"
            },
            card_data={
                "token": card_token,
                "cvv": "456",
                "brand": "mastercard"
            },
            order_id="E2E-TOKEN-001"
        )

        assert payment_result["gateway"] == "cielo"
        assert payment_result["amount"] == 99.9
        assert payment_result["status"] in [PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED]

    @pytest.mark.asyncio
    async def test_cielo_pix_payment_flow(self, cielo_client):
        """
        Teste E2E: criar PIX → obter QR Code → simular pagamento
        """
        # 1. Criar pagamento PIX
        pix_result = await cielo_client.create_pix_payment(
            amount=75.50,
            customer={"Name": "Pedro Costa"},
            order_id="E2E-PIX-001"
        )

        assert "Payment" in pix_result
        payment = pix_result["Payment"]
        assert payment["Type"] == "Pix"
        assert "QrCodeString" in payment
        assert "QrCodeBase64Image" in payment
        payment_id = payment["PaymentId"]

        # QR Code deve existir e seguir formato PIX
        qr_code = payment["QrCodeString"]
        assert qr_code.startswith("00020126")  # Formato PIX padrão

        # 2. Consultar status do PIX
        query_result = await cielo_client.query_payment(payment_id=payment_id)
        assert "Payment" in query_result
        assert query_result["Payment"]["PaymentId"] == payment_id

    @pytest.mark.asyncio
    async def test_cielo_payment_cancellation_flow(self, payment_service):
        """
        Teste E2E: criar pagamento → cancelar
        """
        # 1. Criar pagamento
        payment_result = await payment_service.create_payment(
            gateway=PaymentGateway.CIELO,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("200.00"),
            installments=1,
            customer_data={"name": "Ana Lima"},
            card_data={
                "number": "4532000000000000",
                "holder": "ANA LIMA",
                "expiration": "03/2026",
                "cvv": "789",
                "brand": "visa"
            },
            order_id="E2E-CANCEL-001"
        )

        payment_id = payment_result["payment_id"]

        # 2. Cancelar pagamento
        cancel_result = await payment_service.cancel_payment(
            gateway=PaymentGateway.CIELO,
            payment_id=payment_id
        )

        assert cancel_result["gateway"] == "cielo"
        assert cancel_result["status"] == PaymentStatus.CANCELLED


# ============================================
# TESTES E2E - GETNET COM OAUTH
# ============================================

class TestGetNetE2EIntegration:
    """Testes end-to-end com GetNet incluindo OAuth"""

    @pytest.mark.asyncio
    async def test_getnet_oauth_authentication_flow(self, getnet_client):
        """
        Teste E2E: obter token OAuth → usar em requisição
        """
        # 1. Obter token OAuth
        token_result = await getnet_client.get_oauth_token()

        assert "access_token" in token_result
        assert token_result["token_type"] == "Bearer"
        assert "expires_in" in token_result

        # Token deve estar armazenado no cliente
        assert getnet_client.access_token is not None
        assert getnet_client.access_token == token_result["access_token"]

    @pytest.mark.asyncio
    async def test_getnet_credit_card_payment_with_oauth(self, payment_service):
        """
        Teste E2E: autenticar → criar pagamento cartão de crédito
        """
        # OAuth é feito automaticamente no cliente GetNet
        result = await payment_service.create_payment(
            gateway=PaymentGateway.GETNET,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("250.00"),
            installments=6,
            customer_data={
                "name": "Carlos Pereira",
                "email": "carlos@test.com",
                "document_number": "98765432100"
            },
            card_data={
                "number": "5555666677778884",
                "holder": "CARLOS PEREIRA",
                "expiration": "09/2026",
                "cvv": "321",
                "brand": "mastercard"
            },
            order_id="E2E-GETNET-001"
        )

        assert result["gateway"] == "getnet"
        assert result["status"] in [PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED]
        assert result["amount"] == 250.0
        assert result["installments"] == 6

    @pytest.mark.asyncio
    async def test_getnet_debit_card_payment_flow(self, payment_service):
        """
        Teste E2E: pagamento com cartão de débito
        """
        result = await payment_service.create_payment(
            gateway=PaymentGateway.GETNET,
            payment_method=PaymentMethod.DEBIT_CARD,
            amount=Decimal("80.00"),
            installments=1,
            customer_data={
                "name": "Fernanda Costa",
                "email": "fernanda@test.com",
                "document_number": "11122233344"
            },
            card_data={
                "number": "4532000000000000",
                "holder": "FERNANDA COSTA",
                "expiration": "07/2025",
                "cvv": "456",
                "brand": "visa"
            },
            order_id="E2E-GETNET-DEBIT-001"
        )

        assert result["gateway"] == "getnet"
        assert result["amount"] == 80.0
        # Débito geralmente é aprovado imediatamente
        assert result["status"] in [PaymentStatus.CAPTURED, PaymentStatus.AUTHORIZED]

    @pytest.mark.asyncio
    async def test_getnet_pix_payment_flow(self, getnet_client):
        """
        Teste E2E: criar PIX GetNet → obter QR Code
        """
        pix_result = await getnet_client.create_pix_payment(
            amount=125.00,
            order_id="E2E-GETNET-PIX-001",
            customer_id="customer-123"
        )

        assert "payment_id" in pix_result
        assert "order_id" in pix_result
        assert pix_result["order_id"] == "E2E-GETNET-PIX-001"
        assert pix_result["status"] in ["PENDING", "WAITING"]

        # QR Code PIX
        if "qr_code" in pix_result:
            assert pix_result["qr_code"].startswith("00020126")

    @pytest.mark.asyncio
    async def test_getnet_card_tokenization_flow(self, payment_service):
        """
        Teste E2E: tokenizar cartão GetNet → usar token
        """
        # 1. Tokenizar cartão
        token_result = await payment_service.tokenize_card(
            gateway=PaymentGateway.GETNET,
            card_data={
                "number": "4532000000000000",
                "holder": "JOSE SANTOS",
                "expiration": "12/2027",
                "brand": "visa"
            },
            customer_data={
                "customer_id": "customer-456"
            }
        )

        assert token_result["gateway"] == "getnet"
        assert "card_token" in token_result
        assert token_result["last_digits"] == "0000"


# ============================================
# TESTES E2E - MERCADO PAGO
# ============================================

class TestMercadoPagoE2EIntegration:
    """Testes end-to-end com Mercado Pago"""

    @pytest.mark.asyncio
    async def test_mercadopago_pix_payment_flow(self, mercadopago_client):
        """
        Teste E2E: criar PIX Mercado Pago → obter QR Code
        """
        pix_result = await mercadopago_client.criar_pagamento_pix(
            valor=199.90,
            descricao="Teste E2E Mercado Pago",
            pagador_email="cliente@test.com",
            external_reference="E2E-MP-PIX-001"
        )

        assert "id" in pix_result
        assert pix_result["status"] in ["pending", "approved"]

        # QR Code deve estar presente
        if "qr_code" in pix_result:
            assert len(pix_result["qr_code"]) > 0


# ============================================
# TESTES E2E - FLUXOS MISTOS
# ============================================

class TestMixedE2EFlows:
    """Testes de fluxos mistos entre diferentes gateways"""

    @pytest.mark.asyncio
    async def test_multiple_gateways_concurrent_payments(self, payment_service):
        """
        Teste E2E: criar pagamentos concorrentes em múltiplos gateways
        """
        # Criar 3 pagamentos simultaneamente
        cielo_task = payment_service.create_payment(
            gateway=PaymentGateway.CIELO,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("100.00"),
            installments=1,
            customer_data={"name": "Cliente 1"},
            card_data={
                "number": "4532000000000000",
                "holder": "CLIENTE UM",
                "expiration": "12/2025",
                "cvv": "123",
                "brand": "visa"
            },
            order_id="CONCURRENT-CIELO-001"
        )

        getnet_task = payment_service.create_payment(
            gateway=PaymentGateway.GETNET,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("200.00"),
            installments=2,
            customer_data={"name": "Cliente 2", "document_number": "12345678900"},
            card_data={
                "number": "5555666677778884",
                "holder": "CLIENTE DOIS",
                "expiration": "06/2026",
                "cvv": "456",
                "brand": "mastercard"
            },
            order_id="CONCURRENT-GETNET-001"
        )

        # Executar concorrentemente
        results = await asyncio.gather(cielo_task, getnet_task)

        # Validar ambos os resultados
        assert len(results) == 2
        assert results[0]["gateway"] == "cielo"
        assert results[1]["gateway"] == "getnet"
        assert all(r["status"] in [PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED] for r in results)

    @pytest.mark.asyncio
    async def test_payment_lifecycle_complete_flow(self, payment_service):
        """
        Teste E2E: ciclo completo de vida de um pagamento
        criar → consultar → capturar → consultar novamente → cancelar
        """
        # 1. Criar pagamento (autorizado, não capturado)
        create_result = await payment_service.create_payment(
            gateway=PaymentGateway.CIELO,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("300.00"),
            installments=1,
            customer_data={"name": "Lifecycle Test"},
            card_data={
                "number": "4532000000000000",
                "holder": "LIFECYCLE TEST",
                "expiration": "12/2025",
                "cvv": "123",
                "brand": "visa"
            },
            order_id="LIFECYCLE-001"
        )

        payment_id = create_result["payment_id"]
        assert create_result["status"] in [PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED]

        # 2. Consultar status inicial
        query1 = await payment_service.query_payment(
            gateway=PaymentGateway.CIELO,
            payment_id=payment_id
        )
        assert query1["payment_id"] == payment_id

        # 3. Se autorizado, capturar
        if create_result["status"] == PaymentStatus.AUTHORIZED:
            capture_result = await payment_service.capture_payment(
                gateway=PaymentGateway.CIELO,
                payment_id=payment_id,
                amount=Decimal("300.00")
            )
            assert capture_result["status"] == PaymentStatus.CAPTURED

            # 4. Consultar após captura
            query2 = await payment_service.query_payment(
                gateway=PaymentGateway.CIELO,
                payment_id=payment_id
            )
            assert query2["payment_id"] == payment_id

        # 5. Cancelar pagamento
        cancel_result = await payment_service.cancel_payment(
            gateway=PaymentGateway.CIELO,
            payment_id=payment_id
        )
        assert cancel_result["status"] == PaymentStatus.CANCELLED


# ============================================
# TESTES E2E - CASOS DE ERRO
# ============================================

class TestE2EErrorHandling:
    """Testes de tratamento de erros end-to-end"""

    @pytest.mark.asyncio
    async def test_invalid_card_number(self, payment_service):
        """
        Teste E2E: cartão com número inválido deve falhar
        """
        with pytest.raises(Exception):  # Pode ser ValidationException ou BusinessRuleException
            await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("100.00"),
                installments=1,
                customer_data={"name": "Test"},
                card_data={
                    "number": "1234",  # Número inválido
                    "holder": "TEST",
                    "expiration": "12/2025",
                    "cvv": "123",
                    "brand": "visa"
                },
                order_id="ERROR-001"
            )

    @pytest.mark.asyncio
    async def test_query_nonexistent_payment(self, cielo_client):
        """
        Teste E2E: consultar pagamento inexistente
        """
        try:
            result = await cielo_client.query_payment(payment_id="nonexistent-id-999")
            # Se não lançar exceção, deve retornar 404 ou similar
            assert result is None or "error" in result
        except Exception as e:
            # Esperado: erro ao consultar pagamento inexistente
            assert "404" in str(e) or "not found" in str(e).lower()


# ============================================
# TESTES E2E - VALIDAÇÃO DE DADOS
# ============================================

class TestE2EDataValidation:
    """Testes de validação de dados nas requisições"""

    @pytest.mark.asyncio
    async def test_minimum_amount_validation(self, payment_service):
        """
        Teste E2E: validar valor mínimo de pagamento
        """
        # Valor muito baixo pode ser rejeitado
        result = await payment_service.create_payment(
            gateway=PaymentGateway.CIELO,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("0.01"),  # 1 centavo
            installments=1,
            customer_data={"name": "Test"},
            card_data={
                "number": "4532000000000000",
                "holder": "TEST",
                "expiration": "12/2025",
                "cvv": "123",
                "brand": "visa"
            },
            order_id="MIN-AMOUNT-001"
        )

        # Deve criar ou rejeitar de forma controlada
        assert "status" in result
        assert "gateway" in result

    @pytest.mark.asyncio
    async def test_maximum_installments_validation(self, payment_service):
        """
        Teste E2E: validar número máximo de parcelas
        """
        result = await payment_service.create_payment(
            gateway=PaymentGateway.CIELO,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("1200.00"),
            installments=12,  # Máximo permitido
            customer_data={"name": "Test"},
            card_data={
                "number": "4532000000000000",
                "holder": "TEST",
                "expiration": "12/2025",
                "cvv": "123",
                "brand": "visa"
            },
            order_id="MAX-INSTALL-001"
        )

        assert result["installments"] == 12
        assert result["status"] in [PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED]
