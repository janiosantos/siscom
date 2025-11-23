"""
Celery Tasks para Webhooks
"""
import logging
import requests
from celery import shared_task
from typing import Dict, Any

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_webhook(self, url: str, payload: Dict[str, Any], headers: Dict[str, str] = None):
    """
    Envia webhook para URL especificada

    Args:
        url: URL do webhook
        payload: Dados a enviar
        headers: Headers HTTP customizados
    """
    try:
        headers = headers or {"Content-Type": "application/json"}

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        logger.info(f"Webhook enviado com sucesso para {url}")
        return {"status": "success", "status_code": response.status_code}

    except requests.exceptions.RequestException as exc:
        logger.error(f"Erro ao enviar webhook para {url}: {str(exc)}")

        # Retry com backoff exponencial
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_email_task(to: str, subject: str, body: str):
    """Task para envio de email assíncrono"""
    logger.info(f"Enviando email para {to}: {subject}")
    # Implementar com SendGrid/AWS SES
    return {"status": "sent", "to": to}


@shared_task
def send_sms_task(phone: str, message: str):
    """Task para envio de SMS assíncrono"""
    logger.info(f"Enviando SMS para {phone}")
    # Implementar com Twilio
    return {"status": "sent", "phone": phone}
