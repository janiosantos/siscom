"""
Testes para funcionalidade de webhooks de pagamento

Valida processamento de notificações dos gateways de pagamento
"""

import pytest
import json
import hmac
import hashlib
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

from app.services.payment_webhook_handler import (
    PaymentWebhookHandler,
    WebhookEvent,
    router
)
from app.services.payment_gateway_service import PaymentGateway, PaymentStatus
from app.core.exceptions import ValidationException, BusinessRuleException


# ============================================
# TESTES DO HANDLER DE WEBHOOKS
# ============================================

class TestWebhookHandler:
    """Testes da classe PaymentWebhookHandler"""

    @pytest.fixture
    def handler(self):
        """Fixture do handler"""
        return PaymentWebhookHandler()

    # ============================================
    # TESTES DE PROCESSAMENTO - CIELO
    # ============================================

    @pytest.mark.asyncio
    async def test_process_cielo_webhook_approved(self, handler):
        """Teste de webhook Cielo com pagamento aprovado"""
        payload = {
            "PaymentId": "cielo-payment-123",
            "ChangeType": 1,
            "Status": 2,  # Capturado
            "ReasonCode": 0
        }

        # Criar assinatura válida
        secret = "CIELO_WEBHOOK_SECRET"
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {"X-Cielo-Signature": signature}

        result = await handler.process_webhook(
            gateway=PaymentGateway.CIELO,
            payload=payload,
            headers=headers
        )

        assert result["gateway"] == "cielo"
        assert result["payment_id"] == "cielo-payment-123"
        assert result["status"] == PaymentStatus.CAPTURED
        assert result["event"] == WebhookEvent.PAYMENT_APPROVED

    @pytest.mark.asyncio
    async def test_process_cielo_webhook_denied(self, handler):
        """Teste de webhook Cielo com pagamento negado"""
        payload = {
            "PaymentId": "cielo-payment-456",
            "ChangeType": 1,
            "Status": 3,  # Negado
            "ReasonCode": 57
        }

        secret = "CIELO_WEBHOOK_SECRET"
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {"X-Cielo-Signature": signature}

        result = await handler.process_webhook(
            gateway=PaymentGateway.CIELO,
            payload=payload,
            headers=headers
        )

        assert result["status"] == PaymentStatus.DENIED
        assert result["event"] == WebhookEvent.PAYMENT_DENIED

    @pytest.mark.asyncio
    async def test_process_cielo_webhook_cancelled(self, handler):
        """Teste de webhook Cielo com cancelamento"""
        payload = {
            "PaymentId": "cielo-payment-789",
            "ChangeType": 1,
            "Status": 10,  # Cancelado
            "ReasonCode": 0
        }

        secret = "CIELO_WEBHOOK_SECRET"
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {"X-Cielo-Signature": signature}

        result = await handler.process_webhook(
            gateway=PaymentGateway.CIELO,
            payload=payload,
            headers=headers
        )

        assert result["status"] == PaymentStatus.CANCELLED
        assert result["event"] == WebhookEvent.PAYMENT_CANCELLED

    @pytest.mark.asyncio
    async def test_process_cielo_webhook_refunded(self, handler):
        """Teste de webhook Cielo com estorno"""
        payload = {
            "PaymentId": "cielo-payment-abc",
            "ChangeType": 1,
            "Status": 11,  # Estornado
            "ReasonCode": 0
        }

        secret = "CIELO_WEBHOOK_SECRET"
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {"X-Cielo-Signature": signature}

        result = await handler.process_webhook(
            gateway=PaymentGateway.CIELO,
            payload=payload,
            headers=headers
        )

        assert result["status"] == PaymentStatus.REFUNDED
        assert result["event"] == WebhookEvent.PAYMENT_REFUNDED

    # ============================================
    # TESTES DE PROCESSAMENTO - GETNET
    # ============================================

    @pytest.mark.asyncio
    async def test_process_getnet_webhook_approved(self, handler):
        """Teste de webhook GetNet com pagamento aprovado"""
        payload = {
            "notification_type": "payment",
            "status": "APPROVED",
            "payment_id": "getnet-payment-123",
            "order_id": "ORDER-001"
        }

        headers = {"Authorization": "Bearer valid-token"}

        result = await handler.process_webhook(
            gateway=PaymentGateway.GETNET,
            payload=payload,
            headers=headers
        )

        assert result["gateway"] == "getnet"
        assert result["payment_id"] == "getnet-payment-123"
        assert result["order_id"] == "ORDER-001"
        assert result["status"] == PaymentStatus.CAPTURED
        assert result["event"] == WebhookEvent.PAYMENT_APPROVED

    @pytest.mark.asyncio
    async def test_process_getnet_webhook_denied(self, handler):
        """Teste de webhook GetNet com pagamento negado"""
        payload = {
            "notification_type": "payment",
            "status": "DENIED",
            "payment_id": "getnet-payment-456",
            "order_id": "ORDER-002"
        }

        headers = {"Authorization": "Bearer valid-token"}

        result = await handler.process_webhook(
            gateway=PaymentGateway.GETNET,
            payload=payload,
            headers=headers
        )

        assert result["status"] == PaymentStatus.DENIED
        assert result["event"] == WebhookEvent.PAYMENT_DENIED

    @pytest.mark.asyncio
    async def test_process_getnet_webhook_canceled(self, handler):
        """Teste de webhook GetNet com cancelamento"""
        payload = {
            "notification_type": "payment",
            "status": "CANCELED",
            "payment_id": "getnet-payment-789",
            "order_id": "ORDER-003"
        }

        headers = {"Authorization": "Bearer valid-token"}

        result = await handler.process_webhook(
            gateway=PaymentGateway.GETNET,
            payload=payload,
            headers=headers
        )

        assert result["status"] == PaymentStatus.CANCELLED
        assert result["event"] == WebhookEvent.PAYMENT_CANCELLED

    # ============================================
    # TESTES DE PROCESSAMENTO - MERCADO PAGO
    # ============================================

    @pytest.mark.asyncio
    async def test_process_mercadopago_webhook(self, handler):
        """Teste de webhook Mercado Pago"""
        payload = {
            "action": "payment.updated",
            "data": {
                "id": "123456789"
            },
            "type": "payment"
        }

        headers = {
            "x-signature": "v1=abc123,v2=def456",
            "x-request-id": "unique-request-id"
        }

        result = await handler.process_webhook(
            gateway=PaymentGateway.MERCADOPAGO,
            payload=payload,
            headers=headers
        )

        assert result["gateway"] == "mercadopago"
        assert result["payment_id"] == "123456789"
        assert result["status"] == PaymentStatus.PENDING
        assert result["event"] == WebhookEvent.PAYMENT_PENDING
        assert result["requires_query"] is True
        assert result["action"] == "payment.updated"

    # ============================================
    # TESTES DE VALIDAÇÃO DE ASSINATURA
    # ============================================

    @pytest.mark.asyncio
    async def test_cielo_webhook_invalid_signature(self, handler):
        """Teste de webhook Cielo com assinatura inválida"""
        payload = {
            "PaymentId": "cielo-payment-123",
            "ChangeType": 1,
            "Status": 2
        }

        headers = {"X-Cielo-Signature": "invalid-signature"}

        with pytest.raises(ValidationException, match="Assinatura do webhook inválida"):
            await handler.process_webhook(
                gateway=PaymentGateway.CIELO,
                payload=payload,
                headers=headers
            )

    @pytest.mark.asyncio
    async def test_cielo_webhook_missing_signature(self, handler):
        """Teste de webhook Cielo sem assinatura"""
        payload = {
            "PaymentId": "cielo-payment-123",
            "ChangeType": 1,
            "Status": 2
        }

        headers = {}  # Sem assinatura

        with pytest.raises(ValidationException, match="Assinatura do webhook inválida"):
            await handler.process_webhook(
                gateway=PaymentGateway.CIELO,
                payload=payload,
                headers=headers
            )

    @pytest.mark.asyncio
    async def test_getnet_webhook_invalid_auth(self, handler):
        """Teste de webhook GetNet com auth inválido"""
        payload = {
            "notification_type": "payment",
            "status": "APPROVED",
            "payment_id": "getnet-123"
        }

        headers = {"Authorization": "Invalid token"}  # Não começa com Bearer

        with pytest.raises(ValidationException, match="Assinatura do webhook inválida"):
            await handler.process_webhook(
                gateway=PaymentGateway.GETNET,
                payload=payload,
                headers=headers
            )

    @pytest.mark.asyncio
    async def test_getnet_webhook_missing_auth(self, handler):
        """Teste de webhook GetNet sem auth"""
        payload = {
            "notification_type": "payment",
            "status": "APPROVED",
            "payment_id": "getnet-123"
        }

        headers = {}  # Sem Authorization

        with pytest.raises(ValidationException, match="Assinatura do webhook inválida"):
            await handler.process_webhook(
                gateway=PaymentGateway.GETNET,
                payload=payload,
                headers=headers
            )

    @pytest.mark.asyncio
    async def test_mercadopago_webhook_missing_headers(self, handler):
        """Teste de webhook Mercado Pago sem headers necessários"""
        payload = {
            "action": "payment.updated",
            "data": {"id": "123"}
        }

        headers = {}  # Sem x-signature e x-request-id

        with pytest.raises(ValidationException, match="Assinatura do webhook inválida"):
            await handler.process_webhook(
                gateway=PaymentGateway.MERCADOPAGO,
                payload=payload,
                headers=headers
            )

    # ============================================
    # TESTES DE PROCESSAMENTO DE EVENTOS
    # ============================================

    @pytest.mark.asyncio
    async def test_handle_payment_approved_event(self, handler):
        """Teste de processamento de evento de pagamento aprovado"""
        payment_data = {
            "payment_id": "test-123",
            "gateway": "cielo",
            "status": PaymentStatus.CAPTURED
        }

        # Não deve lançar exceção
        await handler.handle_payment_event(
            event=WebhookEvent.PAYMENT_APPROVED,
            payment_data=payment_data
        )

    @pytest.mark.asyncio
    async def test_handle_payment_denied_event(self, handler):
        """Teste de processamento de evento de pagamento negado"""
        payment_data = {
            "payment_id": "test-456",
            "gateway": "getnet",
            "status": PaymentStatus.DENIED
        }

        await handler.handle_payment_event(
            event=WebhookEvent.PAYMENT_DENIED,
            payment_data=payment_data
        )

    @pytest.mark.asyncio
    async def test_handle_payment_cancelled_event(self, handler):
        """Teste de processamento de evento de cancelamento"""
        payment_data = {
            "payment_id": "test-789",
            "gateway": "cielo",
            "status": PaymentStatus.CANCELLED
        }

        await handler.handle_payment_event(
            event=WebhookEvent.PAYMENT_CANCELLED,
            payment_data=payment_data
        )

    @pytest.mark.asyncio
    async def test_handle_payment_refunded_event(self, handler):
        """Teste de processamento de evento de estorno"""
        payment_data = {
            "payment_id": "test-abc",
            "gateway": "mercadopago",
            "status": PaymentStatus.REFUNDED
        }

        await handler.handle_payment_event(
            event=WebhookEvent.PAYMENT_REFUNDED,
            payment_data=payment_data
        )

    @pytest.mark.asyncio
    async def test_handle_payment_chargeback_event(self, handler):
        """Teste de processamento de evento de chargeback"""
        payment_data = {
            "payment_id": "test-def",
            "gateway": "cielo",
            "status": PaymentStatus.REFUNDED
        }

        await handler.handle_payment_event(
            event=WebhookEvent.PAYMENT_CHARGEBACK,
            payment_data=payment_data
        )


# ============================================
# TESTES DO ROUTER DE WEBHOOKS
# ============================================

class TestWebhookRouter:
    """Testes dos endpoints de webhook"""

    @pytest.fixture
    def client(self):
        """Client de teste"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_webhook_test_endpoint(self, client):
        """Teste do endpoint de teste de conectividade"""
        response = client.get("/webhooks/payments/test")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Webhook endpoint is ready" in data["message"]

    def test_receive_webhook_invalid_gateway(self, client):
        """Teste de webhook com gateway inválido"""
        response = client.post(
            "/webhooks/payments/invalid-gateway",
            json={"test": "data"}
        )

        assert response.status_code == 400
        assert "Gateway inválido" in response.json()["detail"]

    @patch('app.services.payment_webhook_handler.PaymentWebhookHandler.process_webhook')
    def test_receive_cielo_webhook_success(self, mock_process, client):
        """Teste de recebimento bem-sucedido de webhook Cielo"""
        mock_process.return_value = {
            "gateway": "cielo",
            "payment_id": "test-123",
            "status": PaymentStatus.CAPTURED,
            "event": WebhookEvent.PAYMENT_APPROVED
        }

        payload = {
            "PaymentId": "test-123",
            "ChangeType": 1,
            "Status": 2
        }

        response = client.post(
            "/webhooks/payments/cielo",
            json=payload,
            headers={"X-Cielo-Signature": "test-signature"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["payment_id"] == "test-123"
        assert data["event"] == "payment.approved"

    @patch('app.services.payment_webhook_handler.PaymentWebhookHandler.process_webhook')
    def test_receive_webhook_validation_error(self, mock_process, client):
        """Teste de webhook com erro de validação"""
        mock_process.side_effect = ValidationException("Assinatura inválida")

        payload = {
            "PaymentId": "test-123"
        }

        response = client.post(
            "/webhooks/payments/cielo",
            json=payload
        )

        assert response.status_code == 401
        assert "Assinatura inválida" in response.json()["detail"]

    @patch('app.services.payment_webhook_handler.PaymentWebhookHandler.process_webhook')
    def test_receive_webhook_general_error(self, mock_process, client):
        """Teste de webhook com erro geral"""
        mock_process.side_effect = Exception("Erro inesperado")

        payload = {
            "PaymentId": "test-123"
        }

        response = client.post(
            "/webhooks/payments/cielo",
            json=payload
        )

        assert response.status_code == 500
        assert "Erro ao processar webhook" in response.json()["detail"]


# ============================================
# TESTES DE EDGE CASES
# ============================================

class TestWebhookEdgeCases:
    """Testes de casos extremos"""

    @pytest.fixture
    def handler(self):
        """Fixture do handler"""
        return PaymentWebhookHandler()

    @pytest.mark.asyncio
    async def test_cielo_webhook_unknown_status(self, handler):
        """Teste de webhook Cielo com status desconhecido"""
        payload = {
            "PaymentId": "cielo-payment-xyz",
            "ChangeType": 1,
            "Status": 99,  # Status desconhecido
            "ReasonCode": 0
        }

        secret = "CIELO_WEBHOOK_SECRET"
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        headers = {"X-Cielo-Signature": signature}

        result = await handler.process_webhook(
            gateway=PaymentGateway.CIELO,
            payload=payload,
            headers=headers
        )

        # Status desconhecido deve mapear para PENDING
        assert result["status"] == PaymentStatus.PENDING
        assert result["event"] is None  # Sem evento específico

    @pytest.mark.asyncio
    async def test_getnet_webhook_unknown_status(self, handler):
        """Teste de webhook GetNet com status desconhecido"""
        payload = {
            "notification_type": "payment",
            "status": "UNKNOWN_STATUS",
            "payment_id": "getnet-payment-xyz"
        }

        headers = {"Authorization": "Bearer valid-token"}

        result = await handler.process_webhook(
            gateway=PaymentGateway.GETNET,
            payload=payload,
            headers=headers
        )

        # Status desconhecido deve mapear para PENDING
        assert result["status"] == PaymentStatus.PENDING
        assert result["event"] is None

    @pytest.mark.asyncio
    async def test_cielo_signature_case_insensitive(self, handler):
        """Teste que assinatura Cielo é case-insensitive"""
        payload = {
            "PaymentId": "cielo-payment-123",
            "Status": 2
        }

        secret = "CIELO_WEBHOOK_SECRET"
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        # Testar com header em minúscula
        headers = {"x-cielo-signature": signature.upper()}

        result = await handler.process_webhook(
            gateway=PaymentGateway.CIELO,
            payload=payload,
            headers=headers
        )

        assert result["payment_id"] == "cielo-payment-123"

    @pytest.mark.asyncio
    async def test_getnet_auth_header_case_insensitive(self, handler):
        """Teste que header Authorization é case-insensitive"""
        payload = {
            "notification_type": "payment",
            "status": "APPROVED",
            "payment_id": "getnet-123"
        }

        # Testar com header em minúscula
        headers = {"authorization": "Bearer valid-token"}

        result = await handler.process_webhook(
            gateway=PaymentGateway.GETNET,
            payload=payload,
            headers=headers
        )

        assert result["payment_id"] == "getnet-123"
