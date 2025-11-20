"""
Cliente para envio de SMS (Twilio)
"""
import logging
import httpx
from typing import Dict, Any, Optional
import base64

logger = logging.getLogger(__name__)


class SMSClient:
    """
    Client para envio de SMS via Twilio

    Funcionalidades:
    - Envio de SMS
    - Consulta de status
    - WhatsApp Business (via Twilio)
    """

    def __init__(self, account_sid: str, auth_token: str, phone_number: str):
        """
        Inicializa client Twilio

        Args:
            account_sid: Account SID do Twilio
            auth_token: Auth Token do Twilio
            phone_number: Número de telefone Twilio (formato: +5511999999999)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"

    def _get_auth_header(self) -> str:
        """Gera header de autenticação Basic"""
        credentials = f"{self.account_sid}:{self.auth_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def enviar_sms(
        self,
        destinatario: str,
        mensagem: str,
        status_callback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia um SMS

        Args:
            destinatario: Número do destinatário (formato: +5511999999999)
            mensagem: Texto da mensagem (até 160 caracteres por SMS)
            status_callback: URL para receber callbacks de status (opcional)

        Returns:
            Resultado do envio
        """
        logger.info(f"Enviando SMS para: {destinatario}")

        url = f"{self.base_url}/Messages.json"

        payload = {
            "From": self.phone_number,
            "To": destinatario,
            "Body": mensagem
        }

        if status_callback:
            payload["StatusCallback"] = status_callback

        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, data=payload)
                response.raise_for_status()

                data = response.json()

                logger.info(f"SMS enviado com sucesso - SID: {data.get('sid')}, Status: {data.get('status')}")

                return {
                    "sucesso": True,
                    "message_sid": data.get("sid"),
                    "status": data.get("status"),
                    "destinatario": destinatario,
                    "segmentos": data.get("num_segments"),
                    "preco": data.get("price"),
                    "moeda": data.get("price_unit")
                }

            except httpx.HTTPStatusError as e:
                error_data = e.response.json()
                logger.error(f"Erro ao enviar SMS: {error_data.get('message')}")
                return {
                    "sucesso": False,
                    "erro": error_data.get("message"),
                    "codigo_erro": error_data.get("code")
                }
            except Exception as e:
                logger.error(f"Erro ao enviar SMS: {str(e)}")
                return {
                    "sucesso": False,
                    "erro": str(e)
                }

    async def consultar_mensagem(self, message_sid: str) -> Dict[str, Any]:
        """
        Consulta o status de uma mensagem

        Args:
            message_sid: SID da mensagem

        Returns:
            Status da mensagem
        """
        logger.info(f"Consultando mensagem: {message_sid}")

        url = f"{self.base_url}/Messages/{message_sid}.json"

        headers = {
            "Authorization": self._get_auth_header()
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()

                logger.info(f"Mensagem consultada - Status: {data.get('status')}")

                return {
                    "message_sid": data.get("sid"),
                    "status": data.get("status"),
                    "de": data.get("from"),
                    "para": data.get("to"),
                    "corpo": data.get("body"),
                    "data_criacao": data.get("date_created"),
                    "data_envio": data.get("date_sent"),
                    "data_atualizacao": data.get("date_updated"),
                    "segmentos": data.get("num_segments"),
                    "preco": data.get("price"),
                    "erro_codigo": data.get("error_code"),
                    "erro_mensagem": data.get("error_message")
                }

            except Exception as e:
                logger.error(f"Erro ao consultar mensagem: {str(e)}")
                return {
                    "sucesso": False,
                    "erro": str(e)
                }

    async def enviar_whatsapp(
        self,
        destinatario: str,
        mensagem: str,
        media_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem via WhatsApp Business (Twilio)

        Args:
            destinatario: Número do destinatário (formato: +5511999999999)
            mensagem: Texto da mensagem
            media_url: URL de mídia para enviar (imagem, vídeo, etc)

        Returns:
            Resultado do envio
        """
        logger.info(f"Enviando WhatsApp para: {destinatario}")

        url = f"{self.base_url}/Messages.json"

        # WhatsApp usa prefixo whatsapp:
        whatsapp_from = f"whatsapp:{self.phone_number}"
        whatsapp_to = f"whatsapp:{destinatario}"

        payload = {
            "From": whatsapp_from,
            "To": whatsapp_to,
            "Body": mensagem
        }

        if media_url:
            payload["MediaUrl"] = media_url

        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, data=payload)
                response.raise_for_status()

                data = response.json()

                logger.info(f"WhatsApp enviado com sucesso - SID: {data.get('sid')}")

                return {
                    "sucesso": True,
                    "message_sid": data.get("sid"),
                    "status": data.get("status"),
                    "destinatario": destinatario,
                    "canal": "whatsapp"
                }

            except httpx.HTTPStatusError as e:
                error_data = e.response.json()
                logger.error(f"Erro ao enviar WhatsApp: {error_data.get('message')}")
                return {
                    "sucesso": False,
                    "erro": error_data.get("message"),
                    "codigo_erro": error_data.get("code")
                }
            except Exception as e:
                logger.error(f"Erro ao enviar WhatsApp: {str(e)}")
                return {
                    "sucesso": False,
                    "erro": str(e)
                }

    async def verificar_numero(self, numero: str) -> Dict[str, Any]:
        """
        Verifica se um número é válido (Lookup API)

        Args:
            numero: Número a verificar (formato: +5511999999999)

        Returns:
            Informações sobre o número
        """
        logger.info(f"Verificando número: {numero}")

        url = f"https://lookups.twilio.com/v1/PhoneNumbers/{numero}"

        headers = {
            "Authorization": self._get_auth_header()
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()

                logger.info(f"Número verificado - Válido: {data.get('phone_number')}")

                return {
                    "valido": True,
                    "numero_formatado": data.get("phone_number"),
                    "numero_nacional": data.get("national_format"),
                    "pais": data.get("country_code"),
                    "operadora": data.get("carrier", {}).get("name"),
                    "tipo": data.get("carrier", {}).get("type")
                }

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Número inválido: {numero}")
                    return {
                        "valido": False,
                        "erro": "Número não encontrado"
                    }
                logger.error(f"Erro ao verificar número: {e.response.text}")
                return {
                    "valido": False,
                    "erro": e.response.text
                }
            except Exception as e:
                logger.error(f"Erro ao verificar número: {str(e)}")
                return {
                    "valido": False,
                    "erro": str(e)
                }
