"""
Router que simula API da GetNet (Santander)

Documentação GetNet: https://developers.getnet.com.br/api
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional, Dict, Any
import uuid
import random
import base64
from datetime import datetime, timedelta

from app.models import Transaction, PaymentStatus, PaymentMethod
from app.storage import storage
from app.config import settings

router = APIRouter()


def generate_getnet_payment_id() -> str:
    """Gerar ID de pagamento GetNet"""
    return str(uuid.uuid4())


def generate_pix_qrcode() -> tuple[str, str]:
    """Gerar QR Code PIX simulado"""
    pix_id = f"PIX{random.randint(10000000, 99999999)}"
    qrcode_text = f"00020126580014br.gov.bcb.pix{pix_id}"
    qrcode_base64 = base64.b64encode(qrcode_text.encode()).decode()
    return qrcode_text, qrcode_base64


@router.post("/auth/oauth/v2/token")
async def get_oauth_token(
    client_id: str = None,
    client_secret: str = None,
    scope: str = "oob"
):
    """
    Obter token OAuth2

    Simula: POST https://api-homologacao.getnet.com.br/auth/oauth/v2/token
    """
    return {
        "access_token": f"MOCK-TOKEN-{uuid.uuid4().hex[:32]}",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": scope
    }


@router.post("/v1/payments/credit")
async def create_credit_payment(
    payment_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    Criar pagamento com cartão de crédito

    Simula: POST https://api-homologacao.getnet.com.br/v1/payments/credit
    """
    # Gerar IDs
    payment_id = generate_getnet_payment_id()
    order_id = payment_data.get("order", {}).get("order_id", str(uuid.uuid4()))

    # Decidir aprovação
    approved = random.random() < settings.APPROVAL_RATE

    status = PaymentStatus.CAPTURED if approved else PaymentStatus.DENIED
    status_code = "APPROVED" if approved else "DENIED"

    # Salvar transação
    transaction = Transaction(
        id=payment_id,
        gateway="getnet",
        payment_method=PaymentMethod.CREDIT_CARD,
        status=status,
        amount=payment_data.get("amount", 0) / 100,
        installments=payment_data.get("credit", {}).get("transaction_type") == "INSTALL_NO_INTEREST" and \
                     payment_data.get("credit", {}).get("number_installments", 1) or 1,
        order_id=order_id,
        card_data={
            "masked_number": f"****-****-****-{random.randint(1000, 9999)}",
            "brand": payment_data.get("credit", {}).get("card", {}).get("brand", "Mastercard")
        }
    )
    storage.save_transaction(transaction)
    storage.update_stats("approved" if approved else "denied")

    # Resposta GetNet
    response = {
        "payment_id": payment_id,
        "seller_id": payment_data.get("seller_id", "MOCK-SELLER"),
        "amount": payment_data.get("amount", 0),
        "currency": "BRL",
        "order_id": order_id,
        "status": status_code,
        "received_at": datetime.utcnow().isoformat(),
        "credit": {
            "delayed": False,
            "authenticated": False,
            "authorization_code": f"AUTH{random.randint(100000, 999999)}" if approved else None,
            "authorized_at": datetime.utcnow().isoformat() if approved else None,
            "reason_code": "00" if approved else "05",
            "reason_message": "Transaction successfully authorized" if approved else "Not authorized",
            "acquirer": "GETNET",
            "soft_descriptor": "SISCOM ERP",
            "brand": transaction.card_data["brand"],
            "terminal_nsu": f"NSU{random.randint(1000000, 9999999)}",
            "acquirer_transaction_id": f"TXN{random.randint(100000000, 999999999)}"
        }
    }

    return response


@router.post("/v1/payments/debit")
async def create_debit_payment(
    payment_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    Criar pagamento com cartão de débito

    Simula: POST https://api-homologacao.getnet.com.br/v1/payments/debit
    """
    payment_id = generate_getnet_payment_id()
    order_id = payment_data.get("order", {}).get("order_id", str(uuid.uuid4()))

    approved = random.random() < settings.APPROVAL_RATE
    status = PaymentStatus.CAPTURED if approved else PaymentStatus.DENIED

    transaction = Transaction(
        id=payment_id,
        gateway="getnet",
        payment_method=PaymentMethod.DEBIT_CARD,
        status=status,
        amount=payment_data.get("amount", 0) / 100,
        order_id=order_id
    )
    storage.save_transaction(transaction)
    storage.update_stats("approved" if approved else "denied")

    return {
        "payment_id": payment_id,
        "seller_id": payment_data.get("seller_id", "MOCK-SELLER"),
        "amount": payment_data.get("amount", 0),
        "currency": "BRL",
        "order_id": order_id,
        "status": "APPROVED" if approved else "DENIED",
        "received_at": datetime.utcnow().isoformat(),
        "debit": {
            "authorization_code": f"AUTH{random.randint(100000, 999999)}" if approved else None,
            "authenticated": True,
            "reason_code": "00" if approved else "05",
            "reason_message": "Transaction successfully authorized" if approved else "Not authorized"
        }
    }


@router.post("/v1/payments/pix")
async def create_pix_payment(
    payment_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    Criar pagamento PIX

    Simula: POST https://api-homologacao.getnet.com.br/v1/payments/pix
    """
    payment_id = generate_getnet_payment_id()
    order_id = payment_data.get("order", {}).get("order_id", str(uuid.uuid4()))

    # Gerar QR Code PIX
    qrcode_text, qrcode_base64 = generate_pix_qrcode()

    # PIX sempre pending inicialmente
    transaction = Transaction(
        id=payment_id,
        gateway="getnet",
        payment_method=PaymentMethod.PIX,
        status=PaymentStatus.PENDING,
        amount=payment_data.get("amount", 0) / 100,
        order_id=order_id,
        pix_data={
            "qrcode": qrcode_text,
            "qrcode_base64": qrcode_base64,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
    )
    storage.save_transaction(transaction)

    return {
        "payment_id": payment_id,
        "seller_id": payment_data.get("seller_id", "MOCK-SELLER"),
        "amount": payment_data.get("amount", 0),
        "currency": "BRL",
        "order_id": order_id,
        "status": "PENDING",
        "received_at": datetime.utcnow().isoformat(),
        "pix": {
            "qrcode": qrcode_text,
            "qrcode_image": f"data:image/png;base64,{qrcode_base64}",
            "expiration_date": transaction.pix_data["expires_at"],
            "additional_data": {
                "txid": f"TXID{uuid.uuid4().hex[:32]}"
            }
        }
    }


@router.get("/v1/payments/{payment_id}")
async def query_payment(
    payment_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Consultar pagamento

    Simula: GET https://api-homologacao.getnet.com.br/v1/payments/{payment_id}
    """
    transaction = storage.get_transaction(payment_id)
    if not transaction:
        raise HTTPException(404, {"error": "Payment not found"})

    # Mapear status
    status_map = {
        PaymentStatus.PENDING: "PENDING",
        PaymentStatus.AUTHORIZED: "AUTHORIZED",
        PaymentStatus.CAPTURED: "APPROVED",
        PaymentStatus.DENIED: "DENIED",
        PaymentStatus.CANCELLED: "CANCELLED",
        PaymentStatus.REFUNDED: "REFUNDED"
    }

    response = {
        "payment_id": payment_id,
        "seller_id": "MOCK-SELLER",
        "amount": int(transaction.amount * 100),
        "currency": "BRL",
        "order_id": transaction.order_id,
        "status": status_map.get(transaction.status, "PENDING"),
        "received_at": transaction.created_at.isoformat()
    }

    if transaction.payment_method == PaymentMethod.PIX:
        response["pix"] = transaction.pix_data

    return response


@router.post("/v1/payments/credit/{payment_id}/cancel")
async def cancel_payment(
    payment_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Cancelar pagamento

    Simula: POST https://api-homologacao.getnet.com.br/v1/payments/credit/{payment_id}/cancel
    """
    transaction = storage.get_transaction(payment_id)
    if not transaction:
        raise HTTPException(404, {"error": "Payment not found"})

    storage.update_transaction(payment_id, {
        "status": PaymentStatus.CANCELLED,
        "cancelled_at": datetime.utcnow()
    })
    storage.update_stats("cancelled")

    return {
        "payment_id": payment_id,
        "cancel_status": "CONFIRMED",
        "status": "CANCELLED",
        "cancelled_at": datetime.utcnow().isoformat()
    }


@router.post("/v1/tokens/card")
async def tokenize_card(
    card_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    Tokenizar cartão

    Simula: POST https://api-homologacao.getnet.com.br/v1/tokens/card
    """
    return {
        "number_token": f"TOKEN-GETNET-{uuid.uuid4().hex[:16].upper()}"
    }
