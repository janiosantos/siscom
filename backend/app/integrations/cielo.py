"""
Client para Gateway Cielo - API 3.0

Suporte a:
- Cartão de crédito
- Cartão de débito
- Tokenização
- Parcelamento
- Captura e cancelamento
- 3DS (3D Secure)

Documentação: https://developercielo.github.io/manual/cielo-ecommerce
"""
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CieloEnvironment(str, Enum):
    """Ambiente Cielo"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class CieloCardBrand(str, Enum):
    """Bandeiras suportadas"""
    VISA = "Visa"
    MASTER = "Master"
    ELO = "Elo"
    AMEX = "Amex"
    DINERS = "Diners"
    DISCOVER = "Discover"
    JCB = "JCB"
    AURA = "Aura"


class CieloPaymentType(str, Enum):
    """Tipos de pagamento"""
    CREDIT_CARD = "CreditCard"
    DEBIT_CARD = "DebitCard"
    BOLETO = "Boleto"
    PIX = "Pix"


class CieloTransactionStatus(str, Enum):
    """Status de transação"""
    NOT_FINISHED = "0"  # Não Finalizada
    AUTHORIZED = "1"  # Autorizada
    PAYMENT_CONFIRMED = "2"  # Pagamento Confirmado
    DENIED = "3"  # Negada
    VOIDED = "10"  # Cancelada
    REFUNDED = "11"  # Estornada
    PENDING = "12"  # Pendente
    ABORTED = "13"  # Abortada


class CieloClient:
    """
    Client para integração com Cielo API 3.0

    Features:
    - Pagamento com cartão (crédito/débito)
    - Tokenização de cartões
    - Parcelamento configurável
    - Captura automática ou manual
    - Cancelamento/estorno
    - Consulta de transações
    """

    def __init__(
        self,
        merchant_id: Optional[str] = None,
        merchant_key: Optional[str] = None,
        environment: CieloEnvironment = CieloEnvironment.SANDBOX
    ):
        self.merchant_id = merchant_id or getattr(settings, "CIELO_MERCHANT_ID", "")
        self.merchant_key = merchant_key or getattr(settings, "CIELO_MERCHANT_KEY", "")
        self.environment = environment

        # URLs da API
        if environment == CieloEnvironment.SANDBOX:
            self.base_url = "https://apisandbox.cieloecommerce.cielo.com.br"
            self.query_url = "https://apiquerysandbox.cieloecommerce.cielo.com.br"
        else:
            self.base_url = "https://api.cieloecommerce.cielo.com.br"
            self.query_url = "https://apiquery.cieloecommerce.cielo.com.br"

        self.headers = {
            "MerchantId": self.merchant_id,
            "MerchantKey": self.merchant_key,
            "Content-Type": "application/json",
            "RequestId": ""  # Será preenchido por requisição
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        use_query_url: bool = False
    ) -> Dict[str, Any]:
        """Fazer requisição à API Cielo"""
        base = self.query_url if use_query_url else self.base_url
        url = f"{base}/{endpoint}"

        # RequestId único para cada requisição
        request_id = f"REQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        headers = {**self.headers, "RequestId": request_id}

        logger.info(f"Cielo API request: {method} {url}", extra={
            "request_id": request_id,
            "endpoint": endpoint
        })

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=data, headers=headers)
                else:
                    raise ValueError(f"Método HTTP não suportado: {method}")

                response.raise_for_status()
                result = response.json()

                logger.info(f"Cielo API success: {response.status_code}", extra={
                    "request_id": request_id,
                    "status_code": response.status_code
                })

                return result

            except httpx.HTTPStatusError as e:
                logger.error(f"Cielo API error: {e.response.status_code}", extra={
                    "request_id": request_id,
                    "status_code": e.response.status_code,
                    "response": e.response.text
                })
                error_data = e.response.json() if e.response.text else {}
                raise Exception(f"Erro Cielo API: {error_data.get('message', str(e))}")

            except Exception as e:
                logger.error(f"Cielo request error: {str(e)}", extra={
                    "request_id": request_id,
                    "error": str(e)
                })
                raise

    # ========================================================================
    # PAGAMENTO COM CARTÃO DE CRÉDITO
    # ========================================================================

    async def create_credit_card_payment(
        self,
        amount: float,
        installments: int = 1,
        card_number: str = None,
        card_holder: str = None,
        card_expiration_date: str = None,
        card_cvv: str = None,
        card_brand: CieloCardBrand = None,
        card_token: Optional[str] = None,
        capture: bool = True,
        soft_descriptor: Optional[str] = None,
        customer: Optional[Dict[str, Any]] = None,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Criar pagamento com cartão de crédito

        Args:
            amount: Valor em reais (será convertido para centavos)
            installments: Número de parcelas (1-12)
            card_number: Número do cartão (se não usar token)
            card_holder: Nome no cartão
            card_expiration_date: Validade MM/YYYY
            card_cvv: CVV
            card_brand: Bandeira do cartão
            card_token: Token do cartão (alternativa aos dados do cartão)
            capture: Captura automática
            soft_descriptor: Texto na fatura (até 13 caracteres)
            customer: Dados do cliente
            order_id: ID do pedido no sistema

        Returns:
            Dados da transação criada
        """
        amount_cents = int(amount * 100)

        # Validar parcelas
        if not 1 <= installments <= 12:
            raise ValueError("Parcelas devem estar entre 1 e 12")

        # Merchant Order ID
        merchant_order_id = order_id or f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        payload = {
            "MerchantOrderId": merchant_order_id,
            "Customer": customer or {
                "Name": card_holder or "Cliente"
            },
            "Payment": {
                "Type": CieloPaymentType.CREDIT_CARD.value,
                "Amount": amount_cents,
                "Installments": installments,
                "Capture": capture,
                "SoftDescriptor": soft_descriptor or "Loja"[:13],
            }
        }

        # Dados do cartão ou token
        if card_token:
            payload["Payment"]["CreditCard"] = {
                "CardToken": card_token,
                "SecurityCode": card_cvv,
                "Brand": card_brand.value if card_brand else CieloCardBrand.VISA.value
            }
        else:
            if not all([card_number, card_holder, card_expiration_date, card_cvv]):
                raise ValueError("Dados do cartão incompletos")

            payload["Payment"]["CreditCard"] = {
                "CardNumber": card_number.replace(" ", "").replace("-", ""),
                "Holder": card_holder,
                "ExpirationDate": card_expiration_date.replace("/", ""),  # MMYYYY
                "SecurityCode": card_cvv,
                "Brand": card_brand.value if card_brand else self._detect_card_brand(card_number)
            }

        return await self._make_request("POST", "1/sales", payload)

    # ========================================================================
    # PAGAMENTO COM CARTÃO DE DÉBITO
    # ========================================================================

    async def create_debit_card_payment(
        self,
        amount: float,
        card_number: str,
        card_holder: str,
        card_expiration_date: str,
        card_cvv: str,
        card_brand: CieloCardBrand,
        return_url: str,
        customer: Optional[Dict[str, Any]] = None,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Criar pagamento com cartão de débito

        Débito requer autenticação 3DS (redirecionamento)

        Args:
            return_url: URL de retorno após autenticação
        """
        amount_cents = int(amount * 100)
        merchant_order_id = order_id or f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        payload = {
            "MerchantOrderId": merchant_order_id,
            "Customer": customer or {"Name": card_holder},
            "Payment": {
                "Type": CieloPaymentType.DEBIT_CARD.value,
                "Amount": amount_cents,
                "ReturnUrl": return_url,
                "DebitCard": {
                    "CardNumber": card_number.replace(" ", "").replace("-", ""),
                    "Holder": card_holder,
                    "ExpirationDate": card_expiration_date.replace("/", ""),
                    "SecurityCode": card_cvv,
                    "Brand": card_brand.value
                }
            }
        }

        return await self._make_request("POST", "1/sales", payload)

    # ========================================================================
    # TOKENIZAÇÃO
    # ========================================================================

    async def tokenize_card(
        self,
        card_number: str,
        card_holder: str,
        card_expiration_date: str,
        card_brand: CieloCardBrand
    ) -> str:
        """
        Tokenizar cartão para uso futuro (PCI compliant)

        Returns:
            Token do cartão
        """
        payload = {
            "CustomerName": card_holder,
            "CardNumber": card_number.replace(" ", "").replace("-", ""),
            "Holder": card_holder,
            "ExpirationDate": card_expiration_date.replace("/", ""),
            "Brand": card_brand.value
        }

        result = await self._make_request("POST", "1/card", payload)
        return result.get("CardToken")

    # ========================================================================
    # CAPTURA E CANCELAMENTO
    # ========================================================================

    async def capture_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Capturar pagamento previamente autorizado

        Args:
            payment_id: ID do pagamento
            amount: Valor a capturar (None = valor total)
        """
        endpoint = f"1/sales/{payment_id}/capture"

        if amount:
            amount_cents = int(amount * 100)
            endpoint += f"?amount={amount_cents}"

        return await self._make_request("PUT", endpoint)

    async def cancel_payment(
        self,
        payment_id: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Cancelar/estornar pagamento

        Args:
            payment_id: ID do pagamento
            amount: Valor a cancelar (None = valor total)
        """
        endpoint = f"1/sales/{payment_id}/void"

        if amount:
            amount_cents = int(amount * 100)
            endpoint += f"?amount={amount_cents}"

        return await self._make_request("PUT", endpoint)

    # ========================================================================
    # CONSULTAS
    # ========================================================================

    async def query_payment(self, payment_id: str) -> Dict[str, Any]:
        """Consultar pagamento por ID"""
        return await self._make_request(
            "GET",
            f"1/sales/{payment_id}",
            use_query_url=True
        )

    async def query_payment_by_order(self, order_id: str) -> Dict[str, Any]:
        """Consultar pagamento por OrderId"""
        return await self._make_request(
            "GET",
            f"1/sales?merchantOrderId={order_id}",
            use_query_url=True
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _detect_card_brand(self, card_number: str) -> str:
        """Detectar bandeira do cartão pelo número"""
        card_number = card_number.replace(" ", "").replace("-", "")

        # Regras de detecção
        if card_number[0] == "4":
            return CieloCardBrand.VISA.value
        elif card_number[:2] in ["51", "52", "53", "54", "55"]:
            return CieloCardBrand.MASTER.value
        elif card_number[:4] in ["4011", "4312", "4389", "4514", "4576"]:
            return CieloCardBrand.ELO.value
        elif card_number[:2] in ["34", "37"]:
            return CieloCardBrand.AMEX.value
        elif card_number[:2] in ["36", "38"]:
            return CieloCardBrand.DINERS.value

        # Default
        return CieloCardBrand.VISA.value

    def format_status(self, status_code: str) -> str:
        """Formatar status da transação"""
        status_map = {
            "0": "Não Finalizada",
            "1": "Autorizada",
            "2": "Pagamento Confirmado",
            "3": "Negada",
            "10": "Cancelada",
            "11": "Estornada",
            "12": "Pendente",
            "13": "Abortada"
        }
        return status_map.get(str(status_code), "Desconhecido")

    def is_success(self, payment_response: Dict[str, Any]) -> bool:
        """Verificar se pagamento foi bem-sucedido"""
        payment = payment_response.get("Payment", {})
        status = str(payment.get("Status", ""))
        return status in ["1", "2"]  # Autorizada ou Confirmada
