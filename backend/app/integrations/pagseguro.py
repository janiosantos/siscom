"""
Cliente para integração com PagSeguro
API v4 (REST)

Funcionalidades:
- PIX (QR Code dinâmico)
- Cartão de crédito/débito
- Boleto bancário
- Consulta de transações
- Webhooks (notificações)
"""
import logging
import httpx
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PagSeguroClient:
    """
    Cliente para API PagSeguro v4

    Documentação: https://dev.pagseguro.uol.com.br/reference/
    """

    def __init__(self, token: str, sandbox: bool = True):
        """
        Inicializa cliente PagSeguro

        Args:
            token: Token de acesso da API
            sandbox: Se True, usa ambiente sandbox
        """
        self.token = token
        self.sandbox = sandbox

        if sandbox:
            self.base_url = "https://sandbox.api.pagseguro.com"
        else:
            self.base_url = "https://api.pagseguro.com"

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def criar_pagamento_pix(
        self,
        valor: Decimal,
        descricao: str,
        reference_id: str,
        customer: Dict[str, Any],
        expiration_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria pagamento PIX com QR Code

        Args:
            valor: Valor em centavos
            descricao: Descrição da transação
            reference_id: ID de referência único
            customer: Dados do cliente
            expiration_date: Data de expiração (ISO 8601)

        Returns:
            Dados do pagamento com QR Code
        """
        logger.info(f"Criando pagamento PIX - Valor: R$ {float(valor)/100:.2f}")

        # Expiração padrão: 30 minutos
        if not expiration_date:
            exp_time = datetime.utcnow() + timedelta(minutes=30)
            expiration_date = exp_time.strftime("%Y-%m-%dT%H:%M:%S-03:00")

        payload = {
            "reference_id": reference_id,
            "description": descricao,
            "amount": {
                "value": int(valor),  # Valor em centavos
                "currency": "BRL"
            },
            "payment_method": {
                "type": "PIX",
                "pix": {
                    "expiration_date": expiration_date
                }
            },
            "notification_urls": [],  # Será preenchido pelo webhook
            "customer": customer
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/charges",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"PIX criado com sucesso - ID: {data.get('id')}")
                return {
                    "sucesso": True,
                    "id": data.get("id"),
                    "reference_id": data.get("reference_id"),
                    "status": data.get("status"),
                    "qr_code": data.get("qr_codes", [{}])[0].get("text"),
                    "qr_code_base64": data.get("qr_codes", [{}])[0].get("arrangement", {}).get("qr_code"),
                    "expiration_date": data.get("qr_codes", [{}])[0].get("expiration_date"),
                    "links": data.get("links", [])
                }
            else:
                logger.error(f"Erro ao criar PIX: {response.status_code} - {response.text}")
                return {
                    "sucesso": False,
                    "erro": response.text,
                    "status_code": response.status_code
                }

    async def criar_pagamento_cartao(
        self,
        valor: Decimal,
        descricao: str,
        reference_id: str,
        customer: Dict[str, Any],
        card: Dict[str, Any],
        installments: int = 1
    ) -> Dict[str, Any]:
        """
        Cria pagamento com cartão de crédito/débito

        Args:
            valor: Valor em centavos
            descricao: Descrição
            reference_id: ID de referência
            customer: Dados do cliente
            card: Dados do cartão (encrypted ou holder)
            installments: Número de parcelas

        Returns:
            Dados do pagamento
        """
        logger.info(f"Criando pagamento cartão - Valor: R$ {float(valor)/100:.2f}, Parcelas: {installments}")

        payload = {
            "reference_id": reference_id,
            "description": descricao,
            "amount": {
                "value": int(valor),
                "currency": "BRL"
            },
            "payment_method": {
                "type": "CREDIT_CARD",
                "installments": installments,
                "capture": True,  # Captura automática
                "card": card
            },
            "customer": customer
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/charges",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Pagamento cartão criado - ID: {data.get('id')}")
                return {
                    "sucesso": True,
                    "id": data.get("id"),
                    "reference_id": data.get("reference_id"),
                    "status": data.get("status"),
                    "amount": data.get("amount"),
                    "paid_at": data.get("paid_at"),
                    "payment_response": data.get("payment_response"),
                    "links": data.get("links", [])
                }
            else:
                logger.error(f"Erro pagamento cartão: {response.status_code} - {response.text}")
                return {
                    "sucesso": False,
                    "erro": response.text,
                    "status_code": response.status_code
                }

    async def criar_boleto(
        self,
        valor: Decimal,
        descricao: str,
        reference_id: str,
        customer: Dict[str, Any],
        due_date: Optional[str] = None,
        instruction_lines: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Cria boleto bancário

        Args:
            valor: Valor em centavos
            descricao: Descrição
            reference_id: ID de referência
            customer: Dados do cliente
            due_date: Data de vencimento (YYYY-MM-DD)
            instruction_lines: Linhas de instrução

        Returns:
            Dados do boleto
        """
        logger.info(f"Criando boleto - Valor: R$ {float(valor)/100:.2f}")

        # Vencimento padrão: 3 dias
        if not due_date:
            due = datetime.now() + timedelta(days=3)
            due_date = due.strftime("%Y-%m-%d")

        payload = {
            "reference_id": reference_id,
            "description": descricao,
            "amount": {
                "value": int(valor),
                "currency": "BRL"
            },
            "payment_method": {
                "type": "BOLETO",
                "boleto": {
                    "due_date": due_date,
                    "instruction_lines": instruction_lines or {
                        "line_1": "Pagamento processado para Conta Mercantil",
                        "line_2": "Via PagSeguro"
                    }
                }
            },
            "customer": customer
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/charges",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code in [200, 201]:
                data = response.json()
                logger.info(f"Boleto criado - ID: {data.get('id')}")
                return {
                    "sucesso": True,
                    "id": data.get("id"),
                    "reference_id": data.get("reference_id"),
                    "status": data.get("status"),
                    "barcode": data.get("payment_method", {}).get("boleto", {}).get("barcode"),
                    "formatted_barcode": data.get("payment_method", {}).get("boleto", {}).get("formatted_barcode"),
                    "due_date": data.get("payment_method", {}).get("boleto", {}).get("due_date"),
                    "links": data.get("links", [])
                }
            else:
                logger.error(f"Erro ao criar boleto: {response.status_code} - {response.text}")
                return {
                    "sucesso": False,
                    "erro": response.text,
                    "status_code": response.status_code
                }

    async def consultar_cobranca(self, charge_id: str) -> Dict[str, Any]:
        """
        Consulta status de uma cobrança

        Args:
            charge_id: ID da cobrança

        Returns:
            Dados atualizados da cobrança
        """
        logger.info(f"Consultando cobrança: {charge_id}")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/charges/{charge_id}",
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "sucesso": True,
                    "id": data.get("id"),
                    "reference_id": data.get("reference_id"),
                    "status": data.get("status"),
                    "amount": data.get("amount"),
                    "paid_at": data.get("paid_at"),
                    "created_at": data.get("created_at"),
                    "payment_method": data.get("payment_method"),
                    "customer": data.get("customer")
                }
            else:
                logger.error(f"Erro ao consultar: {response.status_code} - {response.text}")
                return {
                    "sucesso": False,
                    "erro": response.text,
                    "status_code": response.status_code
                }

    async def cancelar_cobranca(self, charge_id: str) -> Dict[str, Any]:
        """
        Cancela uma cobrança

        Args:
            charge_id: ID da cobrança

        Returns:
            Confirmação do cancelamento
        """
        logger.info(f"Cancelando cobrança: {charge_id}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/charges/{charge_id}/cancel",
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code in [200, 201, 204]:
                logger.info(f"Cobrança {charge_id} cancelada")
                return {
                    "sucesso": True,
                    "charge_id": charge_id,
                    "status": "CANCELED"
                }
            else:
                logger.error(f"Erro ao cancelar: {response.status_code} - {response.text}")
                return {
                    "sucesso": False,
                    "erro": response.text,
                    "status_code": response.status_code
                }

    async def capturar_pagamento(
        self,
        charge_id: str,
        amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Captura um pagamento pré-autorizado

        Args:
            charge_id: ID da cobrança
            amount: Valor em centavos (opcional, captura total se não informado)

        Returns:
            Dados da captura
        """
        logger.info(f"Capturando pagamento: {charge_id}")

        payload = {}
        if amount:
            payload["amount"] = {"value": amount}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/charges/{charge_id}/capture",
                json=payload if payload else None,
                headers=self.headers,
                timeout=30.0
            )

            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "sucesso": True,
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "amount": data.get("amount")
                }
            else:
                logger.error(f"Erro ao capturar: {response.status_code} - {response.text}")
                return {
                    "sucesso": False,
                    "erro": response.text,
                    "status_code": response.status_code
                }

    def processar_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa webhook do PagSeguro

        Args:
            payload: Dados recebidos do webhook

        Returns:
            Dados processados do webhook
        """
        logger.info(f"Processando webhook - Tipo: {payload.get('type')}")

        evento_tipo = payload.get("type")
        charge = payload.get("data", {}).get("charge", {})

        return {
            "tipo_evento": evento_tipo,
            "charge_id": charge.get("id"),
            "reference_id": charge.get("reference_id"),
            "status": charge.get("status"),
            "amount": charge.get("amount"),
            "paid_at": charge.get("paid_at"),
            "created_at": charge.get("created_at")
        }
