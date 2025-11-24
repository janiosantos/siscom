"""
Integração Mercado Pago - PIX e Pagamentos
Documentação: https://documenter.getpostman.com/view/15366798/2sAXjKasp4
"""
import logging
import httpx
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from app.modules.pagamentos.models import StatusPagamento

logger = logging.getLogger(__name__)


class MercadoPagoClient:
    """Cliente para integração com Mercado Pago"""

    def __init__(self, access_token: str, public_key: str = None):
        self.access_token = access_token
        self.public_key = public_key
        self.base_url = "https://api.mercadopago.com"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    async def criar_pagamento_pix(
        self,
        valor: Decimal,
        descricao: str,
        email_pagador: Optional[str] = None,
        external_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um pagamento PIX no Mercado Pago

        Args:
            valor: Valor do pagamento
            descricao: Descrição do pagamento
            email_pagador: Email do pagador (opcional)
            external_reference: Referência externa (ID da venda, etc)

        Returns:
            Dados do pagamento criado (inclui QR Code PIX)
        """
        logger.info(f"Criando pagamento PIX - Valor: {valor}, Ref: {external_reference}")

        payload = {
            "transaction_amount": float(valor),
            "description": descricao,
            "payment_method_id": "pix",
            "payer": {
                "email": email_pagador or "test@test.com"
            }
        }

        if external_reference:
            payload["external_reference"] = external_reference

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/payments",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"Pagamento PIX criado com sucesso - ID: {data.get('id')}")

                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "status_detail": data.get("status_detail"),
                    "qr_code": data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code"),
                    "qr_code_base64": data.get("point_of_interaction", {}).get("transaction_data", {}).get("qr_code_base64"),
                    "ticket_url": data.get("point_of_interaction", {}).get("transaction_data", {}).get("ticket_url"),
                    "transaction_id": data.get("id"),
                    "external_reference": data.get("external_reference"),
                    "valor": Decimal(str(data.get("transaction_amount"))),
                    "data_criacao": data.get("date_created"),
                    "data_expiracao": data.get("date_of_expiration")
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"Erro HTTP ao criar pagamento: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Erro ao criar pagamento PIX: {e.response.text}")
            except Exception as e:
                logger.error(f"Erro ao criar pagamento PIX: {str(e)}")
                raise

    async def consultar_pagamento(self, payment_id: int) -> Dict[str, Any]:
        """
        Consulta status de um pagamento

        Args:
            payment_id: ID do pagamento no Mercado Pago

        Returns:
            Dados atualizados do pagamento
        """
        logger.info(f"Consultando pagamento {payment_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/v1/payments/{payment_id}",
                    headers=self.headers
                )
                response.raise_for_status()

                data = response.json()

                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "status_detail": data.get("status_detail"),
                    "transaction_id": data.get("id"),
                    "external_reference": data.get("external_reference"),
                    "valor": Decimal(str(data.get("transaction_amount"))),
                    "valor_pago": Decimal(str(data.get("transaction_amount_refunded", 0))),
                    "data_criacao": data.get("date_created"),
                    "data_aprovacao": data.get("date_approved"),
                    "metodo_pagamento": data.get("payment_method_id"),
                    "tipo_pagamento": data.get("payment_type_id")
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"Erro ao consultar pagamento: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"Erro ao consultar pagamento: {str(e)}")
                raise

    async def cancelar_pagamento(self, payment_id: int) -> Dict[str, Any]:
        """
        Cancela um pagamento pendente

        Args:
            payment_id: ID do pagamento

        Returns:
            Dados do pagamento cancelado
        """
        logger.info(f"Cancelando pagamento {payment_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.put(
                    f"{self.base_url}/v1/payments/{payment_id}",
                    headers=self.headers,
                    json={"status": "cancelled"}
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"Pagamento {payment_id} cancelado com sucesso")

                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "cancelado": True
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"Erro ao cancelar pagamento: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"Erro ao cancelar pagamento: {str(e)}")
                raise

    async def processar_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa notificação de webhook do Mercado Pago

        Args:
            webhook_data: Dados do webhook

        Returns:
            Dados processados
        """
        logger.info(f"Processando webhook - Tipo: {webhook_data.get('type')}")

        # Extrair dados do webhook
        resource_type = webhook_data.get("type")
        resource_id = webhook_data.get("data", {}).get("id")

        if resource_type == "payment" and resource_id:
            # Consultar pagamento para obter dados completos
            payment_data = await self.consultar_pagamento(resource_id)
            return payment_data

        return webhook_data

    async def criar_preferencia_checkout(
        self,
        items: list,
        external_reference: str = None,
        notification_url: str = None,
        back_urls: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Cria uma preferência de checkout (para Checkout Pro)

        Args:
            items: Lista de itens do pagamento
            external_reference: Referência externa
            notification_url: URL para notificações
            back_urls: URLs de retorno (success, failure, pending)

        Returns:
            Dados da preferência criada
        """
        logger.info(f"Criando preferência de checkout - Ref: {external_reference}")

        payload = {
            "items": items,
            "back_urls": back_urls or {},
            "auto_return": "approved",
            "payment_methods": {
                "excluded_payment_methods": [],
                "excluded_payment_types": [],
                "installments": 12
            }
        }

        if external_reference:
            payload["external_reference"] = external_reference

        if notification_url:
            payload["notification_url"] = notification_url

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/checkout/preferences",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"Preferência criada - ID: {data.get('id')}")

                return {
                    "id": data.get("id"),
                    "init_point": data.get("init_point"),  # URL para checkout web
                    "sandbox_init_point": data.get("sandbox_init_point"),  # URL sandbox
                    "external_reference": data.get("external_reference")
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"Erro ao criar preferência: {e.response.status_code}")
                raise
            except Exception as e:
                logger.error(f"Erro ao criar preferência: {str(e)}")
                raise

    async def criar_pagamento_cartao(
        self,
        valor: Decimal,
        descricao: str,
        token_cartao: str,
        installments: int = 1,
        email_pagador: str = None,
        cpf_pagador: str = None,
        nome_pagador: str = None,
        external_reference: str = None
    ) -> Dict[str, Any]:
        """
        Cria um pagamento com cartão de crédito/débito

        Args:
            valor: Valor do pagamento
            descricao: Descrição do pagamento
            token_cartao: Token do cartão (obtido via MercadoPago.js)
            installments: Número de parcelas (1-12)
            email_pagador: Email do pagador
            cpf_pagador: CPF do pagador
            nome_pagador: Nome do pagador
            external_reference: Referência externa

        Returns:
            Dados do pagamento criado
        """
        logger.info(f"Criando pagamento com cartão - Valor: {valor}, Parcelas: {installments}")

        payload = {
            "transaction_amount": float(valor),
            "description": descricao,
            "token": token_cartao,
            "installments": installments,
            "payer": {
                "email": email_pagador or "test@test.com"
            }
        }

        if cpf_pagador:
            payload["payer"]["identification"] = {
                "type": "CPF",
                "number": cpf_pagador
            }

        if nome_pagador:
            payload["payer"]["first_name"] = nome_pagador.split()[0] if nome_pagador else "Nome"
            payload["payer"]["last_name"] = " ".join(nome_pagador.split()[1:]) if len(nome_pagador.split()) > 1 else "Sobrenome"

        if external_reference:
            payload["external_reference"] = external_reference

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/payments",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                logger.info(f"Pagamento com cartão criado - ID: {data.get('id')}, Status: {data.get('status')}")

                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "status_detail": data.get("status_detail"),
                    "valor": data.get("transaction_amount"),
                    "data_criacao": data.get("date_created"),
                    "data_aprovacao": data.get("date_approved"),
                    "metodo_pagamento": data.get("payment_method_id"),
                    "parcelas": data.get("installments"),
                    "authorization_code": data.get("authorization_code"),
                    "external_reference": data.get("external_reference")
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"Erro ao criar pagamento com cartão: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Erro ao criar pagamento com cartão: {str(e)}")
                raise


# Helper para converter status MP para status interno
def converter_status_mp(status_mp: str) -> StatusPagamento:
    """
    Converte status do Mercado Pago para StatusPagamento enum

    Args:
        status_mp: Status do Mercado Pago (pending, approved, rejected, etc.)

    Returns:
        StatusPagamento enum correspondente
    """
    status_map = {
        "pending": StatusPagamento.PENDENTE,
        "approved": StatusPagamento.APROVADO,
        "authorized": StatusPagamento.APROVADO,  # Autorizado = Aprovado
        "in_process": StatusPagamento.PROCESSANDO,
        "in_mediation": StatusPagamento.PROCESSANDO,  # Em mediação = Processando
        "rejected": StatusPagamento.REJEITADO,
        "cancelled": StatusPagamento.CANCELADO,
        "refunded": StatusPagamento.ESTORNADO,
        "charged_back": StatusPagamento.ESTORNADO
    }

    return status_map.get(status_mp, StatusPagamento.PENDENTE)
