"""
Cliente para envio de emails (SendGrid / AWS SES)
"""
import logging
import httpx
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    """Provedores de email suportados"""
    SENDGRID = "sendgrid"
    AWS_SES = "aws_ses"


class EmailClient:
    """
    Client universal para envio de emails

    Suporta:
    - SendGrid
    - AWS SES
    """

    def __init__(self, provider: EmailProvider, api_key: str, sender_email: str, sender_name: str = None):
        """
        Inicializa client de email

        Args:
            provider: Provedor de email (sendgrid ou aws_ses)
            api_key: API Key do provedor
            sender_email: Email do remetente
            sender_name: Nome do remetente (opcional)
        """
        self.provider = provider
        self.api_key = api_key
        self.sender_email = sender_email
        self.sender_name = sender_name or sender_email

    async def enviar_email(
        self,
        destinatario: str,
        assunto: str,
        corpo_html: str,
        corpo_texto: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        anexos: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Envia um email

        Args:
            destinatario: Email do destinatário
            assunto: Assunto do email
            corpo_html: Corpo do email em HTML
            corpo_texto: Corpo do email em texto puro (opcional)
            reply_to: Email para resposta (opcional)
            cc: Lista de emails em cópia (opcional)
            bcc: Lista de emails em cópia oculta (opcional)
            anexos: Lista de anexos (opcional)

        Returns:
            Resultado do envio
        """
        if self.provider == EmailProvider.SENDGRID:
            return await self._enviar_sendgrid(
                destinatario, assunto, corpo_html, corpo_texto,
                reply_to, cc, bcc, anexos
            )
        elif self.provider == EmailProvider.AWS_SES:
            return await self._enviar_aws_ses(
                destinatario, assunto, corpo_html, corpo_texto,
                reply_to, cc, bcc
            )
        else:
            raise ValueError(f"Provedor não suportado: {self.provider}")

    async def _enviar_sendgrid(
        self,
        destinatario: str,
        assunto: str,
        corpo_html: str,
        corpo_texto: Optional[str],
        reply_to: Optional[str],
        cc: Optional[List[str]],
        bcc: Optional[List[str]],
        anexos: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Envia email via SendGrid"""
        logger.info(f"Enviando email via SendGrid para: {destinatario}")

        url = "https://api.sendgrid.com/v3/mail/send"

        # Montar payload
        payload = {
            "personalizations": [{
                "to": [{"email": destinatario}]
            }],
            "from": {
                "email": self.sender_email,
                "name": self.sender_name
            },
            "subject": assunto,
            "content": [
                {"type": "text/html", "value": corpo_html}
            ]
        }

        if corpo_texto:
            payload["content"].insert(0, {"type": "text/plain", "value": corpo_texto})

        if reply_to:
            payload["reply_to"] = {"email": reply_to}

        if cc:
            payload["personalizations"][0]["cc"] = [{"email": email} for email in cc]

        if bcc:
            payload["personalizations"][0]["bcc"] = [{"email": email} for email in bcc]

        if anexos:
            payload["attachments"] = []
            for anexo in anexos:
                payload["attachments"].append({
                    "content": anexo.get("content_base64"),
                    "filename": anexo.get("filename"),
                    "type": anexo.get("content_type", "application/octet-stream")
                })

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                logger.info(f"Email enviado com sucesso via SendGrid - ID: {response.headers.get('X-Message-Id')}")

                return {
                    "sucesso": True,
                    "provider": "sendgrid",
                    "message_id": response.headers.get("X-Message-Id"),
                    "destinatario": destinatario
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"Erro ao enviar email via SendGrid: {e.response.status_code} - {e.response.text}")
                return {
                    "sucesso": False,
                    "provider": "sendgrid",
                    "erro": f"HTTP {e.response.status_code}: {e.response.text}"
                }
            except Exception as e:
                logger.error(f"Erro ao enviar email via SendGrid: {str(e)}")
                return {
                    "sucesso": False,
                    "provider": "sendgrid",
                    "erro": str(e)
                }

    async def _enviar_aws_ses(
        self,
        destinatario: str,
        assunto: str,
        corpo_html: str,
        corpo_texto: Optional[str],
        reply_to: Optional[str],
        cc: Optional[List[str]],
        bcc: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Envia email via AWS SES"""
        logger.info(f"Enviando email via AWS SES para: {destinatario}")

        try:
            # Importar boto3 (AWS SDK)
            import boto3
            from botocore.exceptions import ClientError

            ses_client = boto3.client('ses', region_name='us-east-1')

            # Montar destinatários
            destination = {"ToAddresses": [destinatario]}
            if cc:
                destination["CcAddresses"] = cc
            if bcc:
                destination["BccAddresses"] = bcc

            # Montar mensagem
            message = {
                "Subject": {"Data": assunto, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": corpo_html, "Charset": "UTF-8"}
                }
            }

            if corpo_texto:
                message["Body"]["Text"] = {"Data": corpo_texto, "Charset": "UTF-8"}

            # Enviar email
            response = ses_client.send_email(
                Source=f"{self.sender_name} <{self.sender_email}>",
                Destination=destination,
                Message=message,
                ReplyToAddresses=[reply_to] if reply_to else []
            )

            message_id = response.get("MessageId")
            logger.info(f"Email enviado com sucesso via AWS SES - ID: {message_id}")

            return {
                "sucesso": True,
                "provider": "aws_ses",
                "message_id": message_id,
                "destinatario": destinatario
            }

        except ClientError as e:
            logger.error(f"Erro AWS SES: {e.response['Error']['Message']}")
            return {
                "sucesso": False,
                "provider": "aws_ses",
                "erro": e.response["Error"]["Message"]
            }
        except ImportError:
            logger.error("boto3 não instalado. Execute: pip install boto3")
            return {
                "sucesso": False,
                "provider": "aws_ses",
                "erro": "boto3 não instalado"
            }
        except Exception as e:
            logger.error(f"Erro ao enviar email via AWS SES: {str(e)}")
            return {
                "sucesso": False,
                "provider": "aws_ses",
                "erro": str(e)
            }

    async def enviar_template(
        self,
        destinatario: str,
        template_id: str,
        dados_template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envia email usando template (SendGrid)

        Args:
            destinatario: Email do destinatário
            template_id: ID do template no SendGrid
            dados_template: Dados dinâmicos do template

        Returns:
            Resultado do envio
        """
        if self.provider != EmailProvider.SENDGRID:
            raise ValueError("Templates são suportados apenas no SendGrid")

        logger.info(f"Enviando email template '{template_id}' para: {destinatario}")

        url = "https://api.sendgrid.com/v3/mail/send"

        payload = {
            "personalizations": [{
                "to": [{"email": destinatario}],
                "dynamic_template_data": dados_template
            }],
            "from": {
                "email": self.sender_email,
                "name": self.sender_name
            },
            "template_id": template_id
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                logger.info(f"Email template enviado com sucesso - ID: {response.headers.get('X-Message-Id')}")

                return {
                    "sucesso": True,
                    "provider": "sendgrid",
                    "message_id": response.headers.get("X-Message-Id"),
                    "destinatario": destinatario,
                    "template_id": template_id
                }

            except Exception as e:
                logger.error(f"Erro ao enviar template: {str(e)}")
                return {
                    "sucesso": False,
                    "provider": "sendgrid",
                    "erro": str(e)
                }
