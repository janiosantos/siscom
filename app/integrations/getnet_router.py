"""
Router para integração GetNet
Endpoints REST para pagamentos com cartão e PIX
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import httpx
import os

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.integrations.getnet import (
    GetNetClient,
    GetNetEnvironment,
    GetNetCardBrand,
    GetNetPaymentType
)


router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class CreditCardPaymentRequest(BaseModel):
    """Request para pagamento com cartão de crédito"""
    amount: float = Field(..., gt=0, description="Valor em reais")
    order_id: str = Field(..., min_length=1, max_length=100)
    customer_id: str = Field(..., min_length=1)
    card_number: Optional[str] = Field(None, min_length=13, max_length=19)
    card_holder_name: Optional[str] = Field(None, min_length=3)
    card_expiration_month: Optional[str] = Field(None, pattern="^(0[1-9]|1[0-2])$")
    card_expiration_year: Optional[str] = Field(None, pattern="^[0-9]{2}$")
    card_cvv: Optional[str] = Field(None, min_length=3, max_length=4)
    card_token: Optional[str] = None
    installments: int = Field(1, ge=1, le=12)
    capture: bool = Field(True, description="Captura automática")
    description: Optional[str] = None


class DebitCardPaymentRequest(BaseModel):
    """Request para pagamento com cartão de débito"""
    amount: float = Field(..., gt=0)
    order_id: str = Field(..., min_length=1, max_length=100)
    customer_id: str = Field(..., min_length=1)
    card_number: str = Field(..., min_length=13, max_length=19)
    card_holder_name: str = Field(..., min_length=3)
    card_expiration_month: str = Field(..., pattern="^(0[1-9]|1[0-2])$")
    card_expiration_year: str = Field(..., pattern="^[0-9]{2}$")
    card_cvv: str = Field(..., min_length=3, max_length=4)
    description: Optional[str] = None


class PixPaymentRequest(BaseModel):
    """Request para pagamento PIX"""
    amount: float = Field(..., gt=0)
    order_id: str = Field(..., min_length=1, max_length=100)
    customer_id: str = Field(..., min_length=1)
    customer_name: str = Field(..., min_length=3)
    customer_document: str = Field(..., min_length=11, max_length=14)
    expiration_minutes: int = Field(30, ge=1, le=1440)
    description: Optional[str] = None


class TokenizeCardRequest(BaseModel):
    """Request para tokenização de cartão"""
    card_number: str = Field(..., min_length=13, max_length=19)
    customer_id: str = Field(..., min_length=1)


class CapturePaymentRequest(BaseModel):
    """Request para captura de pagamento"""
    amount: Optional[float] = Field(None, gt=0, description="Valor parcial (None = total)")


class CancelPaymentRequest(BaseModel):
    """Request para cancelamento"""
    amount: Optional[float] = Field(None, gt=0, description="Valor parcial (None = total)")


class PaymentResponse(BaseModel):
    """Response padrão de pagamento"""
    payment_id: str
    status: str
    status_formatted: str
    amount: float
    order_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = {}


# ============================================================================
# DEPENDENCY
# ============================================================================

def get_getnet_client() -> GetNetClient:
    """
    Retorna cliente GetNet configurado
    """
    seller_id = os.getenv("GETNET_SELLER_ID")
    client_id = os.getenv("GETNET_CLIENT_ID")
    client_secret = os.getenv("GETNET_CLIENT_SECRET")
    env = os.getenv("GETNET_ENVIRONMENT", "sandbox")

    environment = GetNetEnvironment.SANDBOX if env == "sandbox" else GetNetEnvironment.PRODUCTION

    return GetNetClient(
        seller_id=seller_id,
        client_id=client_id,
        client_secret=client_secret,
        environment=environment
    )


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/getnet/credit-card",
    response_model=PaymentResponse,
    summary="Pagamento com cartão de crédito",
    description="Processa pagamento com cartão de crédito via GetNet (1-12x)"
)
async def create_credit_card_payment(
    request: CreditCardPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cria pagamento com cartão de crédito GetNet

    - **Parcelamento**: 1 a 12 vezes
    - **Captura**: Automática ou manual
    - **Tokenização**: Suporta card_token para pagamentos recorrentes
    """
    try:
        client = get_getnet_client()

        response = await client.create_credit_card_payment(
            amount=request.amount,
            order_id=request.order_id,
            customer_id=request.customer_id,
            card_number=request.card_number,
            card_holder_name=request.card_holder_name,
            card_expiration_month=request.card_expiration_month,
            card_expiration_year=request.card_expiration_year,
            card_cvv=request.card_cvv,
            card_token=request.card_token,
            installments=request.installments,
            capture=request.capture,
            description=request.description
        )

        return PaymentResponse(
            payment_id=response.get("payment_id", ""),
            status=response.get("status", ""),
            status_formatted=client.format_status(response.get("status", "")),
            amount=request.amount,
            order_id=request.order_id,
            metadata=response
        )

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao processar pagamento: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@router.post(
    "/getnet/debit-card",
    response_model=PaymentResponse,
    summary="Pagamento com cartão de débito",
    description="Processa pagamento com cartão de débito via GetNet (requer 3DS)"
)
async def create_debit_card_payment(
    request: DebitCardPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cria pagamento com cartão de débito GetNet

    - **3DS**: Requer autenticação do banco
    - **Captura**: Automática após autenticação
    """
    try:
        client = get_getnet_client()

        response = await client.create_debit_card_payment(
            amount=request.amount,
            order_id=request.order_id,
            customer_id=request.customer_id,
            card_number=request.card_number,
            card_holder_name=request.card_holder_name,
            card_expiration_month=request.card_expiration_month,
            card_expiration_year=request.card_expiration_year,
            card_cvv=request.card_cvv,
            description=request.description
        )

        return PaymentResponse(
            payment_id=response.get("payment_id", ""),
            status=response.get("status", ""),
            status_formatted=client.format_status(response.get("status", "")),
            amount=request.amount,
            order_id=request.order_id,
            metadata=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar pagamento: {str(e)}"
        )


@router.post(
    "/getnet/pix",
    response_model=PaymentResponse,
    summary="Pagamento PIX",
    description="Cria pagamento PIX com QR Code dinâmico"
)
async def create_pix_payment(
    request: PixPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cria pagamento PIX GetNet

    - **QR Code**: Base64 para exibição
    - **Copia e Cola**: EMV code para pagamento manual
    - **Expiração**: Configurável (padrão 30min)
    """
    try:
        client = get_getnet_client()

        response = await client.create_pix_payment(
            amount=request.amount,
            order_id=request.order_id,
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            customer_document=request.customer_document,
            expiration_minutes=request.expiration_minutes,
            description=request.description
        )

        return PaymentResponse(
            payment_id=response.get("payment_id", ""),
            status=response.get("status", "PENDING"),
            status_formatted="Aguardando Pagamento",
            amount=request.amount,
            order_id=request.order_id,
            metadata={
                **response,
                "qr_code": response.get("qr_code"),
                "qr_code_text": response.get("emv")
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar pagamento PIX: {str(e)}"
        )


@router.post(
    "/getnet/tokenize",
    summary="Tokenizar cartão",
    description="Tokeniza cartão para uso futuro (PCI compliant)"
)
async def tokenize_card(
    request: TokenizeCardRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Tokeniza cartão para pagamentos recorrentes

    - **Segurança**: PCI DSS compliant
    - **Reutilização**: Token pode ser usado em pagamentos futuros
    """
    try:
        client = get_getnet_client()

        token = await client.tokenize_card(
            card_number=request.card_number,
            customer_id=request.customer_id
        )

        return {
            "success": True,
            "card_token": token,
            "customer_id": request.customer_id
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao tokenizar cartão: {str(e)}"
        )


@router.put(
    "/getnet/payments/{payment_id}/capture",
    response_model=PaymentResponse,
    summary="Capturar pagamento",
    description="Captura pagamento pré-autorizado"
)
async def capture_payment(
    payment_id: str,
    request: CapturePaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Captura pagamento pré-autorizado

    - **Captura total**: Não enviar amount
    - **Captura parcial**: Enviar amount menor que o autorizado
    """
    try:
        client = get_getnet_client()

        response = await client.capture_payment(
            payment_id=payment_id,
            amount=request.amount
        )

        return PaymentResponse(
            payment_id=payment_id,
            status=response.get("status", ""),
            status_formatted=client.format_status(response.get("status", "")),
            amount=request.amount or 0.0,
            order_id="",
            metadata=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao capturar pagamento: {str(e)}"
        )


@router.put(
    "/getnet/payments/{payment_id}/cancel",
    response_model=PaymentResponse,
    summary="Cancelar pagamento",
    description="Cancela/estorna pagamento"
)
async def cancel_payment(
    payment_id: str,
    request: CancelPaymentRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cancela ou estorna pagamento

    - **Cancelamento total**: Não enviar amount
    - **Cancelamento parcial**: Enviar amount menor que o capturado
    """
    try:
        client = get_getnet_client()

        response = await client.cancel_payment(
            payment_id=payment_id,
            amount=request.amount
        )

        return PaymentResponse(
            payment_id=payment_id,
            status=response.get("status", ""),
            status_formatted=client.format_status(response.get("status", "")),
            amount=request.amount or 0.0,
            order_id="",
            metadata=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao cancelar pagamento: {str(e)}"
        )


@router.get(
    "/getnet/payments/{payment_id}",
    response_model=PaymentResponse,
    summary="Consultar pagamento",
    description="Consulta status de pagamento por ID"
)
async def query_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Consulta status de um pagamento

    Retorna informações completas incluindo status, valor e dados da transação
    """
    try:
        client = get_getnet_client()

        response = await client.query_payment(payment_id)

        return PaymentResponse(
            payment_id=payment_id,
            status=response.get("status", ""),
            status_formatted=client.format_status(response.get("status", "")),
            amount=response.get("amount", 0) / 100,
            order_id=response.get("order", {}).get("order_id", ""),
            metadata=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pagamento não encontrado: {str(e)}"
        )


@router.get(
    "/getnet/pix/{payment_id}",
    response_model=PaymentResponse,
    summary="Consultar pagamento PIX",
    description="Consulta status de pagamento PIX"
)
async def query_pix_payment(
    payment_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Consulta status de um pagamento PIX

    Retorna QR Code e status de pagamento
    """
    try:
        client = get_getnet_client()

        response = await client.query_pix_payment(payment_id)

        return PaymentResponse(
            payment_id=payment_id,
            status=response.get("status", ""),
            status_formatted=client.format_status(response.get("status", "")),
            amount=response.get("amount", 0) / 100,
            order_id=response.get("order", {}).get("order_id", ""),
            metadata=response
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pagamento PIX não encontrado: {str(e)}"
        )


@router.get(
    "/getnet/health",
    summary="Health check",
    description="Verifica status da integração GetNet"
)
async def health_check():
    """
    Health check da integração GetNet

    Retorna status e configuração do ambiente
    """
    try:
        client = get_getnet_client()

        return {
            "status": "healthy",
            "service": "GetNet",
            "environment": client.environment.value,
            "seller_id": client.seller_id[:10] + "..." if client.seller_id else None,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Serviço indisponível: {str(e)}"
        )
