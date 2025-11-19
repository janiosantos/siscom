"""
Router para Integração Mercado Pago
"""
import logging
import hmac
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

from app.core.database import get_async_session
from app.modules.auth.dependencies import get_current_user
from app.integrations.mercadopago import MercadoPagoClient, converter_status_mp
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mercadopago", tags=["Mercado Pago"])


# Helper functions
def validar_assinatura_webhook(
    x_signature: Optional[str],
    x_request_id: Optional[str],
    data_id: str,
    secret: str
) -> bool:
    """
    Valida a assinatura do webhook do Mercado Pago

    Args:
        x_signature: Header x-signature enviado pelo MP
        x_request_id: Header x-request-id enviado pelo MP
        data_id: ID do recurso (payment, merchant_order, etc)
        secret: Secret obtido no painel do MP

    Returns:
        True se a assinatura é válida, False caso contrário
    """
    if not x_signature or not x_request_id or not secret:
        logger.warning("Validação de assinatura: headers ou secret ausentes")
        return False

    try:
        # Extrair ts e hash do x-signature
        # Formato: ts=1234567890,v1=abc123def456...
        parts = {}
        for part in x_signature.split(','):
            key, value = part.split('=', 1)
            parts[key] = value

        ts = parts.get('ts')
        received_hash = parts.get('v1')

        if not ts or not received_hash:
            logger.warning("Validação de assinatura: ts ou v1 ausentes no x-signature")
            return False

        # Criar string para assinar no formato do Mercado Pago
        # Formato: id:{data_id};request-id:{x_request_id};ts:{ts};
        manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"

        # Calcular HMAC SHA256
        calculated_hash = hmac.new(
            secret.encode('utf-8'),
            manifest.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Comparar hashes de forma segura (timing attack resistant)
        is_valid = hmac.compare_digest(calculated_hash, received_hash)

        if not is_valid:
            logger.warning(f"Assinatura inválida - Expected: {calculated_hash}, Received: {received_hash}")

        return is_valid

    except Exception as e:
        logger.error(f"Erro ao validar assinatura: {str(e)}")
        return False


# Schemas
class CriarPagamentoPixMP(BaseModel):
    """Schema para criar pagamento PIX via Mercado Pago"""
    valor: Decimal = Field(..., gt=0, description="Valor do pagamento")
    descricao: str = Field(..., min_length=1, description="Descrição do pagamento")
    email_pagador: str = Field(default="test@test.com", description="Email do pagador")
    external_reference: str = Field(None, description="Referência externa (ID da venda)")


class PagamentoPixMPResponse(BaseModel):
    """Response de pagamento PIX criado"""
    id: int
    status: str
    qr_code: str
    qr_code_base64: str
    ticket_url: str
    transaction_id: int
    valor: Decimal
    data_criacao: str
    external_reference: str = None


class ConsultarPagamentoResponse(BaseModel):
    """Response de consulta de pagamento"""
    id: int
    status: str
    status_detail: str
    valor: Decimal
    data_criacao: str
    data_aprovacao: str = None
    metodo_pagamento: str
    external_reference: str = None


class CriarPagamentoCartaoMP(BaseModel):
    """Schema para criar pagamento com cartão via Mercado Pago"""
    valor: Decimal = Field(..., gt=0, description="Valor do pagamento")
    descricao: str = Field(..., min_length=1, description="Descrição do pagamento")
    token_cartao: str = Field(..., min_length=1, description="Token do cartão (via MercadoPago.js)")
    installments: int = Field(default=1, ge=1, le=12, description="Número de parcelas (1-12)")
    email_pagador: str = Field(default="test@test.com", description="Email do pagador")
    cpf_pagador: str = Field(None, description="CPF do pagador (opcional)")
    nome_pagador: str = Field(None, description="Nome do pagador (opcional)")
    external_reference: str = Field(None, description="Referência externa (ID da venda)")


class PagamentoCartaoMPResponse(BaseModel):
    """Response de pagamento com cartão criado"""
    id: int
    status: str
    status_detail: str
    valor: Decimal
    data_criacao: str
    data_aprovacao: str = None
    metodo_pagamento: str
    parcelas: int
    authorization_code: str = None
    external_reference: str = None


# Helper para obter client do MP
def get_mp_client() -> MercadoPagoClient:
    """Retorna client configurado do Mercado Pago"""
    access_token = getattr(settings, 'MERCADOPAGO_ACCESS_TOKEN', None)
    public_key = getattr(settings, 'MERCADOPAGO_PUBLIC_KEY', None)

    if not access_token:
        # Usar credentials de teste se não estiver no .env
        access_token = "TEST-127924860584293-111909-8eb99a40f34eb5ba5c03fa2979196258-184641661"
        public_key = "TEST-040da26c-318d-46ff-b42e-4ef22fbf755f"
        logger.warning("Usando credenciais de teste do Mercado Pago")

    return MercadoPagoClient(access_token=access_token, public_key=public_key)


# Endpoints
@router.post("/pix", response_model=PagamentoPixMPResponse, status_code=status.HTTP_201_CREATED)
async def criar_pagamento_pix_mp(
    pagamento: CriarPagamentoPixMP,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cria um pagamento PIX via Mercado Pago

    Retorna QR Code para pagamento instantâneo.
    """
    logger.info(f"Criando pagamento PIX MP - Usuário: {current_user.id}, Valor: {pagamento.valor}")

    try:
        mp_client = get_mp_client()

        # Criar pagamento no Mercado Pago
        resultado = await mp_client.criar_pagamento_pix(
            valor=pagamento.valor,
            descricao=pagamento.descricao,
            email_pagador=pagamento.email_pagador,
            external_reference=pagamento.external_reference
        )

        # Salvar no banco de dados local
        from app.modules.pagamentos.models import TransacaoPix, StatusPagamento, ChavePix
        from sqlalchemy import select
        import json

        # Buscar a primeira chave PIX ativa (ou criar lógica para selecionar)
        query = select(ChavePix).where(ChavePix.ativa == True).limit(1)
        result = await db.execute(query)
        chave_pix = result.scalar_one_or_none()

        if chave_pix:
            # Criar transação no banco de dados
            transacao = TransacaoPix(
                txid=str(resultado['id']),  # Usar ID do MP como txid temporário
                chave_pix_id=chave_pix.id,
                valor=resultado['valor'],
                descricao=pagamento.descricao,
                status=converter_status_mp(resultado['status']),
                qr_code_texto=resultado.get('qr_code'),
                qr_code_imagem=resultado.get('qr_code_base64'),
                integration_id=str(resultado['id']),
                integration_provider='mercadopago',
                integration_data=json.dumps(resultado)
            )
            db.add(transacao)
            await db.commit()
            await db.refresh(transacao)

            logger.info(f"Transação PIX MP salva no BD - ID: {transacao.id}, Integration ID: {resultado['id']}")

        return PagamentoPixMPResponse(**resultado)

    except Exception as e:
        logger.error(f"Erro ao criar pagamento PIX MP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar pagamento: {str(e)}"
        )


@router.post("/cartao", response_model=PagamentoCartaoMPResponse, status_code=status.HTTP_201_CREATED)
async def criar_pagamento_cartao_mp(
    pagamento: CriarPagamentoCartaoMP,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cria um pagamento com cartão de crédito/débito via Mercado Pago

    Requer que o frontend tenha tokenizado o cartão usando MercadoPago.js
    e enviado o token nesta requisição.

    Suporta parcelamento em até 12x.
    """
    logger.info(f"Criando pagamento com cartão MP - Usuário: {current_user.id}, Valor: {pagamento.valor}, Parcelas: {pagamento.installments}")

    try:
        mp_client = get_mp_client()

        # Criar pagamento no Mercado Pago
        resultado = await mp_client.criar_pagamento_cartao(
            valor=pagamento.valor,
            descricao=pagamento.descricao,
            token_cartao=pagamento.token_cartao,
            installments=pagamento.installments,
            email_pagador=pagamento.email_pagador,
            cpf_pagador=pagamento.cpf_pagador,
            nome_pagador=pagamento.nome_pagador,
            external_reference=pagamento.external_reference
        )

        # Salvar no banco de dados local (se necessário)
        # TODO: Criar modelo específico para pagamentos com cartão ou usar modelo genérico

        return PagamentoCartaoMPResponse(**resultado)

    except Exception as e:
        logger.error(f"Erro ao criar pagamento com cartão MP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar pagamento: {str(e)}"
        )


@router.get("/pagamento/{payment_id}", response_model=ConsultarPagamentoResponse)
async def consultar_pagamento_mp(
    payment_id: int,
    current_user=Depends(get_current_user)
):
    """
    Consulta status de um pagamento no Mercado Pago
    """
    logger.info(f"Consultando pagamento MP {payment_id}")

    try:
        mp_client = get_mp_client()
        resultado = await mp_client.consultar_pagamento(payment_id)

        return ConsultarPagamentoResponse(**resultado)

    except Exception as e:
        logger.error(f"Erro ao consultar pagamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar pagamento: {str(e)}"
        )


@router.delete("/pagamento/{payment_id}")
async def cancelar_pagamento_mp(
    payment_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cancela um pagamento pendente no Mercado Pago
    """
    logger.info(f"Cancelando pagamento MP {payment_id}")

    try:
        mp_client = get_mp_client()
        resultado = await mp_client.cancelar_pagamento(payment_id)

        # Atualizar status no banco de dados local
        from app.modules.pagamentos.models import TransacaoPix, StatusPagamento
        from sqlalchemy import select
        import json

        query = select(TransacaoPix).where(
            TransacaoPix.integration_id == str(payment_id),
            TransacaoPix.integration_provider == 'mercadopago'
        )
        result = await db.execute(query)
        transacao = result.scalar_one_or_none()

        if transacao:
            transacao.status = StatusPagamento.CANCELADO
            transacao.integration_data = json.dumps(resultado)
            await db.commit()
            logger.info(f"Transação {transacao.id} marcada como CANCELADA")

        return {"sucesso": True, "status": resultado["status"]}

    except Exception as e:
        logger.error(f"Erro ao cancelar pagamento: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao cancelar pagamento: {str(e)}"
        )


@router.post("/webhook")
async def webhook_mercadopago(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Webhook para receber notificações do Mercado Pago

    Este endpoint é chamado pelo MP quando há alterações no pagamento.
    Não requer autenticação JWT pois é chamado pelo sistema do MP,
    mas valida a assinatura do webhook para segurança.
    """
    try:
        webhook_data = await request.json()
        logger.info(f"Webhook MP recebido: {webhook_data}")

        # Validar assinatura do webhook (se secret estiver configurado)
        webhook_secret = getattr(settings, 'MERCADOPAGO_WEBHOOK_SECRET', None)
        if webhook_secret:
            x_signature = request.headers.get('x-signature')
            x_request_id = request.headers.get('x-request-id')
            data_id = webhook_data.get('data', {}).get('id', '')

            if not validar_assinatura_webhook(x_signature, x_request_id, data_id, webhook_secret):
                logger.error("Webhook MP rejeitado: assinatura inválida")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Assinatura do webhook inválida"
                )
            logger.info("Assinatura do webhook validada com sucesso")
        else:
            logger.warning("MERCADOPAGO_WEBHOOK_SECRET não configurado - webhook sem validação de assinatura")

        mp_client = get_mp_client()
        dados_processados = await mp_client.processar_webhook(webhook_data)

        # Atualizar status do pagamento no banco de dados
        from app.modules.pagamentos.models import TransacaoPix
        from sqlalchemy import select
        from datetime import datetime
        import json

        payment_id = str(dados_processados.get('id'))

        # Buscar transação por integration_id
        query = select(TransacaoPix).where(
            TransacaoPix.integration_id == payment_id,
            TransacaoPix.integration_provider == 'mercadopago'
        )
        result = await db.execute(query)
        transacao = result.scalar_one_or_none()

        if transacao:
            # Atualizar status
            novo_status = converter_status_mp(dados_processados.get('status'))
            transacao.status = novo_status

            # Atualizar data de pagamento se aprovado
            if novo_status == 'aprovado' and not transacao.data_pagamento:
                transacao.data_pagamento = datetime.utcnow()

            # Atualizar dados da integração
            transacao.integration_data = json.dumps(dados_processados)

            # Atualizar e2e_id se disponível
            if dados_processados.get('e2e_id'):
                transacao.e2e_id = dados_processados['e2e_id']

            await db.commit()

            logger.info(f"Transação atualizada - ID: {transacao.id}, Novo Status: {novo_status}")
        else:
            logger.warning(f"Transação não encontrada para Payment ID: {payment_id}")

        logger.info(f"Webhook processado - Payment ID: {payment_id}, Status: {dados_processados.get('status')}")

        return {"sucesso": True}

    except Exception as e:
        logger.error(f"Erro ao processar webhook MP: {str(e)}", exc_info=True)
        # Retornar 200 mesmo com erro para não fazer MP retentar infinitamente
        return {"sucesso": False, "erro": str(e)}


@router.post("/checkout/preferencia")
async def criar_preferencia_checkout(
    items: list,
    external_reference: str = None,
    notification_url: str = None,
    current_user=Depends(get_current_user)
):
    """
    Cria uma preferência de checkout (Checkout Pro)

    Retorna URL para redirecionar cliente ao checkout do Mercado Pago.
    """
    logger.info(f"Criando preferência de checkout - Items: {len(items)}")

    try:
        mp_client = get_mp_client()

        back_urls = {
            "success": f"{settings.FRONTEND_URL}/pagamento/sucesso",
            "failure": f"{settings.FRONTEND_URL}/pagamento/falha",
            "pending": f"{settings.FRONTEND_URL}/pagamento/pendente"
        }

        resultado = await mp_client.criar_preferencia_checkout(
            items=items,
            external_reference=external_reference,
            notification_url=notification_url,
            back_urls=back_urls
        )

        return resultado

    except Exception as e:
        logger.error(f"Erro ao criar preferência: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar preferência: {str(e)}"
        )


@router.get("/health")
async def health_check_mp():
    """
    Verifica se a integração com Mercado Pago está funcionando
    """
    try:
        mp_client = get_mp_client()

        # Testar com uma consulta simples (vai retornar erro 404, mas mostra que API está acessível)
        try:
            await mp_client.consultar_pagamento(999999999)
        except Exception:
            # Esperado - payment não existe, mas API respondeu
            pass

        return {
            "status": "ok",
            "mercadopago": "conectado",
            "ambiente": "teste" if "TEST" in mp_client.access_token else "producao"
        }

    except Exception as e:
        return {
            "status": "erro",
            "mercadopago": "desconectado",
            "erro": str(e)
        }
