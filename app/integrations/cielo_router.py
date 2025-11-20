"""
Router para Gateway Cielo

Endpoints REST para pagamentos com cartão via Cielo
"""
from fastapi import APIRouter, Depends, status, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.core.logging import get_logger

from .cielo import CieloClient, CieloCardBrand, CieloEnvironment

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class CreditCardPaymentRequest(BaseModel):
    """Request de pagamento com cartão de crédito"""
    amount: float = Field(..., gt=0, description="Valor do pagamento")
    installments: int = Field(1, ge=1, le=12, description="Número de parcelas")

    # Dados do cartão
    card_number: Optional[str] = Field(None, description="Número do cartão")
    card_holder: Optional[str] = Field(None, description="Nome no cartão")
    card_expiration_date: Optional[str] = Field(None, description="Validade MM/YYYY")
    card_cvv: Optional[str] = Field(None, description="CVV")
    card_brand: Optional[str] = Field(None, description="Bandeira")

    # Ou token
    card_token: Optional[str] = Field(None, description="Token do cartão")

    # Configurações
    capture: bool = Field(True, description="Captura automática")
    soft_descriptor: Optional[str] = Field(None, max_length=13, description="Texto na fatura")

    # Cliente
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_cpf: Optional[str] = None

    # Pedido
    order_id: Optional[str] = None


class DebitCardPaymentRequest(BaseModel):
    """Request de pagamento com cartão de débito"""
    amount: float = Field(..., gt=0)
    card_number: str
    card_holder: str
    card_expiration_date: str
    card_cvv: str
    card_brand: str
    return_url: str = Field(..., description="URL de retorno após autenticação")

    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    order_id: Optional[str] = None


class TokenizeCardRequest(BaseModel):
    """Request de tokenização de cartão"""
    card_number: str
    card_holder: str
    card_expiration_date: str
    card_brand: str


class CapturePaymentRequest(BaseModel):
    """Request de captura"""
    amount: Optional[float] = Field(None, description="Valor a capturar (None = total)")


class CancelPaymentRequest(BaseModel):
    """Request de cancelamento"""
    amount: Optional[float] = Field(None, description="Valor a cancelar (None = total)")


class PaymentResponse(BaseModel):
    """Response de pagamento"""
    success: bool
    payment_id: Optional[str] = None
    status: str
    status_description: str
    amount: float
    provider_response: Dict[str, Any]


# ============================================================================
# ENDPOINTS - PAGAMENTO CARTÃO DE CRÉDITO
# ============================================================================

@router.post(
    "/cielo/credit-card",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pagamento com cartão de crédito",
    description="Processar pagamento com cartão de crédito via Cielo"
)
async def create_credit_card_payment(
    request: CreditCardPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pagamento com cartão de crédito

    **Suporta**:
    - Parcelamento em até 12x
    - Tokenização de cartões (PCI compliant)
    - Captura automática ou manual
    - Todas as bandeiras principais

    **Exemplo com dados do cartão**:
    ```json
    {
        "amount": 150.00,
        "installments": 3,
        "card_number": "4111111111111111",
        "card_holder": "João da Silva",
        "card_expiration_date": "12/2025",
        "card_cvv": "123",
        "card_brand": "Visa",
        "capture": true,
        "customer_name": "João da Silva",
        "order_id": "PED-123"
    }
    ```

    **Exemplo com token**:
    ```json
    {
        "amount": 150.00,
        "installments": 1,
        "card_token": "TOKEN-XYZ123",
        "card_cvv": "123",
        "capture": true
    }
    ```
    """
    logger.info(f"Cielo credit card payment: amount={request.amount}, installments={request.installments}")

    try:
        # Cliente Cielo
        client = CieloClient(environment=CieloEnvironment.SANDBOX)

        # Preparar dados do cliente
        customer = None
        if request.customer_name:
            customer = {"Name": request.customer_name}
            if request.customer_email:
                customer["Email"] = request.customer_email
            if request.customer_cpf:
                customer["Identity"] = request.customer_cpf
                customer["IdentityType"] = "CPF"

        # Criar pagamento
        result = await client.create_credit_card_payment(
            amount=request.amount,
            installments=request.installments,
            card_number=request.card_number,
            card_holder=request.card_holder,
            card_expiration_date=request.card_expiration_date,
            card_cvv=request.card_cvv,
            card_brand=CieloCardBrand(request.card_brand) if request.card_brand else None,
            card_token=request.card_token,
            capture=request.capture,
            soft_descriptor=request.soft_descriptor,
            customer=customer,
            order_id=request.order_id
        )

        # Verificar sucesso
        success = client.is_success(result)
        payment = result.get("Payment", {})
        payment_id = payment.get("PaymentId")
        status_code = str(payment.get("Status", ""))

        logger.info(f"Cielo payment created: payment_id={payment_id}, success={success}")

        return PaymentResponse(
            success=success,
            payment_id=payment_id,
            status=status_code,
            status_description=client.format_status(status_code),
            amount=request.amount,
            provider_response=result
        )

    except Exception as e:
        logger.error(f"Cielo payment error: {str(e)}")
        raise


# ============================================================================
# ENDPOINTS - PAGAMENTO CARTÃO DE DÉBITO
# ============================================================================

@router.post(
    "/cielo/debit-card",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pagamento com cartão de débito",
    description="Processar pagamento com cartão de débito via Cielo (requer autenticação)"
)
async def create_debit_card_payment(
    request: DebitCardPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pagamento com cartão de débito

    **ATENÇÃO**: Débito requer autenticação 3DS.
    O retorno conterá uma URL para redirecionamento do cliente.

    **Exemplo**:
    ```json
    {
        "amount": 50.00,
        "card_number": "5200000000001096",
        "card_holder": "João da Silva",
        "card_expiration_date": "12/2025",
        "card_cvv": "123",
        "card_brand": "Master",
        "return_url": "https://sualoja.com/payment/return"
    }
    ```
    """
    logger.info(f"Cielo debit card payment: amount={request.amount}")

    try:
        client = CieloClient(environment=CieloEnvironment.SANDBOX)

        customer = None
        if request.customer_name:
            customer = {"Name": request.customer_name}
            if request.customer_email:
                customer["Email"] = request.customer_email

        result = await client.create_debit_card_payment(
            amount=request.amount,
            card_number=request.card_number,
            card_holder=request.card_holder,
            card_expiration_date=request.card_expiration_date,
            card_cvv=request.card_cvv,
            card_brand=CieloCardBrand(request.card_brand),
            return_url=request.return_url,
            customer=customer,
            order_id=request.order_id
        )

        payment = result.get("Payment", {})
        payment_id = payment.get("PaymentId")
        status_code = str(payment.get("Status", ""))

        logger.info(f"Cielo debit payment created: payment_id={payment_id}")

        return PaymentResponse(
            success=False,  # Aguardando autenticação
            payment_id=payment_id,
            status=status_code,
            status_description="Aguardando autenticação",
            amount=request.amount,
            provider_response=result
        )

    except Exception as e:
        logger.error(f"Cielo debit payment error: {str(e)}")
        raise


# ============================================================================
# ENDPOINTS - TOKENIZAÇÃO
# ============================================================================

@router.post(
    "/cielo/tokenize",
    summary="Tokenizar cartão",
    description="Tokenizar cartão para uso futuro (seguro PCI compliant)"
)
async def tokenize_card(
    request: TokenizeCardRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tokenizar cartão

    Permite armazenar um token do cartão para compras futuras
    sem armazenar dados sensíveis.

    **Exemplo**:
    ```json
    {
        "card_number": "4111111111111111",
        "card_holder": "João da Silva",
        "card_expiration_date": "12/2025",
        "card_brand": "Visa"
    }
    ```

    **Retorna**:
    ```json
    {
        "card_token": "TOKEN-ABC123XYZ",
        "success": true
    }
    ```
    """
    logger.info("Tokenizing card")

    try:
        client = CieloClient(environment=CieloEnvironment.SANDBOX)

        card_token = await client.tokenize_card(
            card_number=request.card_number,
            card_holder=request.card_holder,
            card_expiration_date=request.card_expiration_date,
            card_brand=CieloCardBrand(request.card_brand)
        )

        logger.info(f"Card tokenized successfully: {card_token[:10]}...")

        return {
            "card_token": card_token,
            "success": True
        }

    except Exception as e:
        logger.error(f"Tokenization error: {str(e)}")
        raise


# ============================================================================
# ENDPOINTS - CAPTURA E CANCELAMENTO
# ============================================================================

@router.put(
    "/cielo/payments/{payment_id}/capture",
    response_model=PaymentResponse,
    summary="Capturar pagamento",
    description="Capturar pagamento previamente autorizado"
)
async def capture_payment(
    payment_id: str,
    request: CapturePaymentRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Capturar pagamento autorizado

    Quando um pagamento é criado com `capture=false`,
    ele fica autorizado mas não capturado. Use este endpoint
    para confirmar a captura.

    **Exemplo**:
    ```json
    {
        "amount": null  // null = capturar valor total
    }
    ```
    """
    logger.info(f"Capturing payment: {payment_id}")

    try:
        client = CieloClient(environment=CieloEnvironment.SANDBOX)

        result = await client.capture_payment(payment_id, request.amount)

        payment = result.get("Payment", {}) if "Payment" in result else result
        status_code = str(payment.get("Status", ""))

        logger.info(f"Payment captured: {payment_id}")

        return PaymentResponse(
            success=True,
            payment_id=payment_id,
            status=status_code,
            status_description=client.format_status(status_code),
            amount=request.amount or 0,
            provider_response=result
        )

    except Exception as e:
        logger.error(f"Capture error: {str(e)}")
        raise


@router.put(
    "/cielo/payments/{payment_id}/cancel",
    response_model=PaymentResponse,
    summary="Cancelar pagamento",
    description="Cancelar/estornar pagamento"
)
async def cancel_payment(
    payment_id: str,
    request: CancelPaymentRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancelar ou estornar pagamento

    - Se ainda não capturado: cancela a autorização
    - Se já capturado: realiza estorno

    **Exemplo**:
    ```json
    {
        "amount": 50.00  // cancelar parcialmente, ou null para total
    }
    ```
    """
    logger.info(f"Canceling payment: {payment_id}")

    try:
        client = CieloClient(environment=CieloEnvironment.SANDBOX)

        result = await client.cancel_payment(payment_id, request.amount)

        payment = result.get("Payment", {}) if "Payment" in result else result
        status_code = str(payment.get("Status", ""))

        logger.info(f"Payment canceled: {payment_id}")

        return PaymentResponse(
            success=True,
            payment_id=payment_id,
            status=status_code,
            status_description=client.format_status(status_code),
            amount=request.amount or 0,
            provider_response=result
        )

    except Exception as e:
        logger.error(f"Cancel error: {str(e)}")
        raise


# ============================================================================
# ENDPOINTS - CONSULTAS
# ============================================================================

@router.get(
    "/cielo/payments/{payment_id}",
    summary="Consultar pagamento por ID",
    description="Buscar detalhes de um pagamento"
)
async def query_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Consultar pagamento

    Retorna detalhes completos do pagamento incluindo status atual.
    """
    logger.info(f"Querying payment: {payment_id}")

    try:
        client = CieloClient(environment=CieloEnvironment.SANDBOX)

        result = await client.query_payment(payment_id)

        logger.info(f"Payment found: {payment_id}")

        return result

    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise


@router.get(
    "/cielo/orders/{order_id}",
    summary="Consultar por Order ID",
    description="Buscar pagamento pelo ID do pedido"
)
async def query_by_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Consultar pagamento por Order ID

    Busca pagamento usando o ID do pedido do seu sistema.
    """
    logger.info(f"Querying by order: {order_id}")

    try:
        client = CieloClient(environment=CieloEnvironment.SANDBOX)

        result = await client.query_payment_by_order(order_id)

        logger.info(f"Payment found for order: {order_id}")

        return result

    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/cielo/health",
    summary="Health check Cielo",
    description="Verifica se a integração com Cielo está funcionando"
)
async def health_check():
    """Health check da integração Cielo"""
    return {
        "status": "healthy",
        "provider": "cielo",
        "api_version": "3.0",
        "features": {
            "credit_card": True,
            "debit_card": True,
            "installments": True,
            "tokenization": True,
            "capture": True,
            "cancel": True,
            "refund": True
        },
        "supported_brands": [
            "Visa", "Master", "Elo", "Amex",
            "Diners", "Discover", "JCB", "Aura"
        ]
    }
