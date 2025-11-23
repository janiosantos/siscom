"""
Payment Webhook Handler

Processa notificações (webhooks) dos gateways de pagamento:
- Cielo
- GetNet
- Mercado Pago

Responsabilidades:
- Validar assinatura do webhook
- Processar notificação
- Atualizar status do pagamento no banco
- Disparar eventos para outros módulos
"""
from typing import Dict, Any, Optional
from enum import Enum
import hmac
import hashlib
import json
from datetime import datetime

from app.core.logging import get_logger
from app.core.exceptions import ValidationException, BusinessRuleException
from app.services.payment_gateway_service import PaymentGateway, PaymentStatus

logger = get_logger(__name__)


class WebhookEvent(str, Enum):
    """Tipos de eventos de webhook"""
    PAYMENT_APPROVED = "payment.approved"
    PAYMENT_PENDING = "payment.pending"
    PAYMENT_DENIED = "payment.denied"
    PAYMENT_CANCELLED = "payment.cancelled"
    PAYMENT_REFUNDED = "payment.refunded"
    PAYMENT_CHARGEBACK = "payment.chargeback"


class PaymentWebhookHandler:
    """
    Handler unificado de webhooks de pagamento

    Processa notificações de todos os gateways e normaliza os eventos
    """

    def __init__(self):
        """Inicializa handler"""
        self.handlers = {
            PaymentGateway.CIELO: self._handle_cielo_webhook,
            PaymentGateway.GETNET: self._handle_getnet_webhook,
            PaymentGateway.MERCADOPAGO: self._handle_mercadopago_webhook
        }

    async def process_webhook(
        self,
        gateway: PaymentGateway,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Processa webhook de qualquer gateway

        Args:
            gateway: Gateway que enviou a notificação
            payload: Corpo da requisição (JSON)
            headers: Headers HTTP da requisição

        Returns:
            Dados processados do pagamento

        Raises:
            ValidationException: Se assinatura inválida
            BusinessRuleException: Se gateway não suportado
        """
        logger.info(
            f"Processando webhook - Gateway: {gateway}",
            extra={
                "gateway": gateway.value,
                "event_type": payload.get("type") or payload.get("action")
            }
        )

        # Valida assinatura do webhook
        if not await self._validate_signature(gateway, payload, headers):
            logger.warning(
                f"Webhook com assinatura inválida - Gateway: {gateway}",
                extra={"gateway": gateway.value}
            )
            raise ValidationException("Assinatura do webhook inválida")

        # Roteia para handler específico
        handler = self.handlers.get(gateway)
        if not handler:
            raise BusinessRuleException(f"Gateway {gateway} não suportado para webhooks")

        result = await handler(payload, headers)

        logger.info(
            f"Webhook processado com sucesso",
            extra={
                "gateway": gateway.value,
                "payment_id": result.get("payment_id"),
                "status": result.get("status"),
                "event": result.get("event")
            }
        )

        return result

    async def _validate_signature(
        self,
        gateway: PaymentGateway,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> bool:
        """
        Valida assinatura do webhook

        Cada gateway usa método diferente de assinatura
        """
        if gateway == PaymentGateway.CIELO:
            return self._validate_cielo_signature(payload, headers)
        elif gateway == PaymentGateway.GETNET:
            return self._validate_getnet_signature(payload, headers)
        elif gateway == PaymentGateway.MERCADOPAGO:
            return self._validate_mercadopago_signature(payload, headers)
        else:
            return False

    def _validate_cielo_signature(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> bool:
        """
        Valida assinatura Cielo

        Cielo usa HMAC SHA256 no header X-Cielo-Signature
        """
        signature = headers.get("X-Cielo-Signature") or headers.get("x-cielo-signature")
        if not signature:
            logger.warning("Header X-Cielo-Signature não encontrado")
            return False

        # TODO: Obter secret do settings
        secret = "CIELO_WEBHOOK_SECRET"

        # Calcula HMAC
        payload_str = json.dumps(payload, sort_keys=True)
        calculated = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature.lower(), calculated.lower())

    def _validate_getnet_signature(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> bool:
        """
        Valida assinatura GetNet

        GetNet usa token no header Authorization
        """
        auth = headers.get("Authorization") or headers.get("authorization")
        if not auth:
            logger.warning("Header Authorization não encontrado")
            return False

        # TODO: Validar token com GetNet
        # Por ora, aceita qualquer token Bearer
        return auth.startswith("Bearer ")

    def _validate_mercadopago_signature(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> bool:
        """
        Valida assinatura Mercado Pago

        MP usa x-signature e x-request-id
        """
        signature = headers.get("x-signature")
        request_id = headers.get("x-request-id")

        if not signature or not request_id:
            logger.warning("Headers x-signature ou x-request-id não encontrados")
            return False

        # TODO: Implementar validação completa do MP
        # Por ora, aceita se headers existem
        return True

    # ============================================
    # HANDLERS ESPECÍFICOS POR GATEWAY
    # ============================================

    async def _handle_cielo_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Processa webhook da Cielo

        Formato esperado:
        {
            "PaymentId": "abc-123",
            "ChangeType": 1,  # 1=Status, 2=Recurrency, 3=Chargeback
            "ReasonCode": 0,
            "Status": 2
        }
        """
        payment_id = payload.get("PaymentId")
        change_type = payload.get("ChangeType")
        status_code = str(payload.get("Status", ""))

        # Mapeia status Cielo
        status_map = {
            "0": PaymentStatus.PENDING,
            "1": PaymentStatus.AUTHORIZED,
            "2": PaymentStatus.CAPTURED,
            "3": PaymentStatus.DENIED,
            "10": PaymentStatus.CANCELLED,
            "11": PaymentStatus.REFUNDED,
            "12": PaymentStatus.PENDING,
            "13": PaymentStatus.CANCELLED
        }

        status = status_map.get(status_code, PaymentStatus.PENDING)

        # Determina evento
        event = None
        if status == PaymentStatus.CAPTURED:
            event = WebhookEvent.PAYMENT_APPROVED
        elif status == PaymentStatus.DENIED:
            event = WebhookEvent.PAYMENT_DENIED
        elif status == PaymentStatus.CANCELLED:
            event = WebhookEvent.PAYMENT_CANCELLED
        elif status == PaymentStatus.REFUNDED:
            event = WebhookEvent.PAYMENT_REFUNDED

        return {
            "gateway": PaymentGateway.CIELO.value,
            "payment_id": payment_id,
            "status": status,
            "event": event,
            "raw_payload": payload,
            "processed_at": datetime.utcnow().isoformat()
        }

    async def _handle_getnet_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Processa webhook da GetNet

        Formato esperado:
        {
            "notification_type": "payment",
            "status": "APPROVED",
            "payment_id": "xyz-789",
            "order_id": "ORDER-001"
        }
        """
        payment_id = payload.get("payment_id")
        order_id = payload.get("order_id")
        status_str = payload.get("status", "")

        # Mapeia status GetNet
        status_map = {
            "PENDING": PaymentStatus.PENDING,
            "AUTHORIZED": PaymentStatus.AUTHORIZED,
            "APPROVED": PaymentStatus.CAPTURED,
            "DENIED": PaymentStatus.DENIED,
            "CANCELED": PaymentStatus.CANCELLED,
            "REFUNDED": PaymentStatus.REFUNDED
        }

        status = status_map.get(status_str, PaymentStatus.PENDING)

        # Determina evento
        event = None
        if status == PaymentStatus.CAPTURED:
            event = WebhookEvent.PAYMENT_APPROVED
        elif status == PaymentStatus.DENIED:
            event = WebhookEvent.PAYMENT_DENIED
        elif status == PaymentStatus.CANCELLED:
            event = WebhookEvent.PAYMENT_CANCELLED
        elif status == PaymentStatus.REFUNDED:
            event = WebhookEvent.PAYMENT_REFUNDED

        return {
            "gateway": PaymentGateway.GETNET.value,
            "payment_id": payment_id,
            "order_id": order_id,
            "status": status,
            "event": event,
            "raw_payload": payload,
            "processed_at": datetime.utcnow().isoformat()
        }

    async def _handle_mercadopago_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Processa webhook do Mercado Pago

        Formato esperado:
        {
            "action": "payment.created" | "payment.updated",
            "data": {
                "id": "123456789"
            },
            "type": "payment"
        }
        """
        action = payload.get("action")
        data = payload.get("data", {})
        payment_id = str(data.get("id", ""))

        # MP envia apenas o ID, precisamos consultar para obter detalhes
        # Por ora, retornamos PENDING e deixamos o sistema consultar depois

        return {
            "gateway": PaymentGateway.MERCADOPAGO.value,
            "payment_id": payment_id,
            "status": PaymentStatus.PENDING,  # Consultar depois
            "event": WebhookEvent.PAYMENT_PENDING,
            "action": action,
            "raw_payload": payload,
            "processed_at": datetime.utcnow().isoformat(),
            "requires_query": True  # Flag para indicar que precisa consultar
        }

    # ============================================
    # PROCESSAMENTO DE EVENTOS
    # ============================================

    async def handle_payment_event(
        self,
        event: WebhookEvent,
        payment_data: Dict[str, Any]
    ) -> None:
        """
        Processa evento de pagamento

        Atualiza banco de dados e dispara ações necessárias
        """
        logger.info(
            f"Processando evento: {event}",
            extra={
                "event": event.value,
                "payment_id": payment_data.get("payment_id"),
                "gateway": payment_data.get("gateway")
            }
        )

        if event == WebhookEvent.PAYMENT_APPROVED:
            await self._handle_payment_approved(payment_data)

        elif event == WebhookEvent.PAYMENT_DENIED:
            await self._handle_payment_denied(payment_data)

        elif event == WebhookEvent.PAYMENT_CANCELLED:
            await self._handle_payment_cancelled(payment_data)

        elif event == WebhookEvent.PAYMENT_REFUNDED:
            await self._handle_payment_refunded(payment_data)

        elif event == WebhookEvent.PAYMENT_CHARGEBACK:
            await self._handle_payment_chargeback(payment_data)

    async def _handle_payment_approved(self, payment_data: Dict[str, Any]):
        """
        Processa pagamento aprovado

        Ações:
        - Atualizar status no banco
        - Liberar pedido
        - Enviar email de confirmação
        - Emitir nota fiscal
        """
        logger.info(
            "Pagamento aprovado",
            extra={
                "payment_id": payment_data.get("payment_id"),
                "gateway": payment_data.get("gateway")
            }
        )

        # TODO: Implementar atualização no banco
        # TODO: Liberar pedido para separação
        # TODO: Enviar email
        # TODO: Emitir NF-e

    async def _handle_payment_denied(self, payment_data: Dict[str, Any]):
        """
        Processa pagamento negado

        Ações:
        - Atualizar status no banco
        - Notificar cliente
        - Liberar estoque (se reservado)
        """
        logger.warning(
            "Pagamento negado",
            extra={
                "payment_id": payment_data.get("payment_id"),
                "gateway": payment_data.get("gateway")
            }
        )

        # TODO: Implementar ações

    async def _handle_payment_cancelled(self, payment_data: Dict[str, Any]):
        """
        Processa cancelamento

        Ações:
        - Atualizar status no banco
        - Cancelar pedido
        - Liberar estoque
        """
        logger.info(
            "Pagamento cancelado",
            extra={
                "payment_id": payment_data.get("payment_id"),
                "gateway": payment_data.get("gateway")
            }
        )

        # TODO: Implementar ações

    async def _handle_payment_refunded(self, payment_data: Dict[str, Any]):
        """
        Processa estorno

        Ações:
        - Atualizar status no banco
        - Registrar estorno financeiro
        - Notificar cliente
        """
        logger.info(
            "Pagamento estornado",
            extra={
                "payment_id": payment_data.get("payment_id"),
                "gateway": payment_data.get("gateway")
            }
        )

        # TODO: Implementar ações

    async def _handle_payment_chargeback(self, payment_data: Dict[str, Any]):
        """
        Processa chargeback (contestação)

        Ações:
        - Atualizar status no banco
        - Alertar equipe financeira
        - Bloquear cliente (se necessário)
        """
        logger.warning(
            "Chargeback recebido",
            extra={
                "payment_id": payment_data.get("payment_id"),
                "gateway": payment_data.get("gateway")
            }
        )

        # TODO: Implementar ações


# ============================================
# ROUTER PARA RECEBER WEBHOOKS
# ============================================

from fastapi import APIRouter, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post(
    "/webhooks/payments/{gateway}",
    summary="Receber webhook de gateway de pagamento",
    description="Endpoint para processar notificações dos gateways",
    status_code=status.HTTP_200_OK
)
async def receive_payment_webhook(
    gateway: str,
    request: Request
):
    """
    Recebe webhook de pagamento

    Suporta: cielo, getnet, mercadopago
    """
    try:
        # Parse gateway
        gateway_enum = PaymentGateway(gateway.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Gateway inválido: {gateway}"
        )

    # Le payload
    payload = await request.json()
    headers = dict(request.headers)

    # Processa webhook
    handler = PaymentWebhookHandler()

    try:
        result = await handler.process_webhook(
            gateway=gateway_enum,
            payload=payload,
            headers=headers
        )

        # Processa evento
        if result.get("event"):
            await handler.handle_payment_event(
                event=result["event"],
                payment_data=result
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "processed",
                "payment_id": result.get("payment_id"),
                "event": result.get("event")
            }
        )

    except ValidationException as e:
        logger.error(f"Webhook inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar webhook"
        )


@router.get(
    "/webhooks/payments/test",
    summary="Testar endpoint de webhook",
    description="Retorna 200 OK para testes de conectividade"
)
async def test_webhook_endpoint():
    """Endpoint de teste para validar conectividade"""
    return {"status": "ok", "message": "Webhook endpoint is ready"}
