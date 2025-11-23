"""
Router para endpoints de integração com PagSeguro
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field, EmailStr
from decimal import Decimal

from app.modules.auth.dependencies import get_current_user
from app.integrations.pagseguro import PagSeguroClient
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pagseguro", tags=["PagSeguro"])


# ============================================
# SCHEMAS
# ============================================

class CustomerSchema(BaseModel):
    """Schema para dados do cliente"""
    name: str
    email: EmailStr
    tax_id: str = Field(..., description="CPF/CNPJ")
    phones: Optional[list] = None


class PagamentoPIXRequest(BaseModel):
    """Request para criar pagamento PIX"""
    valor: Decimal = Field(..., gt=0, description="Valor em reais")
    descricao: str = Field(..., min_length=1, max_length=255)
    reference_id: str = Field(..., description="ID único da transação")
    customer: CustomerSchema
    expiration_minutes: Optional[int] = Field(30, ge=5, le=1440)


class CardSchema(BaseModel):
    """Schema para dados do cartão"""
    encrypted: Optional[str] = Field(None, description="Dados criptografados do cartão")
    security_code: Optional[str] = Field(None, min_length=3, max_length=4)
    holder: Optional[Dict[str, Any]] = Field(None, description="Dados do titular")


class PagamentoCartaoRequest(BaseModel):
    """Request para pagamento com cartão"""
    valor: Decimal = Field(..., gt=0)
    descricao: str = Field(..., min_length=1, max_length=255)
    reference_id: str
    customer: CustomerSchema
    card: CardSchema
    installments: int = Field(1, ge=1, le=12, description="Número de parcelas")


class BoletoRequest(BaseModel):
    """Request para criar boleto"""
    valor: Decimal = Field(..., gt=0)
    descricao: str = Field(..., min_length=1, max_length=255)
    reference_id: str
    customer: CustomerSchema
    due_date: Optional[str] = Field(None, description="Data vencimento YYYY-MM-DD")
    instruction_lines: Optional[Dict[str, str]] = None


# ============================================
# HELPER
# ============================================

def get_pagseguro_client() -> PagSeguroClient:
    """Retorna cliente PagSeguro configurado"""
    token = getattr(settings, 'PAGSEGURO_TOKEN', None)
    sandbox = getattr(settings, 'PAGSEGURO_SANDBOX', True)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PagSeguro não configurado (PAGSEGURO_TOKEN ausente)"
        )

    return PagSeguroClient(token=token, sandbox=sandbox)


# ============================================
# ENDPOINTS PIX
# ============================================

@router.post("/pix")
async def criar_pagamento_pix(
    dados: PagamentoPIXRequest,
    current_user=Depends(get_current_user)
):
    """
    Cria pagamento PIX com QR Code

    Retorna QR Code (texto e base64) para pagamento via PIX.

    **Funcionalidades:**
    - QR Code dinâmico
    - Expiração configurável (5 a 1440 minutos)
    - Notificação via webhook

    **Exemplo de resposta:**
    ```json
    {
        "sucesso": true,
        "id": "CHAR_XXXX",
        "qr_code": "00020126...",
        "qr_code_base64": "iVBORw0KGgoAAAANSUh...",
        "status": "WAITING"
    }
    ```
    """
    logger.info(f"Criando PIX PagSeguro - Valor: R$ {dados.valor}")

    try:
        client = get_pagseguro_client()

        # Converter valor para centavos
        valor_centavos = int(dados.valor * 100)

        resultado = await client.criar_pagamento_pix(
            valor=Decimal(valor_centavos),
            descricao=dados.descricao,
            reference_id=dados.reference_id,
            customer=dados.customer.dict(),
            expiration_date=None  # Será calculado pelo client
        )

        return resultado

    except Exception as e:
        logger.error(f"Erro ao criar PIX: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar PIX: {str(e)}"
        )


# ============================================
# ENDPOINTS CARTÃO
# ============================================

@router.post("/cartao")
async def criar_pagamento_cartao(
    dados: PagamentoCartaoRequest,
    current_user=Depends(get_current_user)
):
    """
    Cria pagamento com cartão de crédito

    **Importante:**
    - Use a biblioteca JavaScript do PagSeguro para criptografar dados do cartão
    - Nunca envie dados não criptografados do cartão
    - Suporta parcelamento em até 12x

    **Exemplo de resposta:**
    ```json
    {
        "sucesso": true,
        "id": "CHAR_XXXX",
        "status": "PAID",
        "paid_at": "2025-11-19T10:00:00Z"
    }
    ```
    """
    logger.info(f"Criando pagamento cartão PagSeguro - Valor: R$ {dados.valor}")

    try:
        client = get_pagseguro_client()
        valor_centavos = int(dados.valor * 100)

        resultado = await client.criar_pagamento_cartao(
            valor=Decimal(valor_centavos),
            descricao=dados.descricao,
            reference_id=dados.reference_id,
            customer=dados.customer.dict(),
            card=dados.card.dict(exclude_none=True),
            installments=dados.installments
        )

        return resultado

    except Exception as e:
        logger.error(f"Erro pagamento cartão: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar cartão: {str(e)}"
        )


# ============================================
# ENDPOINTS BOLETO
# ============================================

@router.post("/boleto")
async def criar_boleto(
    dados: BoletoRequest,
    current_user=Depends(get_current_user)
):
    """
    Cria boleto bancário

    **Funcionalidades:**
    - Vencimento configurável (padrão: 3 dias)
    - Código de barras
    - Linha digitável
    - Instruções personalizadas

    **Exemplo de resposta:**
    ```json
    {
        "sucesso": true,
        "id": "CHAR_XXXX",
        "barcode": "03399733100000100001091000123456789012345678901234",
        "formatted_barcode": "03399.73310 00001.000010 91000.123456 7 89012345678901234"
    }
    ```
    """
    logger.info(f"Criando boleto PagSeguro - Valor: R$ {dados.valor}")

    try:
        client = get_pagseguro_client()
        valor_centavos = int(dados.valor * 100)

        resultado = await client.criar_boleto(
            valor=Decimal(valor_centavos),
            descricao=dados.descricao,
            reference_id=dados.reference_id,
            customer=dados.customer.dict(),
            due_date=dados.due_date,
            instruction_lines=dados.instruction_lines
        )

        return resultado

    except Exception as e:
        logger.error(f"Erro ao criar boleto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar boleto: {str(e)}"
        )


# ============================================
# ENDPOINTS DE CONSULTA
# ============================================

@router.get("/cobrancas/{charge_id}")
async def consultar_cobranca(
    charge_id: str,
    current_user=Depends(get_current_user)
):
    """
    Consulta status de uma cobrança

    Retorna informações atualizadas incluindo status de pagamento.
    """
    logger.info(f"Consultando cobrança: {charge_id}")

    try:
        client = get_pagseguro_client()
        resultado = await client.consultar_cobranca(charge_id)
        return resultado

    except Exception as e:
        logger.error(f"Erro ao consultar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar cobrança: {str(e)}"
        )


@router.post("/cobrancas/{charge_id}/cancelar")
async def cancelar_cobranca(
    charge_id: str,
    current_user=Depends(get_current_user)
):
    """
    Cancela uma cobrança pendente

    Apenas cobranças com status WAITING ou AUTHORIZED podem ser canceladas.
    """
    logger.info(f"Cancelando cobrança: {charge_id}")

    try:
        client = get_pagseguro_client()
        resultado = await client.cancelar_cobranca(charge_id)
        return resultado

    except Exception as e:
        logger.error(f"Erro ao cancelar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao cancelar cobrança: {str(e)}"
        )


@router.post("/cobrancas/{charge_id}/capturar")
async def capturar_pagamento(
    charge_id: str,
    amount: Optional[int] = None,
    current_user=Depends(get_current_user)
):
    """
    Captura pagamento pré-autorizado

    Usado quando o pagamento foi criado com capture=false.

    **Parâmetros:**
    - amount: Valor em centavos (opcional, captura total se omitido)
    """
    logger.info(f"Capturando pagamento: {charge_id}")

    try:
        client = get_pagseguro_client()
        resultado = await client.capturar_pagamento(charge_id, amount)
        return resultado

    except Exception as e:
        logger.error(f"Erro ao capturar: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao capturar pagamento: {str(e)}"
        )


# ============================================
# WEBHOOK
# ============================================

@router.post("/webhook")
async def processar_webhook(request: Request):
    """
    Processa webhooks do PagSeguro

    **Importante:**
    - Configure a URL do webhook no painel do PagSeguro
    - Endpoint público (sem autenticação)
    - Processa eventos: CHARGE.PAID, CHARGE.DECLINED, etc.

    **Eventos suportados:**
    - CHARGE.PAID - Cobrança paga
    - CHARGE.DECLINED - Cobrança recusada
    - CHARGE.CANCELED - Cobrança cancelada
    - CHARGE.IN_ANALYSIS - Em análise
    """
    logger.info("Webhook PagSeguro recebido")

    try:
        payload = await request.json()
        client = get_pagseguro_client()

        dados = client.processar_webhook(payload)

        # TODO: Atualizar status no banco de dados
        # TODO: Disparar notificações para o cliente
        # TODO: Processar ações baseadas no status

        logger.info(f"Webhook processado - Charge: {dados['charge_id']}, Status: {dados['status']}")

        return {
            "sucesso": True,
            "mensagem": "Webhook processado com sucesso",
            "dados": dados
        }

    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        # Retornar 200 mesmo com erro para não reenviar webhook
        return {
            "sucesso": False,
            "erro": str(e)
        }


# ============================================
# HEALTH CHECK
# ============================================

@router.get("/health")
async def health_check():
    """
    Verifica configuração do PagSeguro

    Retorna status da configuração (token presente, ambiente).
    """
    token = getattr(settings, 'PAGSEGURO_TOKEN', None)
    sandbox = getattr(settings, 'PAGSEGURO_SANDBOX', True)

    return {
        "status": "ok" if token else "sem_configuracao",
        "configurado": bool(token),
        "ambiente": "sandbox" if sandbox else "producao",
        "metodos_disponiveis": ["PIX", "CARTAO", "BOLETO"]
    }
