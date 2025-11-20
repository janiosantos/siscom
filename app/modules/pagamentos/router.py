"""
Router para Pagamentos (PIX, Boleto, Conciliação)
"""
from typing import List
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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


# ==============================================================================
# CNAB 240/400
# ==============================================================================

@router.post("/cnab/remessa", response_model=schemas.CNABRemessaResponse, status_code=status.HTTP_201_CREATED)
async def gerar_arquivo_cnab_remessa(
    request_data: schemas.CNABRemessaRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Gera arquivo CNAB de remessa (envio de boletos ao banco)

    Formatos suportados:
    - 240: CNAB 240 (moderno, recomendado)
    - 400: CNAB 400 (legado, compatibilidade)
    """
    from app.modules.pagamentos.services.cnab_service import CNABService
    from sqlalchemy import select
    import base64
    from datetime import datetime

    service = CNABService(db)

    # Buscar boletos
    stmt = select(Boleto).where(Boleto.id.in_(request_data.boleto_ids))
    result = await db.execute(stmt)
    boletos = result.scalars().all()

    if not boletos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum boleto encontrado"
        )

    # Gerar arquivo CNAB
    if request_data.formato == "240":
        conteudo = await service.gerar_cnab240_remessa(
            request_data.configuracao_id,
            boletos,
            request_data.numero_remessa
        )
    else:  # 400
        conteudo = await service.gerar_cnab400_remessa(
            request_data.configuracao_id,
            boletos,
            request_data.numero_remessa
        )

    # Converter para base64
    arquivo_base64 = base64.b64encode(conteudo.encode()).decode()

    # Nome do arquivo
    data_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo = f"remessa_cnab{request_data.formato}_{data_str}.txt"

    return schemas.CNABRemessaResponse(
        sucesso=True,
        formato=request_data.formato,
        total_boletos=len(boletos),
        arquivo_base64=arquivo_base64,
        nome_arquivo=nome_arquivo
    )


@router.post("/cnab/retorno", response_model=schemas.CNABRetornoResponse)
async def processar_arquivo_cnab_retorno(
    request_data: schemas.CNABRetornoRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Processa arquivo CNAB de retorno (resposta do banco)

    Atualiza status dos boletos com base nas ocorrências do arquivo.
    """
    from app.modules.pagamentos.services.cnab_service import CNABService

    service = CNABService(db)

    # Processar arquivo CNAB
    if request_data.formato == "240":
        resultado = await service.processar_cnab240_retorno(
            request_data.configuracao_id,
            request_data.conteudo_arquivo
        )
    else:  # 400
        resultado = await service.processar_cnab400_retorno(
            request_data.configuracao_id,
            request_data.conteudo_arquivo
        )

    return schemas.CNABRetornoResponse(
        sucesso=True,
        formato=request_data.formato,
        total_registros=resultado["total_registros"],
        boletos_atualizados=resultado["boletos_atualizados"],
        boletos_pagos=resultado["boletos_pagos"],
        erros=resultado.get("erros", [])
    )
