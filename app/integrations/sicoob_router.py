"""
Router para integração Sicoob
Endpoints REST para PIX e Boleto
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.integrations.sicoob import (
    SicoobClient,
    SicoobEnvironment
)
import os


router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================

class PixChargeRequest(BaseModel):
    """Request para cobrança PIX"""
    amount: float = Field(..., gt=0, description="Valor em reais")
    txid: Optional[str] = Field(None, min_length=26, max_length=35)
    payer_cpf: Optional[str] = Field(None, min_length=11, max_length=14)
    payer_name: Optional[str] = None
    expiration_seconds: int = Field(1800, ge=60, le=86400, description="Expiração em segundos (padrão 30min)")
    info_adicional: Optional[str] = None


class PixStaticQrRequest(BaseModel):
    """Request para QR Code estático"""
    amount: Optional[float] = Field(None, gt=0, description="Valor (None = aberto)")
    description: Optional[str] = None


class PixRefundRequest(BaseModel):
    """Request para devolução PIX"""
    amount: float = Field(..., gt=0)
    reason: Optional[str] = None


class BoletoAddress(BaseModel):
    """Endereço para boleto"""
    logradouro: str
    numero: str
    bairro: str
    cidade: str
    uf: str = Field(..., min_length=2, max_length=2)
    cep: str = Field(..., pattern="^[0-9]{8}$")


class BoletoCreateRequest(BaseModel):
    """Request para criar boleto"""
    amount: float = Field(..., gt=0)
    due_date: datetime
    payer_name: str = Field(..., min_length=3)
    payer_document: str = Field(..., min_length=11, max_length=14)
    payer_address: BoletoAddress
    description: Optional[str] = None
    fine_percentage: float = Field(0.0, ge=0, le=100, description="Multa (%)")
    interest_percentage: float = Field(0.0, ge=0, le=100, description="Juros ao mês (%)")


class PixChargeResponse(BaseModel):
    """Response de cobrança PIX"""
    txid: str
    status: str
    status_formatted: str
    amount: float
    qr_code: Optional[str] = None
    payload_code: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class BoletoResponse(BaseModel):
    """Response de boleto"""
    nosso_numero: str
    linha_digitavel: str
    codigo_barras: str
    status: str
    amount: float
    due_date: datetime


# ============================================================================
# DEPENDENCY
# ============================================================================

def get_sicoob_client() -> SicoobClient:
    """
    Retorna cliente Sicoob configurado
    """
    client_id = os.getenv("SICOOB_CLIENT_ID")
    client_secret = os.getenv("SICOOB_CLIENT_SECRET")
    certificate = os.getenv("SICOOB_CERTIFICATE_PATH")
    env = os.getenv("SICOOB_ENVIRONMENT", "sandbox")

    environment = SicoobEnvironment.SANDBOX if env == "sandbox" else SicoobEnvironment.PRODUCTION

    return SicoobClient(
        client_id=client_id,
        client_secret=client_secret,
        certificate_path=certificate,
        environment=environment
    )


# ============================================================================
# ENDPOINTS PIX
# ============================================================================

@router.post(
    "/sicoob/pix/charge",
    response_model=PixChargeResponse,
    summary="Criar cobrança PIX",
    description="Cria cobrança PIX imediata com QR Code dinâmico"
)
async def create_pix_charge(
    request: PixChargeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cria cobrança PIX Sicoob

    - **QR Code**: Base64 para exibição
    - **Payload**: Copia e cola para pagamento manual
    - **Expiração**: Configurável (30min padrão)
    """
    try:
        client = get_sicoob_client()

        response = await client.create_pix_charge(
            amount=request.amount,
            txid=request.txid,
            payer_cpf=request.payer_cpf,
            payer_name=request.payer_name,
            expiration_seconds=request.expiration_seconds,
            info_adicional=request.info_adicional
        )

        return PixChargeResponse(
            txid=response.get("txid", ""),
            status=response.get("status", "ATIVA"),
            status_formatted=client.format_pix_status(response.get("status", "ATIVA")),
            amount=request.amount,
            qr_code=response.get("pixCopiaECola"),
            payload_code=response.get("pixCopiaECola"),
            location=response.get("location")
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar cobrança PIX: {str(e)}"
        )


@router.post(
    "/sicoob/pix/static-qr",
    response_model=PixChargeResponse,
    summary="Criar QR Code PIX estático",
    description="Cria QR Code estático (valor fixo ou aberto)"
)
async def create_pix_static_qr(
    request: PixStaticQrRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cria QR Code PIX estático

    - **Valor aberto**: Não informar amount
    - **Valor fixo**: Informar amount
    """
    try:
        client = get_sicoob_client()

        response = await client.create_pix_static_qr(
            amount=request.amount,
            description=request.description
        )

        return PixChargeResponse(
            txid=response.get("txid", "static"),
            status="ATIVA",
            status_formatted="Ativa",
            amount=request.amount or 0.0,
            qr_code=response.get("pixCopiaECola"),
            payload_code=response.get("pixCopiaECola")
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar QR Code estático: {str(e)}"
        )


@router.get(
    "/sicoob/pix/charge/{txid}",
    response_model=PixChargeResponse,
    summary="Consultar cobrança PIX",
    description="Consulta status de cobrança PIX por txid"
)
async def query_pix_charge(
    txid: str,
    current_user: User = Depends(get_current_user)
):
    """
    Consulta cobrança PIX por txid

    Retorna status atualizado e informações de pagamento
    """
    try:
        client = get_sicoob_client()

        response = await client.query_pix_charge(txid)

        return PixChargeResponse(
            txid=response.get("txid", txid),
            status=response.get("status", ""),
            status_formatted=client.format_pix_status(response.get("status", "")),
            amount=float(response.get("valor", {}).get("original", 0)),
            qr_code=response.get("pixCopiaECola"),
            payload_code=response.get("pixCopiaECola"),
            location=response.get("location")
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cobrança não encontrada: {str(e)}"
        )


@router.get(
    "/sicoob/pix/payment/{e2e_id}",
    summary="Consultar pagamento PIX",
    description="Consulta pagamento PIX recebido por E2E ID"
)
async def query_pix_payment(
    e2e_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Consulta pagamento PIX recebido

    Args:
        e2e_id: End-to-End ID da transação PIX
    """
    try:
        client = get_sicoob_client()

        response = await client.query_pix_payment(e2e_id)

        return {
            "e2e_id": e2e_id,
            "txid": response.get("txid"),
            "amount": float(response.get("valor", 0)),
            "payer": response.get("pagador"),
            "timestamp": response.get("horario"),
            "info_adicional": response.get("infoPagador")
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pagamento não encontrado: {str(e)}"
        )


@router.post(
    "/sicoob/pix/{e2e_id}/refund",
    summary="Devolver pagamento PIX",
    description="Solicita devolução de pagamento PIX"
)
async def refund_pix_payment(
    e2e_id: str,
    request: PixRefundRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Devolve pagamento PIX

    - **Devolução total**: amount = valor original
    - **Devolução parcial**: amount < valor original
    """
    try:
        client = get_sicoob_client()

        # Gerar refund_id único
        import uuid
        refund_id = uuid.uuid4().hex[:20]

        response = await client.refund_pix_payment(
            e2e_id=e2e_id,
            refund_id=refund_id,
            amount=request.amount,
            reason=request.reason
        )

        return {
            "success": True,
            "refund_id": refund_id,
            "e2e_id": e2e_id,
            "amount": request.amount,
            "status": response.get("status"),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao devolver pagamento: {str(e)}"
        )


@router.get(
    "/sicoob/pix/charges",
    summary="Listar cobranças PIX",
    description="Lista cobranças PIX em um período"
)
async def list_pix_charges(
    start_date: datetime,
    end_date: datetime,
    status_filter: Optional[str] = None,
    page: int = 0,
    items_per_page: int = 100,
    current_user: User = Depends(get_current_user)
):
    """
    Lista cobranças PIX

    Status válidos: ATIVA, CONCLUIDA, REMOVIDA_PELO_USUARIO_RECEBEDOR, REMOVIDA_PELO_PSP
    """
    try:
        client = get_sicoob_client()

        response = await client.list_pix_charges(
            start_date=start_date,
            end_date=end_date,
            status=status_filter,
            page=page,
            items_per_page=items_per_page
        )

        return {
            "charges": response.get("cobs", []),
            "pagination": response.get("paginacao", {}),
            "total": len(response.get("cobs", []))
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar cobranças: {str(e)}"
        )


# ============================================================================
# ENDPOINTS BOLETO
# ============================================================================

@router.post(
    "/sicoob/boleto",
    response_model=BoletoResponse,
    summary="Criar boleto",
    description="Cria boleto bancário Sicoob"
)
async def create_boleto(
    request: BoletoCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Cria boleto bancário

    - **Multa**: Percentual aplicado após vencimento
    - **Juros**: Percentual ao mês após vencimento
    """
    try:
        client = get_sicoob_client()

        response = await client.create_boleto(
            amount=request.amount,
            due_date=request.due_date,
            payer_name=request.payer_name,
            payer_document=request.payer_document,
            payer_address=request.payer_address.dict(),
            description=request.description,
            fine_percentage=request.fine_percentage,
            interest_percentage=request.interest_percentage
        )

        return BoletoResponse(
            nosso_numero=response.get("nossoNumero", ""),
            linha_digitavel=response.get("linhaDigitavel", ""),
            codigo_barras=response.get("codigoBarras", ""),
            status=response.get("situacao", "EMITIDO"),
            amount=request.amount,
            due_date=request.due_date
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar boleto: {str(e)}"
        )


@router.get(
    "/sicoob/boleto/{nosso_numero}",
    response_model=BoletoResponse,
    summary="Consultar boleto",
    description="Consulta boleto por nosso número"
)
async def query_boleto(
    nosso_numero: str,
    current_user: User = Depends(get_current_user)
):
    """
    Consulta boleto

    Retorna status atualizado e informações de pagamento
    """
    try:
        client = get_sicoob_client()

        response = await client.query_boleto(nosso_numero)

        return BoletoResponse(
            nosso_numero=response.get("nossoNumero", nosso_numero),
            linha_digitavel=response.get("linhaDigitavel", ""),
            codigo_barras=response.get("codigoBarras", ""),
            status=response.get("situacao", ""),
            amount=float(response.get("valor", 0)),
            due_date=datetime.fromisoformat(response.get("dataVencimento", datetime.now().isoformat()))
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Boleto não encontrado: {str(e)}"
        )


@router.delete(
    "/sicoob/boleto/{nosso_numero}",
    summary="Cancelar boleto",
    description="Cancela boleto antes do pagamento"
)
async def cancel_boleto(
    nosso_numero: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancela boleto não pago

    Boletos já pagos não podem ser cancelados
    """
    try:
        client = get_sicoob_client()

        await client.cancel_boleto(nosso_numero)

        return {
            "success": True,
            "nosso_numero": nosso_numero,
            "message": "Boleto cancelado com sucesso",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao cancelar boleto: {str(e)}"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/sicoob/health",
    summary="Health check",
    description="Verifica status da integração Sicoob"
)
async def health_check():
    """
    Health check da integração Sicoob

    Retorna status e configuração do ambiente
    """
    try:
        client = get_sicoob_client()

        return {
            "status": "healthy",
            "service": "Sicoob",
            "environment": client.environment.value,
            "client_id": client.client_id[:10] + "..." if client.client_id else None,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Serviço indisponível: {str(e)}"
        )
