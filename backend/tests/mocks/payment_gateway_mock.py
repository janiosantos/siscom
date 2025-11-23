"""
Mock server para simular gateways de pagamento

Simula respostas realistas de:
- Cielo
- GetNet
- Mercado Pago

Mantém estado de transações para simular captura, cancelamento, consulta
"""
import uuid
import random
from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from enum import Enum


class MockPaymentStatus(str, Enum):
    """Status de pagamento simulados"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    APPROVED = "approved"
    CAPTURED = "captured"
    DENIED = "denied"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentGatewayMock:
    """
    Mock unificado de gateways de pagamento

    Simula comportamento real dos gateways mantendo estado
    """

    def __init__(self):
        """Inicializa mock com storage de transações"""
        self.transactions: Dict[str, Dict[str, Any]] = {}
        self.pix_payments: Dict[str, Dict[str, Any]] = {}

    def reset(self):
        """Limpa estado do mock"""
        self.transactions.clear()
        self.pix_payments.clear()

    # ============================================
    # CIELO MOCK
    # ============================================

    def cielo_create_card_payment(
        self,
        amount: float,
        installments: int = 1,
        merchant_order_id: str = None,
        customer_name: str = "Cliente Teste",
        card_number: str = "4532000000000000",
        card_holder: str = "TITULAR TESTE",
        card_expiration: str = "12/2028",
        card_cvv: str = "123",
        card_brand: str = "Visa",
        payment_type: str = "CreditCard",
        capture: bool = True
    ) -> Dict[str, Any]:
        """Mock de pagamento com cartão na Cielo"""

        payment_id = str(uuid.uuid4())
        tid = f"TID{random.randint(100000, 999999)}"

        # Simula aprovação (90% de chance)
        approved = random.random() < 0.9

        if approved:
            status = "2" if capture else "1"  # 2=Capturada, 1=Autorizada
            return_code = "4"  # Autorizada
            return_message = "Operacao realizada com sucesso"
        else:
            status = "3"  # Negada
            return_code = "05"
            return_message = "Não Autorizada"

        # Armazena transação
        transaction = {
            "PaymentId": payment_id,
            "Type": payment_type,
            "Amount": int(amount * 100),  # Centavos
            "Installments": installments,
            "ReceivedDate": datetime.utcnow().isoformat(),
            "CapturedAmount": int(amount * 100) if capture else 0,
            "CapturedDate": datetime.utcnow().isoformat() if capture else None,
            "Status": status,
            "IsSplitted": False,
            "ReturnCode": return_code,
            "ReturnMessage": return_message,
            "Captured": capture,
            "Tid": tid,
            "ProofOfSale": f"POS{random.randint(100000, 999999)}",
            "AuthorizationCode": f"AUTH{random.randint(100000, 999999)}" if approved else None,
            "MerchantOrderId": merchant_order_id or f"ORDER{random.randint(1000, 9999)}",
            "Customer": {
                "Name": customer_name
            },
            "CreditCard": {
                "CardNumber": f"XXXX.XXXX.XXXX.{card_number[-4:]}",
                "Holder": card_holder,
                "ExpirationDate": card_expiration.replace("/", ""),
                "Brand": card_brand
            }
        }

        self.transactions[payment_id] = transaction
        return transaction

    def cielo_create_pix_payment(
        self,
        amount: float,
        merchant_order_id: str = None,
        customer_name: str = "Cliente Teste"
    ) -> Dict[str, Any]:
        """Mock de pagamento PIX na Cielo"""

        payment_id = str(uuid.uuid4())
        tid = f"TID{random.randint(100000, 999999)}"

        # Gera QR Code simulado
        qr_code = f"00020126580014BR.GOV.BCB.PIX{random.randint(10000000, 99999999)}"
        qr_code_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        transaction = {
            "PaymentId": payment_id,
            "Type": "Pix",
            "Amount": int(amount * 100),
            "ReceivedDate": datetime.utcnow().isoformat(),
            "Status": "12",  # Pendente
            "Tid": tid,
            "ProofOfSale": f"POS{random.randint(100000, 999999)}",
            "MerchantOrderId": merchant_order_id or f"ORDER{random.randint(1000, 9999)}",
            "Customer": {
                "Name": customer_name
            },
            "QrCodeString": qr_code,
            "QrCodeBase64Image": qr_code_base64,
            "DeepLinkUrl": f"https://pix.example.com/pay/{payment_id}"
        }

        self.pix_payments[payment_id] = transaction
        self.transactions[payment_id] = transaction
        return transaction

    def cielo_capture_payment(
        self,
        payment_id: str,
        amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """Mock de captura na Cielo"""

        if payment_id not in self.transactions:
            raise ValueError(f"Payment {payment_id} not found")

        transaction = self.transactions[payment_id]

        if transaction["Status"] != "1":  # Deve estar autorizada
            raise ValueError("Payment not authorized")

        capture_amount = amount or transaction["Amount"]

        transaction.update({
            "Status": "2",  # Capturada
            "Captured": True,
            "CapturedAmount": capture_amount,
            "CapturedDate": datetime.utcnow().isoformat(),
            "ReturnCode": "6",
            "ReturnMessage": "Operacao realizada com sucesso"
        })

        return transaction

    def cielo_cancel_payment(
        self,
        payment_id: str,
        amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """Mock de cancelamento na Cielo"""

        if payment_id not in self.transactions:
            raise ValueError(f"Payment {payment_id} not found")

        transaction = self.transactions[payment_id]
        cancel_amount = amount or transaction["Amount"]

        transaction.update({
            "Status": "10",  # Cancelada
            "VoidedAmount": cancel_amount,
            "VoidedDate": datetime.utcnow().isoformat(),
            "ReturnCode": "9",
            "ReturnMessage": "Transacao cancelada com sucesso"
        })

        return transaction

    def cielo_query_payment(self, payment_id: str) -> Dict[str, Any]:
        """Mock de consulta na Cielo"""
        if payment_id not in self.transactions:
            raise ValueError(f"Payment {payment_id} not found")
        return self.transactions[payment_id]

    # ============================================
    # GETNET MOCK
    # ============================================

    def getnet_create_card_payment(
        self,
        amount: float,
        installments: int = 1,
        order_id: str = None,
        customer_name: str = "Cliente Teste",
        customer_document: str = "00000000000",
        card_number: str = "5555555555555555",
        card_holder: str = "TITULAR TESTE",
        card_expiration: str = "12/28",
        card_cvv: str = "123",
        payment_type: str = "credit"
    ) -> Dict[str, Any]:
        """Mock de pagamento com cartão na GetNet"""

        payment_id = str(uuid.uuid4())
        order_id = order_id or f"ORD{random.randint(100000, 999999)}"

        # Simula aprovação (90% de chance)
        approved = random.random() < 0.9

        transaction = {
            "payment_id": payment_id,
            "order_id": order_id,
            "status": "APPROVED" if approved else "DENIED",
            "status_detail": "APPROVED" if approved else "DENIED_BY_BANK",
            "amount": int(amount * 100),  # Centavos
            "installments": installments,
            "currency": "BRL",
            "credit": {
                "delayed": False,
                "authenticated": False,
                "authorization_code": f"AUTH{random.randint(100000, 999999)}" if approved else None,
                "authorized_at": datetime.utcnow().isoformat() if approved else None,
                "card": {
                    "number_token": f"TOKEN{random.randint(100000, 999999)}",
                    "cardholder_name": card_holder,
                    "expiration_month": card_expiration.split("/")[0],
                    "expiration_year": card_expiration.split("/")[1][-2:],
                    "brand": "MASTERCARD"
                }
            },
            "seller_id": "SELLER_ID_SANDBOX",
            "received_at": datetime.utcnow().isoformat()
        }

        self.transactions[payment_id] = transaction
        return transaction

    def getnet_create_pix_payment(
        self,
        amount: float,
        order_id: str = None,
        customer_name: str = "Cliente Teste",
        customer_document: str = "00000000000"
    ) -> Dict[str, Any]:
        """Mock de pagamento PIX na GetNet"""

        payment_id = str(uuid.uuid4())
        order_id = order_id or f"ORD{random.randint(100000, 999999)}"

        # Gera QR Code simulado
        qr_code = f"00020126580014BR.GOV.BCB.PIX{random.randint(10000000, 99999999)}"
        qr_code_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        transaction = {
            "payment_id": payment_id,
            "order_id": order_id,
            "status": "PENDING",
            "status_detail": "PENDING_CONFIRMATION",
            "amount": int(amount * 100),
            "currency": "BRL",
            "qr_code": qr_code,
            "qr_code_image": qr_code_base64,
            "additional_data": {
                "pix_url": f"https://pix.getnet.com.br/{payment_id}"
            },
            "seller_id": "SELLER_ID_SANDBOX",
            "received_at": datetime.utcnow().isoformat(),
            "expiration_date": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }

        self.pix_payments[payment_id] = transaction
        self.transactions[payment_id] = transaction
        return transaction

    def getnet_capture_payment(self, payment_id: str) -> Dict[str, Any]:
        """Mock de captura na GetNet"""
        if payment_id not in self.transactions:
            raise ValueError(f"Payment {payment_id} not found")

        transaction = self.transactions[payment_id]
        transaction.update({
            "status": "APPROVED",
            "status_detail": "CAPTURED",
            "captured_at": datetime.utcnow().isoformat()
        })

        return transaction

    def getnet_cancel_payment(self, payment_id: str) -> Dict[str, Any]:
        """Mock de cancelamento na GetNet"""
        if payment_id not in self.transactions:
            raise ValueError(f"Payment {payment_id} not found")

        transaction = self.transactions[payment_id]
        transaction.update({
            "status": "CANCELED",
            "status_detail": "CANCEL_BY_MERCHANT",
            "canceled_at": datetime.utcnow().isoformat()
        })

        return transaction

    def getnet_query_payment(self, payment_id: str) -> Dict[str, Any]:
        """Mock de consulta na GetNet"""
        if payment_id not in self.transactions:
            raise ValueError(f"Payment {payment_id} not found")
        return self.transactions[payment_id]

    # ============================================
    # MERCADO PAGO MOCK
    # ============================================

    def mercadopago_create_pix_payment(
        self,
        valor: Decimal,
        descricao: str,
        email_pagador: Optional[str] = None,
        external_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock de pagamento PIX no Mercado Pago"""

        payment_id = random.randint(1000000000, 9999999999)

        # Gera QR Code simulado
        qr_code = f"00020126580014BR.GOV.BCB.PIX{random.randint(10000000, 99999999)}"
        qr_code_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

        transaction = {
            "id": payment_id,
            "status": "pending",
            "status_detail": "pending_waiting_payment",
            "transaction_amount": float(valor),
            "description": descricao,
            "external_reference": external_reference,
            "payment_method_id": "pix",
            "payer": {
                "email": email_pagador or "test@test.com"
            },
            "point_of_interaction": {
                "type": "PIX",
                "transaction_data": {
                    "qr_code": qr_code,
                    "qr_code_base64": qr_code_base64,
                    "ticket_url": f"https://www.mercadopago.com.br/payments/{payment_id}/ticket"
                }
            },
            "date_created": datetime.utcnow().isoformat(),
            "date_of_expiration": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "valor": valor,
            "qr_code": qr_code
        }

        self.pix_payments[str(payment_id)] = transaction
        self.transactions[str(payment_id)] = transaction
        return transaction

    def mercadopago_create_card_payment(
        self,
        valor: Decimal,
        parcelas: int,
        descricao: str,
        email_pagador: Optional[str] = None,
        card_token: Optional[str] = None,
        external_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock de pagamento com cartão no Mercado Pago"""

        payment_id = random.randint(1000000000, 9999999999)

        # Simula aprovação (90% de chance)
        approved = random.random() < 0.9

        transaction = {
            "id": payment_id,
            "status": "approved" if approved else "rejected",
            "status_detail": "accredited" if approved else "cc_rejected_bad_filled_card_number",
            "transaction_amount": float(valor),
            "installments": parcelas,
            "description": descricao,
            "external_reference": external_reference,
            "payment_method_id": "visa",
            "payment_type_id": "credit_card",
            "payer": {
                "email": email_pagador or "test@test.com"
            },
            "date_created": datetime.utcnow().isoformat(),
            "date_approved": datetime.utcnow().isoformat() if approved else None,
            "valor": valor
        }

        self.transactions[str(payment_id)] = transaction
        return transaction

    def mercadopago_query_payment(self, payment_id: int) -> Dict[str, Any]:
        """Mock de consulta no Mercado Pago"""
        payment_id_str = str(payment_id)
        if payment_id_str not in self.transactions:
            raise ValueError(f"Payment {payment_id} not found")
        return self.transactions[payment_id_str]

    def mercadopago_cancel_payment(self, payment_id: int) -> Dict[str, Any]:
        """Mock de cancelamento no Mercado Pago"""
        payment_id_str = str(payment_id)
        if payment_id_str not in self.transactions:
            raise ValueError(f"Payment {payment_id} not found")

        transaction = self.transactions[payment_id_str]
        transaction.update({
            "status": "cancelled",
            "status_detail": "by_merchant",
            "date_last_updated": datetime.utcnow().isoformat()
        })

        return transaction

    # ============================================
    # WEBHOOKS MOCK
    # ============================================

    def simulate_pix_payment(self, payment_id: str) -> Dict[str, Any]:
        """Simula pagamento PIX aprovado (para webhooks)"""
        if payment_id not in self.pix_payments:
            raise ValueError(f"PIX payment {payment_id} not found")

        transaction = self.pix_payments[payment_id]

        # Atualiza status para aprovado
        if "PaymentId" in transaction:  # Cielo
            transaction["Status"] = "2"  # Capturada
        elif "payment_id" in transaction:  # GetNet
            transaction["status"] = "APPROVED"
            transaction["status_detail"] = "CONFIRMED"
        else:  # Mercado Pago
            transaction["status"] = "approved"
            transaction["status_detail"] = "accredited"

        transaction["paid_at"] = datetime.utcnow().isoformat()

        return transaction
