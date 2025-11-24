"""
Integração com GetNet (Santander)
Gateway de pagamento completo: Cartão + PIX + Tokenização
"""
import httpx
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import hashlib
import json


class GetNetEnvironment(str, Enum):
    """Ambientes GetNet"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class GetNetCardBrand(str, Enum):
    """Bandeiras de cartão suportadas"""
    VISA = "Visa"
    MASTERCARD = "Mastercard"
    AMEX = "Amex"
    ELO = "Elo"
    HIPERCARD = "Hipercard"


class GetNetPaymentType(str, Enum):
    """Tipos de pagamento"""
    CREDIT = "credit"
    DEBIT = "debit"


class GetNetClient:
    """
    Cliente para integração com GetNet API

    Documentação: https://developers.getnet.com.br/api
    """

    def __init__(
        self,
        seller_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        environment: GetNetEnvironment = GetNetEnvironment.SANDBOX
    ):
        self.seller_id = seller_id or "SELLER_ID_SANDBOX"
        self.client_id = client_id or "CLIENT_ID_SANDBOX"
        self.client_secret = client_secret or "CLIENT_SECRET_SANDBOX"
        self.environment = environment

        # URLs por ambiente
        if environment == GetNetEnvironment.SANDBOX:
            self.base_url = "https://api-sandbox.getnet.com.br"
            self.auth_url = "https://api-sandbox.getnet.com.br/auth/oauth/v2/token"
        else:
            self.base_url = "https://api.getnet.com.br"
            self.auth_url = "https://api.getnet.com.br/auth/oauth/v2/token"

        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """
        Obtém access token OAuth2
        """
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.auth_url,
                auth=(self.client_id, self.client_secret),
                data={
                    "scope": "oob",
                    "grant_type": "client_credentials"
                }
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Faz requisição autenticada para API GetNet
        """
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "seller_id": self.seller_id
        }

        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    def _detect_card_brand(self, card_number: str) -> str:
        """
        Detecta a bandeira do cartão pelo número
        """
        # Remove espaços e traços
        card_number = card_number.replace(" ", "").replace("-", "")

        # Padrões de bandeiras - Ordem importa! Mais específicos primeiro
        # Elo (deve vir antes de Visa pois alguns bins começam com 4)
        if card_number[:4] in ["4011", "4312", "4389", "4514", "4576", "5067", "6277", "6362", "6363"]:
            return GetNetCardBrand.ELO.value
        # Hipercard
        elif card_number[:3] in ["384", "606"]:
            return GetNetCardBrand.HIPERCARD.value
        # Amex
        elif card_number[:2] in ["34", "37"]:
            return GetNetCardBrand.AMEX.value
        # Mastercard
        elif card_number[:2] in ["51", "52", "53", "54", "55"] or card_number[:4] in ["2221", "2720"]:
            return GetNetCardBrand.MASTERCARD.value
        # Visa (genérico - deve ser último)
        elif card_number[0] == "4":
            return GetNetCardBrand.VISA.value

        return GetNetCardBrand.VISA.value

    # ============================================================================
    # CARTÃO DE CRÉDITO
    # ============================================================================

    async def create_credit_card_payment(
        self,
        amount: float,
        order_id: str,
        customer_id: str,
        card_number: Optional[str] = None,
        card_holder_name: Optional[str] = None,
        card_expiration_month: Optional[str] = None,
        card_expiration_year: Optional[str] = None,
        card_cvv: Optional[str] = None,
        card_token: Optional[str] = None,
        installments: int = 1,
        capture: bool = True,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria pagamento com cartão de crédito

        Args:
            amount: Valor em reais (ex: 100.50)
            order_id: ID do pedido
            customer_id: ID do cliente
            card_number: Número do cartão (se não usar token)
            card_holder_name: Nome do titular
            card_expiration_month: Mês de expiração (MM)
            card_expiration_year: Ano de expiração (YY)
            card_cvv: CVV
            card_token: Token do cartão (alternativa aos dados do cartão)
            installments: Número de parcelas (1-12)
            capture: Captura automática ou manual
            description: Descrição da compra
        """
        if installments < 1 or installments > 12:
            raise ValueError("Parcelas devem estar entre 1 e 12")

        # Converter valor para centavos
        amount_cents = int(amount * 100)

        # Dados do cartão
        if card_token:
            card_data = {
                "number_token": card_token,
                "security_code": card_cvv
            }
        else:
            if not all([card_number, card_holder_name, card_expiration_month, card_expiration_year, card_cvv]):
                raise ValueError("Dados do cartão incompletos")

            card_brand = self._detect_card_brand(card_number)

            card_data = {
                "number_token": None,
                "cardholder_name": card_holder_name,
                "security_code": card_cvv,
                "brand": card_brand,
                "number": card_number,
                "expiration_month": card_expiration_month,
                "expiration_year": card_expiration_year
            }

        payload = {
            "seller_id": self.seller_id,
            "amount": amount_cents,
            "currency": "BRL",
            "order": {
                "order_id": order_id,
                "sales_tax": 0,
                "product_type": "service"
            },
            "customer": {
                "customer_id": customer_id,
                "first_name": card_holder_name.split()[0] if card_holder_name else "Cliente",
                "last_name": " ".join(card_holder_name.split()[1:]) if card_holder_name and len(card_holder_name.split()) > 1 else "GetNet",
                "document_type": "CPF",
                "document_number": "12345678909"
            },
            "credit": {
                "delayed": not capture,
                "save_card_data": False,
                "transaction_type": "INSTALL_NO_INTEREST" if installments > 1 else "FULL",
                "number_installments": installments,
                "card": card_data
            }
        }

        if description:
            payload["order"]["description"] = description

        return await self._make_request("POST", "/v1/payments/credit", data=payload)

    # ============================================================================
    # CARTÃO DE DÉBITO
    # ============================================================================

    async def create_debit_card_payment(
        self,
        amount: float,
        order_id: str,
        customer_id: str,
        card_number: str,
        card_holder_name: str,
        card_expiration_month: str,
        card_expiration_year: str,
        card_cvv: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria pagamento com cartão de débito
        Requer autenticação 3DS
        """
        amount_cents = int(amount * 100)
        card_brand = self._detect_card_brand(card_number)

        payload = {
            "seller_id": self.seller_id,
            "amount": amount_cents,
            "currency": "BRL",
            "order": {
                "order_id": order_id,
                "sales_tax": 0,
                "product_type": "service"
            },
            "customer": {
                "customer_id": customer_id,
                "first_name": card_holder_name.split()[0],
                "last_name": " ".join(card_holder_name.split()[1:]) if len(card_holder_name.split()) > 1 else "GetNet",
                "document_type": "CPF",
                "document_number": "12345678909"
            },
            "debit": {
                "card": {
                    "number_token": None,
                    "cardholder_name": card_holder_name,
                    "security_code": card_cvv,
                    "brand": card_brand,
                    "number": card_number,
                    "expiration_month": card_expiration_month,
                    "expiration_year": card_expiration_year
                },
                "authenticate": True,
                "soft_descriptor": "LOJA MATERIAIS"
            }
        }

        if description:
            payload["order"]["description"] = description

        return await self._make_request("POST", "/v1/payments/debit", data=payload)

    # ============================================================================
    # PIX
    # ============================================================================

    async def create_pix_payment(
        self,
        amount: float,
        order_id: str,
        customer_id: str,
        customer_name: str,
        customer_document: str,
        expiration_minutes: int = 30,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria pagamento PIX com QR Code

        Returns:
            Dict com qr_code (base64), qr_code_text (copia e cola) e payment_id
        """
        amount_cents = int(amount * 100)

        payload = {
            "seller_id": self.seller_id,
            "amount": amount_cents,
            "currency": "BRL",
            "order": {
                "order_id": order_id,
                "sales_tax": 0,
                "product_type": "service"
            },
            "customer": {
                "customer_id": customer_id,
                "first_name": customer_name.split()[0],
                "last_name": " ".join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else "GetNet",
                "document_type": "CPF" if len(customer_document) == 11 else "CNPJ",
                "document_number": customer_document
            },
            "pix": {
                "expiration_time": expiration_minutes
            }
        }

        if description:
            payload["order"]["description"] = description

        return await self._make_request("POST", "/v1/payments/pix", data=payload)

    # ============================================================================
    # TOKENIZAÇÃO
    # ============================================================================

    async def tokenize_card(
        self,
        card_number: str,
        customer_id: str
    ) -> str:
        """
        Tokeniza cartão para uso futuro (PCI compliant)

        Returns:
            Token do cartão
        """
        payload = {
            "card_number": card_number,
            "customer_id": customer_id
        }

        response = await self._make_request("POST", "/v1/tokens/card", data=payload)
        return response["number_token"]

    # ============================================================================
    # CAPTURA E CANCELAMENTO
    # ============================================================================

    async def capture_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Captura pagamento pré-autorizado

        Args:
            payment_id: ID do pagamento
            amount: Valor a capturar (None = valor total)
        """
        payload = {}

        if amount is not None:
            payload["amount"] = int(amount * 100)

        return await self._make_request(
            "POST",
            f"/v1/payments/credit/{payment_id}/confirm",
            data=payload if payload else None
        )

    async def cancel_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Cancela/estorna pagamento

        Args:
            payment_id: ID do pagamento
            amount: Valor a cancelar (None = valor total)
        """
        payload = {}

        if amount is not None:
            payload["amount"] = int(amount * 100)

        return await self._make_request(
            "POST",
            f"/v1/payments/credit/{payment_id}/cancel",
            data=payload if payload else None
        )

    # ============================================================================
    # CONSULTAS
    # ============================================================================

    async def query_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Consulta status de um pagamento
        """
        return await self._make_request("GET", f"/v1/payments/credit/{payment_id}")

    async def query_pix_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Consulta status de um pagamento PIX
        """
        return await self._make_request("GET", f"/v1/payments/pix/{payment_id}")

    # ============================================================================
    # UTILIDADES
    # ============================================================================

    def format_status(self, status: str) -> str:
        """
        Formata status legível
        """
        status_map = {
            "PENDING": "Pendente",
            "AUTHORIZED": "Autorizado",
            "CONFIRMED": "Confirmado",
            "CANCELED": "Cancelado",
            "DENIED": "Negado",
            "ERROR": "Erro"
        }
        return status_map.get(status, status)

    def is_success(self, response: Dict[str, Any]) -> bool:
        """
        Verifica se pagamento foi bem-sucedido
        """
        status = response.get("status", "")
        return status in ["AUTHORIZED", "CONFIRMED"]
