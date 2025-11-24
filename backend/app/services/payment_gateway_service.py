"""
Serviço unificado de Payment Gateway

Interface única para múltiplos gateways de pagamento:
- Cielo
- GetNet (Santander)
- Mercado Pago

Suporta:
- Cartão de crédito (com parcelamento)
- Cartão de débito
- PIX
- Tokenização
- Captura e cancelamento
"""
from typing import Dict, Any, Optional, Literal
from decimal import Decimal
from enum import Enum
from datetime import datetime
import uuid

from app.integrations.cielo import CieloClient, CieloEnvironment, CieloPaymentType
from app.integrations.getnet import GetNetClient, GetNetEnvironment, GetNetPaymentType
from app.integrations.mercadopago import MercadoPagoClient
from app.core.logging import get_logger
from app.core.exceptions import BusinessRuleException, ValidationException
from app.utils.retry import with_retry, RETRYABLE_HTTP_EXCEPTIONS

logger = get_logger(__name__)


class PaymentGateway(str, Enum):
    """Gateways suportados"""
    CIELO = "cielo"
    GETNET = "getnet"
    MERCADOPAGO = "mercadopago"


class PaymentMethod(str, Enum):
    """Métodos de pagamento"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PIX = "pix"


class PaymentStatus(str, Enum):
    """Status de pagamento unificado"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    DENIED = "denied"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentGatewayService:
    """
    Serviço unificado de pagamento

    Abstrai complexidade de múltiplos gateways em interface única
    """

    def __init__(self):
        """Inicializa clients dos gateways"""
        self.cielo = CieloClient(environment=CieloEnvironment.SANDBOX)
        self.getnet = GetNetClient(environment=GetNetEnvironment.SANDBOX)
        self.mercadopago = None  # Será inicializado com credenciais

    def initialize_mercadopago(self, access_token: str, public_key: Optional[str] = None):
        """Inicializa MercadoPago com credenciais"""
        self.mercadopago = MercadoPagoClient(
            access_token=access_token,
            public_key=public_key
        )

    async def create_payment(
        self,
        gateway: PaymentGateway,
        payment_method: PaymentMethod,
        amount: Decimal,
        order_id: str,
        customer_data: Dict[str, Any],
        card_data: Optional[Dict[str, Any]] = None,
        installments: int = 1,
        capture: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Cria pagamento em qualquer gateway

        Args:
            gateway: Gateway a ser usado (cielo, getnet, mercadopago)
            payment_method: Método de pagamento (cartão, pix)
            amount: Valor do pagamento
            order_id: ID do pedido/venda
            customer_data: Dados do cliente (nome, cpf, email)
            card_data: Dados do cartão (se aplicável)
            installments: Número de parcelas (padrão: 1)
            capture: Auto-captura (padrão: True)
            metadata: Metadados adicionais

        Returns:
            Dados do pagamento criado (normalizados)
        """
        logger.info(
            f"Criando pagamento - Gateway: {gateway}, Método: {payment_method}, "
            f"Valor: {amount}, Pedido: {order_id}"
        )

        # Valida valor mínimo
        if amount < Decimal("0.01"):
            raise BusinessRuleException("Valor mínimo de pagamento é R$ 0,01")

        # Valida número de parcelas
        if installments < 1 or installments > 12:
            raise BusinessRuleException("Número de parcelas deve estar entre 1 e 12")

        # Roteamento por gateway
        if gateway == PaymentGateway.CIELO:
            return await self._create_cielo_payment(
                payment_method, amount, order_id, customer_data,
                card_data, installments, capture, metadata
            )
        elif gateway == PaymentGateway.GETNET:
            return await self._create_getnet_payment(
                payment_method, amount, order_id, customer_data,
                card_data, installments, capture, metadata
            )
        elif gateway == PaymentGateway.MERCADOPAGO:
            return await self._create_mercadopago_payment(
                payment_method, amount, order_id, customer_data,
                card_data, installments, metadata
            )
        else:
            raise BusinessRuleException(f"Gateway não suportado: {gateway}")

    @with_retry(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=30.0,
        retryable_exceptions=RETRYABLE_HTTP_EXCEPTIONS
    )
    async def _create_cielo_payment(
        self,
        payment_method: PaymentMethod,
        amount: Decimal,
        order_id: str,
        customer_data: Dict[str, Any],
        card_data: Optional[Dict[str, Any]],
        installments: int,
        capture: bool,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Cria pagamento na Cielo com retry automático"""

        if payment_method == PaymentMethod.PIX:
            # Cielo não tem método create_pix_payment ainda
            raise BusinessRuleException("PIX não disponível na Cielo no momento")

        elif payment_method == PaymentMethod.CREDIT_CARD:
            if not card_data:
                raise BusinessRuleException("Dados do cartão são obrigatórios")

            # Converter brand string para enum CieloCardBrand
            from app.integrations.cielo import CieloCardBrand
            brand_str = card_data.get("brand", "visa").upper()
            brand_map = {
                "VISA": CieloCardBrand.VISA,
                "MASTERCARD": CieloCardBrand.MASTER,
                "MASTER": CieloCardBrand.MASTER,
                "ELO": CieloCardBrand.ELO,
                "AMEX": CieloCardBrand.AMEX,
                "DINERS": CieloCardBrand.DINERS
            }
            card_brand = brand_map.get(brand_str, CieloCardBrand.VISA)

            result = await self.cielo.create_credit_card_payment(
                amount=float(amount),
                installments=installments,
                order_id=order_id,
                customer={"Name": customer_data.get("name", "Cliente")},
                card_number=card_data.get("number"),
                card_holder=card_data.get("holder"),
                card_expiration_date=card_data.get("expiration"),
                card_cvv=card_data.get("cvv"),
                card_brand=card_brand,
                capture=capture
            )

        elif payment_method == PaymentMethod.DEBIT_CARD:
            if not card_data:
                raise BusinessRuleException("Dados do cartão são obrigatórios")

            # Converter brand string para enum CieloCardBrand
            from app.integrations.cielo import CieloCardBrand
            brand_str = card_data.get("brand", "visa").upper()
            brand_map = {
                "VISA": CieloCardBrand.VISA,
                "MASTERCARD": CieloCardBrand.MASTER,
                "MASTER": CieloCardBrand.MASTER
            }
            card_brand = brand_map.get(brand_str, CieloCardBrand.VISA)

            return_url = (metadata.get("return_url") if metadata
                         else "https://loja.com.br/retorno")

            result = await self.cielo.create_debit_card_payment(
                amount=float(amount),
                order_id=order_id,
                customer={"Name": customer_data.get("name", "Cliente")},
                card_number=card_data.get("number"),
                card_holder=card_data.get("holder"),
                card_expiration_date=card_data.get("expiration"),
                card_cvv=card_data.get("cvv"),
                card_brand=card_brand,
                return_url=return_url
            )
        else:
            raise BusinessRuleException(f"Método de pagamento não suportado: {payment_method}")

        # Normaliza resposta
        return self._normalize_response(PaymentGateway.CIELO, result)

    @with_retry(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=30.0,
        retryable_exceptions=RETRYABLE_HTTP_EXCEPTIONS
    )
    async def _create_getnet_payment(
        self,
        payment_method: PaymentMethod,
        amount: Decimal,
        order_id: str,
        customer_data: Dict[str, Any],
        card_data: Optional[Dict[str, Any]],
        installments: int,
        capture: bool,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Cria pagamento na GetNet com retry automático"""

        if payment_method == PaymentMethod.PIX:
            result = await self.getnet.create_pix_payment(
                amount=float(amount),
                order_id=order_id,
                customer_name=customer_data.get("name", "Cliente"),
                customer_document=customer_data.get("cpf", "00000000000")
            )

        elif payment_method == PaymentMethod.CREDIT_CARD:
            if not card_data:
                raise BusinessRuleException("Dados do cartão são obrigatórios")

            # GetNet precisa de customer_id, usar CPF/documento como fallback
            customer_id = customer_data.get("document_number") or customer_data.get("cpf", "customer-123")

            # Parse expiration (MM/YYYY) para month e year
            expiration = card_data.get("expiration", "12/2025")
            month, year = expiration.split("/") if "/" in expiration else ("12", "2025")

            result = await self.getnet.create_credit_card_payment(
                amount=float(amount),
                installments=installments,
                order_id=order_id,
                customer_id=customer_id,
                card_number=card_data.get("number"),
                card_holder_name=card_data.get("holder"),
                card_expiration_month=month,
                card_expiration_year=year,
                card_cvv=card_data.get("cvv"),
                capture=capture
            )

        elif payment_method == PaymentMethod.DEBIT_CARD:
            if not card_data:
                raise BusinessRuleException("Dados do cartão são obrigatórios")

            # GetNet precisa de customer_id
            customer_id = customer_data.get("document_number") or customer_data.get("cpf", "customer-123")

            # Parse expiration (MM/YYYY) para month e year
            expiration = card_data.get("expiration", "12/2025")
            month, year = expiration.split("/") if "/" in expiration else ("12", "2025")

            result = await self.getnet.create_debit_card_payment(
                amount=float(amount),
                order_id=order_id,
                customer_id=customer_id,
                card_number=card_data.get("number"),
                card_holder_name=card_data.get("holder"),
                card_expiration_month=month,
                card_expiration_year=year,
                card_cvv=card_data.get("cvv")
            )
        else:
            raise BusinessRuleException(f"Método de pagamento não suportado: {payment_method}")

        # Normaliza resposta
        return self._normalize_response(PaymentGateway.GETNET, result)

    @with_retry(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=30.0,
        retryable_exceptions=RETRYABLE_HTTP_EXCEPTIONS
    )
    async def _create_mercadopago_payment(
        self,
        payment_method: PaymentMethod,
        amount: Decimal,
        order_id: str,
        customer_data: Dict[str, Any],
        card_data: Optional[Dict[str, Any]],
        installments: int,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Cria pagamento no Mercado Pago com retry automático"""

        if not self.mercadopago:
            raise BusinessRuleException("MercadoPago não inicializado. Use initialize_mercadopago()")

        if payment_method == PaymentMethod.PIX:
            result = await self.mercadopago.criar_pagamento_pix(
                valor=amount,
                descricao=f"Pedido #{order_id}",
                email_pagador=customer_data.get("email"),
                external_reference=order_id
            )
        elif payment_method == PaymentMethod.CREDIT_CARD:
            if not card_data:
                raise BusinessRuleException("Dados do cartão são obrigatórios")

            result = await self.mercadopago.criar_pagamento_cartao(
                valor=amount,
                parcelas=installments,
                descricao=f"Pedido #{order_id}",
                email_pagador=customer_data.get("email"),
                card_token=card_data.get("token"),  # Token gerado pelo frontend
                external_reference=order_id
            )
        else:
            raise BusinessRuleException(f"Método de pagamento não suportado: {payment_method}")

        # Normaliza resposta
        return self._normalize_response(PaymentGateway.MERCADOPAGO, result)

    def _normalize_response(
        self,
        gateway: PaymentGateway,
        raw_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normaliza resposta de diferentes gateways em formato único

        Returns:
            {
                "gateway": "cielo",
                "payment_id": "abc123",
                "transaction_id": "xyz789",
                "status": "authorized",
                "amount": 100.00,
                "installments": 3,
                "captured": False,
                "pix_qrcode": "...",  # se PIX
                "raw_response": {...}
            }
        """
        normalized = {
            "gateway": gateway.value,
            "raw_response": raw_response,
            "created_at": datetime.utcnow().isoformat()
        }

        if gateway == PaymentGateway.CIELO:
            # Extrair dados do objeto Payment (Cielo retorna tudo dentro de Payment)
            payment = raw_response.get("Payment", {})
            normalized.update({
                "payment_id": payment.get("PaymentId"),
                "transaction_id": payment.get("Tid"),
                "status": self._map_cielo_status(payment.get("Status")),
                "amount": payment.get("Amount", 0) / 100,  # Cielo usa centavos
                "installments": payment.get("Installments", 1),
                "captured": payment.get("Capture", False),
                "authorization_code": payment.get("AuthorizationCode"),
                "pix_qrcode": payment.get("QrCodeString"),
            })

        elif gateway == PaymentGateway.GETNET:
            normalized.update({
                "payment_id": raw_response.get("payment_id"),
                "transaction_id": raw_response.get("order_id"),
                "status": self._map_getnet_status(raw_response.get("status")),
                "amount": raw_response.get("amount", 0) / 100,  # GetNet usa centavos
                "installments": raw_response.get("installments", 1),
                "captured": raw_response.get("status") == "APPROVED",
                "authorization_code": raw_response.get("authorization_code"),
                "pix_qrcode": raw_response.get("qr_code"),
            })

        elif gateway == PaymentGateway.MERCADOPAGO:
            normalized.update({
                "payment_id": str(raw_response.get("id")),
                "transaction_id": raw_response.get("external_reference"),
                "status": self._map_mercadopago_status(raw_response.get("status")),
                "amount": float(raw_response.get("valor", 0)),
                "installments": raw_response.get("installments", 1),
                "captured": raw_response.get("status") == "approved",
                "pix_qrcode": raw_response.get("qr_code"),
            })

        return normalized

    def _map_cielo_status(self, cielo_status: Optional[str]) -> PaymentStatus:
        """Mapeia status da Cielo para status unificado"""
        mapping = {
            "0": PaymentStatus.PENDING,      # Não finalizada
            "1": PaymentStatus.AUTHORIZED,   # Autorizada
            "2": PaymentStatus.CAPTURED,     # Capturada
            "3": PaymentStatus.DENIED,       # Negada
            "10": PaymentStatus.CANCELLED,   # Cancelada
            "11": PaymentStatus.REFUNDED,    # Estornada
            "12": PaymentStatus.PENDING,     # Pendente
            "13": PaymentStatus.CANCELLED,   # Abortada
        }
        return mapping.get(str(cielo_status), PaymentStatus.PENDING)

    def _map_getnet_status(self, getnet_status: Optional[str]) -> PaymentStatus:
        """Mapeia status da GetNet para status unificado"""
        mapping = {
            "PENDING": PaymentStatus.PENDING,
            "AUTHORIZED": PaymentStatus.AUTHORIZED,
            "APPROVED": PaymentStatus.CAPTURED,
            "DENIED": PaymentStatus.DENIED,
            "CANCELED": PaymentStatus.CANCELLED,
            "REFUNDED": PaymentStatus.REFUNDED,
        }
        return mapping.get(getnet_status, PaymentStatus.PENDING)

    def _map_mercadopago_status(self, mp_status: Optional[str]) -> PaymentStatus:
        """Mapeia status do MercadoPago para status unificado"""
        mapping = {
            "pending": PaymentStatus.PENDING,
            "authorized": PaymentStatus.AUTHORIZED,
            "approved": PaymentStatus.CAPTURED,
            "rejected": PaymentStatus.DENIED,
            "cancelled": PaymentStatus.CANCELLED,
            "refunded": PaymentStatus.REFUNDED,
        }
        return mapping.get(mp_status, PaymentStatus.PENDING)

    @with_retry(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=10.0,
        retryable_exceptions=RETRYABLE_HTTP_EXCEPTIONS
    )
    async def capture_payment(
        self,
        gateway: PaymentGateway,
        payment_id: str,
        amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Captura pagamento pré-autorizado com retry automático

        Args:
            gateway: Gateway usado
            payment_id: ID do pagamento
            amount: Valor a capturar (None = captura total)
        """
        logger.info(f"Capturando pagamento - Gateway: {gateway}, ID: {payment_id}")

        if gateway == PaymentGateway.CIELO:
            result = await self.cielo.capture_payment(
                payment_id=payment_id,
                amount=int(amount * 100) if amount else None  # Centavos
            )
        elif gateway == PaymentGateway.GETNET:
            result = await self.getnet.capture_payment(
                payment_id=payment_id
            )
        else:
            raise BusinessRuleException(f"Gateway {gateway} não suporta captura manual")

        return self._normalize_response(gateway, result)

    @with_retry(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=10.0,
        retryable_exceptions=RETRYABLE_HTTP_EXCEPTIONS
    )
    async def cancel_payment(
        self,
        gateway: PaymentGateway,
        payment_id: str,
        amount: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Cancela/estorna pagamento com retry automático

        Args:
            gateway: Gateway usado
            payment_id: ID do pagamento
            amount: Valor a cancelar (None = cancelamento total)
        """
        logger.info(f"Cancelando pagamento - Gateway: {gateway}, ID: {payment_id}")

        if gateway == PaymentGateway.CIELO:
            result = await self.cielo.cancel_payment(
                payment_id=payment_id,
                amount=int(amount * 100) if amount else None  # Centavos
            )
        elif gateway == PaymentGateway.GETNET:
            result = await self.getnet.cancel_payment(
                payment_id=payment_id
            )
        elif gateway == PaymentGateway.MERCADOPAGO:
            if not self.mercadopago:
                raise BusinessRuleException("MercadoPago não inicializado")
            result = await self.mercadopago.cancelar_pagamento(
                payment_id=int(payment_id)
            )
        else:
            raise BusinessRuleException(f"Gateway {gateway} não suporta cancelamento")

        return self._normalize_response(gateway, result)

    @with_retry(
        max_attempts=3,
        initial_delay=0.5,
        max_delay=5.0,
        retryable_exceptions=RETRYABLE_HTTP_EXCEPTIONS
    )
    async def query_payment(
        self,
        gateway: PaymentGateway,
        payment_id: str
    ) -> Dict[str, Any]:
        """
        Consulta status de um pagamento com retry automático

        Args:
            gateway: Gateway usado
            payment_id: ID do pagamento
        """
        logger.info(f"Consultando pagamento - Gateway: {gateway}, ID: {payment_id}")

        if gateway == PaymentGateway.CIELO:
            result = await self.cielo.query_payment(payment_id=payment_id)
        elif gateway == PaymentGateway.GETNET:
            result = await self.getnet.query_payment(payment_id=payment_id)
        elif gateway == PaymentGateway.MERCADOPAGO:
            if not self.mercadopago:
                raise BusinessRuleException("MercadoPago não inicializado")
            result = await self.mercadopago.consultar_pagamento(
                payment_id=int(payment_id)
            )
        else:
            raise BusinessRuleException(f"Gateway {gateway} não suportado")

        return self._normalize_response(gateway, result)

    # ============================================
    # TOKENIZAÇÃO DE CARTÕES (PCI COMPLIANCE)
    # ============================================

    async def tokenize_card(
        self,
        gateway: PaymentGateway,
        card_data: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Tokeniza cartão de crédito para uso futuro (PCI compliant)

        Permite armazenar token ao invés de dados sensíveis do cartão.

        Args:
            gateway: Gateway para tokenização
            card_data: Dados do cartão
                - number: Número do cartão
                - holder: Nome do titular (obrigatório para Cielo)
                - expiration: Data de expiração MM/YYYY (obrigatório para Cielo)
                - brand: Bandeira do cartão (obrigatório para Cielo)
            customer_data: Dados do cliente
                - customer_id: ID do cliente (obrigatório para GetNet)

        Returns:
            Dict contendo:
                - gateway: Gateway usado
                - card_token: Token do cartão
                - last_digits: Últimos 4 dígitos (se disponível)
                - created_at: Data/hora da tokenização

        Raises:
            BusinessRuleException: Se gateway não suportar tokenização
            ValidationException: Se dados obrigatórios estiverem faltando

        Example:
            >>> token_data = await service.tokenize_card(
            ...     gateway=PaymentGateway.CIELO,
            ...     card_data={
            ...         "number": "4532000000000000",
            ...         "holder": "JOÃO SILVA",
            ...         "expiration": "12/2028",
            ...         "brand": "Visa"
            ...     }
            ... )
            >>> print(token_data["card_token"])
        """
        logger.info(f"Tokenizando cartão - Gateway: {gateway}")

        # Validar dados obrigatórios
        if not card_data.get("number"):
            raise ValidationException("Número do cartão é obrigatório")

        if gateway == PaymentGateway.CIELO:
            token = await self._tokenize_cielo_card(card_data)
        elif gateway == PaymentGateway.GETNET:
            token = await self._tokenize_getnet_card(card_data, customer_data)
        else:
            raise BusinessRuleException(
                f"Gateway {gateway} não suporta tokenização de cartão"
            )

        # Extrair últimos 4 dígitos
        card_number = card_data["number"].replace(" ", "").replace("-", "")
        last_digits = card_number[-4:]

        logger.info(
            f"Cartão tokenizado com sucesso - Gateway: {gateway}",
            extra={"last_digits": last_digits}
        )

        return {
            "gateway": gateway.value,
            "card_token": token,
            "last_digits": last_digits,
            "created_at": datetime.utcnow().isoformat()
        }

    async def _tokenize_cielo_card(self, card_data: Dict[str, Any]) -> str:
        """
        Tokeniza cartão na Cielo

        Requer: number, holder, expiration, brand
        """
        # Validar campos obrigatórios
        required = ["holder", "expiration", "brand"]
        missing = [f for f in required if not card_data.get(f)]
        if missing:
            raise ValidationException(
                f"Campos obrigatórios para Cielo: {', '.join(missing)}"
            )

        # Converter brand para enum se string
        brand = card_data["brand"]
        if isinstance(brand, str):
            from app.integrations.cielo import CieloCardBrand
            try:
                brand = CieloCardBrand(brand.upper())
            except ValueError:
                # Tentar mapear nomes comuns
                brand_map = {
                    "VISA": CieloCardBrand.VISA,
                    "MASTER": CieloCardBrand.MASTER,
                    "MASTERCARD": CieloCardBrand.MASTER,
                    "ELO": CieloCardBrand.ELO,
                    "AMEX": CieloCardBrand.AMEX,
                    "DINERS": CieloCardBrand.DINERS,
                    "DISCOVER": CieloCardBrand.DISCOVER,
                    "JCB": CieloCardBrand.JCB,
                    "AURA": CieloCardBrand.AURA
                }
                brand = brand_map.get(card_data["brand"].upper())
                if not brand:
                    raise ValidationException(
                        f"Bandeira inválida: {card_data['brand']}"
                    )

        token = await self.cielo.tokenize_card(
            card_number=card_data["number"],
            card_holder=card_data["holder"],
            card_expiration_date=card_data["expiration"],
            card_brand=brand
        )

        return token

    async def _tokenize_getnet_card(
        self,
        card_data: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Tokeniza cartão na GetNet

        Requer: number, customer_id
        """
        if not customer_data or not customer_data.get("customer_id"):
            raise ValidationException(
                "customer_id é obrigatório para tokenização GetNet"
            )

        token = await self.getnet.tokenize_card(
            card_number=card_data["number"],
            customer_id=customer_data["customer_id"]
        )

        return token
