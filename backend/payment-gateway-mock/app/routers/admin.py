"""
Router administrativo para estatísticas e gerenciamento
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.storage import storage
from app.models import PaymentStatus

router = APIRouter()


@router.get("/stats")
async def get_stats():
    """Estatísticas gerais do mock"""
    return {
        "service": "payment-gateway-mock",
        "stats": storage.get_stats(),
        "transactions_count": len(storage.transactions)
    }


@router.get("/transactions")
async def list_transactions(
    gateway: Optional[str] = Query(None, description="Filtrar por gateway"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    limit: int = Query(100, ge=1, le=1000)
):
    """Listar transações com filtros"""
    transactions = storage.list_transactions(
        gateway=gateway,
        status=status,
        limit=limit
    )

    return {
        "total": len(transactions),
        "transactions": [
            {
                "id": t.id,
                "gateway": t.gateway,
                "method": t.payment_method.value,
                "status": t.status.value,
                "amount": t.amount,
                "order_id": t.order_id,
                "created_at": t.created_at.isoformat()
            }
            for t in transactions
        ]
    }


@router.get("/transactions/{transaction_id}")
async def get_transaction_details(transaction_id: str):
    """Detalhes de uma transação"""
    transaction = storage.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(404, "Transaction not found")

    return transaction.dict()


@router.post("/transactions/{transaction_id}/approve")
async def approve_pix_payment(transaction_id: str):
    """
    Aprovar pagamento PIX manualmente (simula pagamento do cliente)

    Útil para testar fluxo completo de PIX
    """
    transaction = storage.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(404, "Transaction not found")

    if transaction.payment_method.value != "pix":
        raise HTTPException(400, "Only PIX payments can be approved manually")

    if transaction.status != PaymentStatus.PENDING:
        raise HTTPException(400, f"Payment is {transaction.status.value}, cannot approve")

    # Atualizar para approved
    from datetime import datetime
    storage.update_transaction(transaction_id, {
        "status": PaymentStatus.CAPTURED,
        "captured_at": datetime.utcnow()
    })
    storage.update_stats("approved")

    return {
        "message": "PIX payment approved",
        "transaction_id": transaction_id,
        "status": "captured"
    }


@router.delete("/transactions")
async def clear_all_transactions():
    """Limpar todas as transações (útil para testes)"""
    storage.clear_all()
    return {"message": "All transactions cleared"}


@router.post("/config/approval-rate")
async def set_approval_rate(rate: float = Query(..., ge=0.0, le=1.0)):
    """
    Configurar taxa de aprovação de pagamentos

    rate: 0.0 a 1.0 (ex: 0.9 = 90% de aprovação)
    """
    from app.config import settings
    settings.APPROVAL_RATE = rate

    return {
        "message": f"Approval rate set to {rate * 100}%",
        "approval_rate": rate
    }


@router.get("/webhooks")
async def list_webhooks():
    """Listar webhooks registrados"""
    return {
        "cielo": [w.dict() for w in storage.get_webhooks("cielo")],
        "getnet": [w.dict() for w in storage.get_webhooks("getnet")],
        "mercadopago": [w.dict() for w in storage.get_webhooks("mercadopago")]
    }


@router.get("/health")
async def health_check():
    """Health check administrativo"""
    return {
        "status": "healthy",
        "transactions_count": len(storage.transactions),
        "stats": storage.get_stats()
    }
