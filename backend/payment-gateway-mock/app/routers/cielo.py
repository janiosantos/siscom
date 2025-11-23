"""
Router que simula API da Cielo

Documentação Cielo: https://developercielo.github.io/manual/cielo-ecommerce
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, Any
import uuid
import random
from datetime import datetime

from app.models import Transaction, PaymentStatus, PaymentMethod
from app.storage import storage
from app.config import settings

router = APIRouter()


def generate_cielo_payment_id() -> str:
    """Gerar ID de pagamento Cielo"""
    return str(uuid.uuid4())


def should_approve_payment() -> bool:
    """Decidir se aprova pagamento (90% de sucesso)"""
    return random.random() < settings.APPROVAL_RATE


@router.post("/1/sales")
async def create_sale(
    sale_data: Dict[str, Any],
    merchant_id: Optional[str] = Header(None, alias="MerchantId"),
    merchant_key: Optional[str] = Header(None, alias="MerchantKey")
):
    """
    Criar venda na Cielo

    Simula: POST https://api.cieloecommerce.cielo.com.br/1/sales
    """
    # Extrair dados
    merchant_order_id = sale_data.get("MerchantOrderId", str(uuid.uuid4()))
    payment = sale_data.get("Payment", {})

    # Determinar método de pagamento
    payment_type = payment.get("Type")
    if payment_type == "CreditCard":
        method = PaymentMethod.CREDIT_CARD
    elif payment_type == "DebitCard":
        method = PaymentMethod.DEBIT_CARD
    else:
        raise HTTPException(400, "Tipo de pagamento não suportado")

    # Gerar IDs
    payment_id = generate_cielo_payment_id()
    tid = f"TID{random.randint(100000, 999999)}"

    # Decidir aprovação
    approved = should_approve_payment()
    capture = payment.get("Capture", True)

    if approved:
        status = PaymentStatus.CAPTURED if capture else PaymentStatus.AUTHORIZED
        status_code = "2" if capture else "1"
        return_code = "4"  # Approved
        return_message = "Operação realizada com sucesso"
    else:
        status = PaymentStatus.DENIED
        status_code = "3"
        return_code = "57"  # Denied
        return_message = "Cartão bloqueado"

    # Salvar transação
    transaction = Transaction(
        id=payment_id,
        gateway="cielo",
        payment_method=method,
        status=status,
        amount=payment.get("Amount", 0) / 100,  # Centavos para reais
        installments=payment.get("Installments", 1),
        order_id=merchant_order_id,
        card_data={
            "masked_number": f"****.****.****{str(random.randint(1000, 9999))}",
            "brand": payment.get("CreditCard", {}).get("Brand", "Visa")
        }
    )
    storage.save_transaction(transaction)
    storage.update_stats("approved" if approved else "denied")

    # Resposta Cielo
    response = {
        "MerchantOrderId": merchant_order_id,
        "Payment": {
            "ServiceTaxAmount": 0,
            "Installments": payment.get("Installments", 1),
            "Interest": payment.get("Interest", "ByMerchant"),
            "Capture": capture,
            "Authenticate": False,
            "Recurrent": False,
            "CreditCard": {
                "CardNumber": transaction.card_data["masked_number"],
                "Holder": payment.get("CreditCard", {}).get("Holder", "HOLDER NAME"),
                "ExpirationDate": payment.get("CreditCard", {}).get("ExpirationDate", "12/2028"),
                "SaveCard": False,
                "Brand": transaction.card_data["brand"]
            },
            "Tid": tid,
            "ProofOfSale": f"POS{random.randint(100000, 999999)}",
            "AuthorizationCode": f"AUTH{random.randint(100000, 999999)}" if approved else None,
            "SoftDescriptor": payment.get("SoftDescriptor", "ERP SISCOM"),
            "PaymentId": payment_id,
            "Type": payment_type,
            "Amount": payment.get("Amount", 0),
            "ReceivedDate": datetime.utcnow().isoformat(),
            "Currency": "BRL",
            "Country": "BRA",
            "Provider": "Simulado",
            "ReasonCode": int(return_code),
            "ReasonMessage": return_message,
            "Status": int(status_code),
            "ProviderReturnCode": return_code,
            "ProviderReturnMessage": return_message,
            "Links": [
                {
                    "Method": "GET",
                    "Rel": "self",
                    "Href": f"http://localhost:8001/cielo/1/sales/{payment_id}"
                },
                {
                    "Method": "PUT",
                    "Rel": "capture",
                    "Href": f"http://localhost:8001/cielo/1/sales/{payment_id}/capture"
                },
                {
                    "Method": "PUT",
                    "Rel": "void",
                    "Href": f"http://localhost:8001/cielo/1/sales/{payment_id}/void"
                }
            ]
        }
    }

    return response


@router.get("/1/sales/{payment_id}")
async def query_sale(
    payment_id: str,
    merchant_id: Optional[str] = Header(None, alias="MerchantId"),
    merchant_key: Optional[str] = Header(None, alias="MerchantKey")
):
    """
    Consultar venda na Cielo

    Simula: GET https://apiquery.cieloecommerce.cielo.com.br/1/sales/{PaymentId}
    """
    transaction = storage.get_transaction(payment_id)
    if not transaction:
        raise HTTPException(404, "Payment not found")

    # Mapear status
    status_map = {
        PaymentStatus.PENDING: "0",
        PaymentStatus.AUTHORIZED: "1",
        PaymentStatus.CAPTURED: "2",
        PaymentStatus.DENIED: "3",
        PaymentStatus.CANCELLED: "10",
        PaymentStatus.REFUNDED: "11"
    }

    return {
        "Payment": {
            "ServiceTaxAmount": 0,
            "Installments": transaction.installments,
            "Interest": "ByMerchant",
            "Capture": transaction.status == PaymentStatus.CAPTURED,
            "Authenticate": False,
            "Recurrent": False,
            "Tid": f"TID{random.randint(100000, 999999)}",
            "ProofOfSale": f"POS{random.randint(100000, 999999)}",
            "AuthorizationCode": f"AUTH{random.randint(100000, 999999)}",
            "PaymentId": payment_id,
            "Type": "CreditCard" if transaction.payment_method == PaymentMethod.CREDIT_CARD else "DebitCard",
            "Amount": int(transaction.amount * 100),
            "ReceivedDate": transaction.created_at.isoformat(),
            "CapturedDate": transaction.captured_at.isoformat() if transaction.captured_at else None,
            "VoidedDate": transaction.cancelled_at.isoformat() if transaction.cancelled_at else None,
            "Currency": "BRL",
            "Country": "BRA",
            "Provider": "Simulado",
            "Status": int(status_map.get(transaction.status, "0")),
            "Links": []
        }
    }


@router.put("/1/sales/{payment_id}/capture")
async def capture_sale(
    payment_id: str,
    amount: Optional[int] = None,
    merchant_id: Optional[str] = Header(None, alias="MerchantId"),
    merchant_key: Optional[str] = Header(None, alias="MerchantKey")
):
    """
    Capturar venda pré-autorizada

    Simula: PUT https://api.cieloecommerce.cielo.com.br/1/sales/{PaymentId}/capture
    """
    transaction = storage.get_transaction(payment_id)
    if not transaction:
        raise HTTPException(404, "Payment not found")

    if transaction.status != PaymentStatus.AUTHORIZED:
        raise HTTPException(400, "Payment is not authorized")

    # Atualizar status
    storage.update_transaction(payment_id, {
        "status": PaymentStatus.CAPTURED,
        "captured_at": datetime.utcnow()
    })
    storage.update_stats("approved")

    return {
        "Status": 2,
        "ReasonCode": 0,
        "ReasonMessage": "Successful",
        "ProviderReturnCode": "6",
        "ProviderReturnMessage": "Operation Successful",
        "Links": [
            {
                "Method": "GET",
                "Rel": "self",
                "Href": f"http://localhost:8001/cielo/1/sales/{payment_id}"
            }
        ]
    }


@router.put("/1/sales/{payment_id}/void")
async def cancel_sale(
    payment_id: str,
    amount: Optional[int] = None,
    merchant_id: Optional[str] = Header(None, alias="MerchantId"),
    merchant_key: Optional[str] = Header(None, alias="MerchantKey")
):
    """
    Cancelar/estornar venda

    Simula: PUT https://api.cieloecommerce.cielo.com.br/1/sales/{PaymentId}/void
    """
    transaction = storage.get_transaction(payment_id)
    if not transaction:
        raise HTTPException(404, "Payment not found")

    if transaction.status not in [PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED]:
        raise HTTPException(400, "Payment cannot be cancelled")

    # Atualizar status
    new_status = PaymentStatus.CANCELLED if transaction.status == PaymentStatus.AUTHORIZED else PaymentStatus.REFUNDED
    storage.update_transaction(payment_id, {
        "status": new_status,
        "cancelled_at": datetime.utcnow()
    })
    storage.update_stats("cancelled" if new_status == PaymentStatus.CANCELLED else "refunded")

    return {
        "Status": 10 if new_status == PaymentStatus.CANCELLED else 11,
        "ReasonCode": 0,
        "ReasonMessage": "Successful",
        "ProviderReturnCode": "0",
        "ProviderReturnMessage": "Operation Successful",
        "Links": [
            {
                "Method": "GET",
                "Rel": "self",
                "Href": f"http://localhost:8001/cielo/1/sales/{payment_id}"
            }
        ]
    }


@router.post("/1/card")
async def tokenize_card(
    card_data: Dict[str, Any],
    merchant_id: Optional[str] = Header(None, alias="MerchantId"),
    merchant_key: Optional[str] = Header(None, alias="MerchantKey")
):
    """
    Tokenizar cartão (Card on File)

    Simula: POST https://api.cieloecommerce.cielo.com.br/1/card
    """
    card_token = f"TOKEN-CIELO-{uuid.uuid4().hex[:16].upper()}"

    return {
        "CardToken": card_token,
        "Links": [
            {
                "Method": "GET",
                "Rel": "self",
                "Href": f"http://localhost:8001/cielo/1/card/{card_token}"
            }
        ]
    }
