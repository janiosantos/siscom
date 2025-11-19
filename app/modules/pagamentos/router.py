"""
Router para Pagamentos (PIX, Boleto, Conciliação)
"""
from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.logging import get_logger
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.models import User
from app.modules.pagamentos.schemas import (
    # PIX
    ChavePixCreate, ChavePixInResponse,
    TransacaoPixCreate, TransacaoPixInResponse,
    WebhookPixPayload,
    # Boleto
    ConfiguracaoBoletoCreate, ConfiguracaoBoletoInResponse,
    BoletoCreate, BoletoInResponse,
    # Conciliação
    ExtratoBancarioInResponse,
    ConciliacaoBancariaInResponse,
    ImportCSVRequest,
)
from app.modules.pagamentos.services.pix_service import PixService
from app.modules.pagamentos.services.boleto_service import BoletoService
from app.modules.pagamentos.services.conciliacao_service import ConciliacaoService

logger = get_logger(__name__)
router = APIRouter()


# ==============================================================================
# PIX Endpoints
# ==============================================================================

@router.post("/pix/chaves", response_model=ChavePixInResponse, status_code=status.HTTP_201_CREATED)
async def criar_chave_pix(
    chave_data: ChavePixCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cria uma nova chave PIX

    Requer permissão: financeiro:create
    """
    service = PixService(db)
    return await service.criar_chave_pix(chave_data)


@router.get("/pix/chaves", response_model=List[ChavePixInResponse])
async def listar_chaves_pix(
    ativa: bool = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Lista chaves PIX cadastradas

    Requer permissão: financeiro:read
    """
    service = PixService(db)
    return await service.listar_chaves_pix(ativa=ativa)


@router.post("/pix/cobrar", response_model=TransacaoPixInResponse, status_code=status.HTTP_201_CREATED)
async def criar_cobranca_pix(
    cobranca_data: TransacaoPixCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cria uma cobrança PIX com QR Code

    Requer permissão: financeiro:create

    Retorna:
    - QR Code texto (copia e cola)
    - QR Code imagem (base64)
    - TXID para rastreamento
    """
    service = PixService(db)
    return await service.criar_cobranca_pix(cobranca_data)


@router.get("/pix/transacoes/{txid}", response_model=TransacaoPixInResponse)
async def consultar_transacao_pix(
    txid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Consulta status de uma transação PIX

    Requer permissão: financeiro:read
    """
    service = PixService(db)
    transacao = await service.consultar_transacao(txid)

    if not transacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação PIX não encontrada"
        )

    return transacao


@router.post("/pix/webhook", status_code=status.HTTP_200_OK)
async def webhook_pix(
    webhook_data: WebhookPixPayload,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Webhook para confirmação de pagamento PIX

    Endpoint público (sem autenticação)
    Em produção, validar assinatura do webhook
    """
    service = PixService(db)
    await service.processar_webhook_pagamento(webhook_data)

    return {"status": "processed"}


@router.delete("/pix/transacoes/{txid}", status_code=status.HTTP_204_NO_CONTENT)
async def cancelar_cobranca_pix(
    txid: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cancela uma cobrança PIX pendente

    Requer permissão: financeiro:delete
    """
    service = PixService(db)
    await service.cancelar_cobranca(txid)


# ==============================================================================
# Boleto Endpoints
# ==============================================================================

@router.post("/boletos/configuracoes", response_model=ConfiguracaoBoletoInResponse, status_code=status.HTTP_201_CREATED)
async def criar_configuracao_boleto(
    config_data: ConfiguracaoBoletoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cria configuração de boleto para um banco

    Requer permissão: financeiro:create
    """
    service = BoletoService(db)
    return await service.criar_configuracao(config_data)


@router.post("/boletos", response_model=BoletoInResponse, status_code=status.HTTP_201_CREATED)
async def gerar_boleto(
    boleto_data: BoletoCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Gera um novo boleto bancário

    Requer permissão: financeiro:create

    Retorna:
    - Nosso número
    - Código de barras
    - Linha digitável
    """
    service = BoletoService(db)
    return await service.gerar_boleto(boleto_data)


@router.get("/boletos/{boleto_id}", response_model=BoletoInResponse)
async def consultar_boleto(
    boleto_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Consulta dados de um boleto

    Requer permissão: financeiro:read
    """
    service = BoletoService(db)
    boleto = await service.consultar_boleto(boleto_id)

    if not boleto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boleto não encontrado"
        )

    return boleto


# ==============================================================================
# Conciliação Endpoints
# ==============================================================================

@router.post("/conciliacao/import-csv")
async def importar_extrato_csv(
    import_data: ImportCSVRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Importa extrato bancário de arquivo CSV

    Requer permissão: financeiro:create

    Formato CSV esperado:
    data,descricao,documento,valor,tipo
    2025-11-19,PIX RECEBIDO,E12345...,150.00,C
    """
    service = ConciliacaoService(db)
    return await service.importar_extrato_csv(import_data)


@router.get("/conciliacao/pendentes", response_model=List[ExtratoBancarioInResponse])
async def listar_pendentes(
    banco_codigo: str,
    conta: str,
    data_inicio: date = None,
    data_fim: date = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Lista lançamentos de extrato não conciliados

    Requer permissão: financeiro:read
    """
    service = ConciliacaoService(db)
    return await service.listar_pendentes(
        banco_codigo=banco_codigo,
        conta=conta,
        data_inicio=data_inicio,
        data_fim=data_fim
    )


@router.post("/conciliacao/auto-conciliar")
async def auto_conciliar(
    banco_codigo: str,
    data_inicio: date,
    data_fim: date,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Executa conciliação automática

    Requer permissão: financeiro:update

    Algoritmo:
    1. PIX: Match por E2E ID
    2. Boleto: Match por Nosso Número
    3. Tolerância: ±R$0,01 e ±1 dia
    """
    service = ConciliacaoService(db)
    return await service.conciliar_automaticamente(
        banco_codigo=banco_codigo,
        data_inicio=data_inicio,
        data_fim=data_fim
    )
