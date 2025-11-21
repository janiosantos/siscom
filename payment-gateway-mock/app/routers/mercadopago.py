"""
Router que simula API do Mercado Pago

Documentação MP: https://www.mercadopago.com.br/developers/pt/reference
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


def generate_mp_payment_id() -> int:
    """Gerar ID de pagamento Mercado Pago"""
    return random.randint(10000000000, 99999999999)


def generate_pix_qrcode() -> tuple[str, str]:
    """Gerar QR Code PIX simulado"""
    pix_id = f"MP{random.randint(10000000, 99999999)}"
    qrcode_text = f"00020126580014br.gov.bcb.pix{pix_id}"
    qrcode_base64 = base64.b64encode(qrcode_text.encode()).decode()
    return qrcode_text, qrcode_base64


@router.post("/v1/payments")
async def create_payment(
    payment_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    Criar pagamento

    Simula: POST https://api.mercadopago.com/v1/payments
    """
    # Gerar ID
    payment_id = generate_mp_payment_id()
    payment_method_id = payment_data.get("payment_method_id", "pix")

    # Determinar método de pagamento
    if payment_method_id == "pix":
        method = PaymentMethod.PIX
        approved = False  # PIX sempre pending inicialmente
        status = PaymentStatus.PENDING
        status_detail = "pending_waiting_payment"

        # Gerar QR Code
        qrcode_text, qrcode_base64 = generate_pix_qrcode()

        pix_data = {
            "qr_code": qrcode_text,
            "qr_code_base64": qrcode_base64,
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
    else:
        # Cartão de crédito
        method = PaymentMethod.CREDIT_CARD
        approved = random.random() < settings.APPROVAL_RATE
        status = PaymentStatus.CAPTURED if approved else PaymentStatus.DENIED
        status_detail = "accredited" if approved else "cc_rejected_bad_filled_card_number"
        pix_data = None

    # Salvar transação
    transaction = Transaction(
        id=str(payment_id),
        gateway="mercadopago",
        payment_method=method,
        status=status,
        amount=payment_data.get("transaction_amount", 0),
        installments=payment_data.get("installments", 1),
        order_id=payment_data.get("external_reference"),
        pix_data=pix_data
    )
    storage.save_transaction(transaction)
    if approved:
        storage.update_stats("approved")
    elif method == PaymentMethod.CREDIT_CARD:
        storage.update_stats("denied")

    # Resposta base
    response = {
        "id": payment_id,
        "date_created": datetime.utcnow().isoformat(),
        "date_approved": datetime.utcnow().isoformat() if approved else None,
        "date_last_updated": datetime.utcnow().isoformat(),
        "money_release_date": (datetime.utcnow() + timedelta(days=14)).isoformat() if approved else None,
        "operation_type": "regular_payment",
        "issuer_id": str(random.randint(100, 999)),
        "payment_method_id": payment_method_id,
        "payment_type_id": "debit_card" if payment_method_id == "pix" else "credit_card",
        "status": "approved" if approved else ("pending" if method == PaymentMethod.PIX else "rejected"),
        "status_detail": status_detail,
        "currency_id": "BRL",
        "description": payment_data.get("description", "Payment"),
        "live_mode": False,
        "sponsor_id": None,
        "authorization_code": f"AUTH{random.randint(100000, 999999)}" if approved else None,
        "money_release_schema": None,
        "taxes_amount": 0,
        "counter_currency": None,
        "brand_id": None,
        "shipping_amount": 0,
        "build_version": "2.0.0",
        "pos_id": None,
        "store_id": None,
        "integrator_id": None,
        "platform_id": None,
        "corporation_id": None,
        "collector_id": random.randint(100000000, 999999999),
        "payer": payment_data.get("payer", {
            "id": str(random.randint(100000000, 999999999)),
            "email": "test@test.com",
            "type": "guest"
        }),
        "metadata": {},
        "additional_info": {},
        "external_reference": payment_data.get("external_reference"),
        "transaction_amount": payment_data.get("transaction_amount", 0),
        "transaction_amount_refunded": 0,
        "coupon_amount": 0,
        "differential_pricing_id": None,
        "deduction_schema": None,
        "installments": payment_data.get("installments", 1),
        "transaction_details": {
            "payment_method_reference_id": None,
            "net_received_amount": payment_data.get("transaction_amount", 0) * 0.97 if approved else 0,
            "total_paid_amount": payment_data.get("transaction_amount", 0),
            "overpaid_amount": 0,
            "external_resource_url": None,
            "installment_amount": payment_data.get("transaction_amount", 0) / payment_data.get("installments", 1),
            "financial_institution": None,
            "payable_deferral_period": None,
            "acquirer_reference": None
        },
        "fee_details": [],
        "captured": True if approved else False,
        "binary_mode": False,
        "call_for_authorize_id": None,
        "statement_descriptor": "SISCOM",
        "card": {},
        "notification_url": payment_data.get("notification_url"),
        "refunds": [],
        "processing_mode": "aggregator",
        "merchant_account_id": None,
        "merchant_number": None,
        "acquirer_reconciliation": []
    }

    # Adicionar dados específicos de PIX
    if method == PaymentMethod.PIX:
        response["point_of_interaction"] = {
            "type": "PIX",
            "sub_type": None,
            "application_data": {
                "name": "SISCOM",
                "version": "1.0"
            },
            "transaction_data": {
                "qr_code": pix_data["qr_code"],
                "qr_code_base64": pix_data["qr_code_base64"],
                "ticket_url": f"https://www.mercadopago.com.br/checkout/v1/redirect?payment_id={payment_id}"
            }
        }

    return response


@router.get("/v1/payments/{payment_id}")
async def query_payment(
    payment_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Consultar pagamento

    Simula: GET https://api.mercadopago.com/v1/payments/{id}
    """
    transaction = storage.get_transaction(payment_id)
    if not transaction:
        raise HTTPException(404, {"message": "Payment not found"})

    # Mapear status
    status_map = {
        PaymentStatus.PENDING: "pending",
        PaymentStatus.AUTHORIZED: "authorized",
        PaymentStatus.CAPTURED: "approved",
        PaymentStatus.DENIED: "rejected",
        PaymentStatus.CANCELLED: "cancelled",
        PaymentStatus.REFUNDED: "refunded"
    }

    approved = transaction.status == PaymentStatus.CAPTURED

    response = {
        "id": int(payment_id),
        "status": status_map.get(transaction.status, "pending"),
        "status_detail": "accredited" if approved else "pending_waiting_payment",
        "payment_method_id": "pix" if transaction.payment_method == PaymentMethod.PIX else "visa",
        "payment_type_id": "debit_card" if transaction.payment_method == PaymentMethod.PIX else "credit_card",
        "transaction_amount": transaction.amount,
        "installments": transaction.installments,
        "external_reference": transaction.order_id,
        "date_created": transaction.created_at.isoformat(),
        "date_approved": transaction.captured_at.isoformat() if transaction.captured_at else None,
        "date_last_updated": transaction.updated_at.isoformat(),
        "currency_id": "BRL",
        "live_mode": False
    }

    # Adicionar dados de PIX se aplicável
    if transaction.payment_method == PaymentMethod.PIX and transaction.pix_data:
        response["point_of_interaction"] = {
            "type": "PIX",
            "transaction_data": {
                "qr_code": transaction.pix_data.get("qr_code"),
                "qr_code_base64": transaction.pix_data.get("qr_code_base64")
            }
        }

    return response


@router.put("/v1/payments/{payment_id}")
async def update_payment(
    payment_id: str,
    payment_data: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    Atualizar pagamento (cancelar/capturar)

    Simula: PUT https://api.mercadopago.com/v1/payments/{id}
    """
    transaction = storage.get_transaction(payment_id)
    if not transaction:
        raise HTTPException(404, {"message": "Payment not found"})

    # Capturar
    if payment_data.get("capture") is True:
        storage.update_transaction(payment_id, {
            "status": PaymentStatus.CAPTURED,
            "captured_at": datetime.utcnow()
        })
        storage.update_stats("approved")
        new_status = "approved"

    # Cancelar
    elif payment_data.get("status") == "cancelled":
        storage.update_transaction(payment_id, {
            "status": PaymentStatus.CANCELLED,
            "cancelled_at": datetime.utcnow()
        })
        storage.update_stats("cancelled")
        new_status = "cancelled"

    else:
        raise HTTPException(400, {"message": "Invalid operation"})

    return {
        "id": int(payment_id),
        "status": new_status,
        "status_detail": "accredited" if new_status == "approved" else "by_collector",
        "date_approved": datetime.utcnow().isoformat() if new_status == "approved" else None,
        "date_last_updated": datetime.utcnow().isoformat()
    }


@router.post("/v1/payments/{payment_id}/refunds")
async def refund_payment(
    payment_id: str,
    refund_data: Optional[Dict[str, Any]] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Estornar pagamento

    Simula: POST https://api.mercadopago.com/v1/payments/{id}/refunds
    """
    transaction = storage.get_transaction(payment_id)
    if not transaction:
        raise HTTPException(404, {"message": "Payment not found"})

    if transaction.status != PaymentStatus.CAPTURED:
        raise HTTPException(400, {"message": "Payment is not captured"})

    storage.update_transaction(payment_id, {
        "status": PaymentStatus.REFUNDED,
        "cancelled_at": datetime.utcnow()
    })
    storage.update_stats("refunded")

    return {
        "id": random.randint(10000000, 99999999),
        "payment_id": int(payment_id),
        "amount": transaction.amount,
        "metadata": {},
        "source": {
            "id": "123456789",
            "name": "Test User",
            "type": "collector"
        },
        "date_created": datetime.utcnow().isoformat(),
        "unique_sequence_number": None,
        "refund_mode": "standard",
        "adjustment_amount": 0,
        "status": "approved",
        "reason": "refund"
    }
