"""
Modelos de dados para o mock service
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class PaymentStatus(str, Enum):
    """Status de pagamento"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    DENIED = "denied"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Método de pagamento"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PIX = "pix"


class Transaction(BaseModel):
    """Transação de pagamento"""
    id: str
    gateway: str
    payment_method: PaymentMethod
    status: PaymentStatus
    amount: float
    installments: int = 1
    order_id: Optional[str] = None
    customer_data: Optional[Dict[str, Any]] = None
    card_data: Optional[Dict[str, Any]] = None
    pix_data: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    captured_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class CieloSaleRequest(BaseModel):
    """Requisição de venda Cielo"""
    MerchantOrderId: str
    Payment: Dict[str, Any]


class GetNetPaymentRequest(BaseModel):
    """Requisição de pagamento GetNet"""
    seller_id: str
    amount: int
    currency: str = "BRL"
    order: Dict[str, Any]
    customer: Optional[Dict[str, Any]] = None
    device: Optional[Dict[str, Any]] = None
    shippings: Optional[List[Dict[str, Any]]] = None


class MercadoPagoPaymentRequest(BaseModel):
    """Requisição de pagamento Mercado Pago"""
    transaction_amount: float
    description: str
    payment_method_id: str
    payer: Optional[Dict[str, Any]] = None
    external_reference: Optional[str] = None
    notification_url: Optional[str] = None


class WebhookConfig(BaseModel):
    """Configuração de webhook"""
    url: str
    events: List[str] = ["*"]
    enabled: bool = True
