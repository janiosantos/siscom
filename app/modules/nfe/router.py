"""
Router para API de Notas Fiscais
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.modules.nfe.service import NotaFiscalService
from app.modules.nfe.schemas import (
    NotaFiscalResponse,
    NotaFiscalList,
    ImportarXMLCreate,
    EmitirNFCeCreate,
    CancelarNotaRequest,
    ConsultarNotaResponse,
    TipoNotaEnum,
    StatusNotaEnum,
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)

router = APIRouter(prefix="/api/nfe", tags=["Notas Fiscais"])


@router.post("/importar-xml", response_model=NotaFiscalResponse, status_code=201)
async def importar_xml_nfe(
    file: UploadFile = File(..., description="Arquivo XML da NF-e"),
    registrar_entrada_estoque: bool = Query(
        True, description="Se deve registrar entrada de estoque"
    ),
    criar_conta_pagar: bool = Query(True, description="Se deve criar conta a pagar"),
    session: AsyncSession = Depends(get_session),
):
    """
    Importa XML de NF-e e processa:
    - Cria/atualiza produtos
    - Registra entrada de estoque
    - Cria conta a pagar (se módulo disponível)

    Args:
        file: Arquivo XML da NF-e
        registrar_entrada_estoque: Se deve registrar entrada no estoque
        criar_conta_pagar: Se deve criar conta a pagar
        session: Sessão do banco de dados

    Returns:
        NotaFiscalResponse com a nota criada

    Raises:
        HTTPException 400: Se XML inválido ou nota duplicada
        HTTPException 500: Se erro ao processar
    """
    # Valida tipo de arquivo
    if not file.filename.endswith(".xml"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo deve ser um XML (.xml)",
        )

    # Lê conteúdo do arquivo
    try:
        xml_content = await file.read()
        xml_str = xml_content.decode("utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao ler arquivo XML: {str(e)}",
        )

    # Processa importação
    service = NotaFiscalService(session)
    try:
        importar_data = ImportarXMLCreate(
            xml_content=xml_str,
            registrar_entrada_estoque=registrar_entrada_estoque,
            criar_conta_pagar=criar_conta_pagar,
        )
        nota = await service.importar_xml_nfe(importar_data)
        await session.commit()
        return nota

    except ValidationException as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao importar XML: {str(e)}",
        )


@router.post("/emitir-nfce", response_model=NotaFiscalResponse, status_code=201)
async def emitir_nfce(
    emissao_data: EmitirNFCeCreate,
    session: AsyncSession = Depends(get_session),
):
    """
    Emite NFC-e para uma venda (simulado)

    Esta é uma implementação simulada que apenas cria o registro da nota.
    Em produção, integraria com a SEFAZ para emissão real.

    Args:
        emissao_data: Dados para emissão da NFC-e
        session: Sessão do banco de dados

    Returns:
        NotaFiscalResponse com a nota criada

    Raises:
        HTTPException 404: Se venda não encontrada
        HTTPException 400: Se venda já possui NFC-e
    """
    service = NotaFiscalService(session)
    try:
        nota = await service.emitir_nfce(emissao_data)
        await session.commit()
        return nota

    except NotFoundException as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao emitir NFC-e: {str(e)}",
        )


@router.get("/{id}", response_model=ConsultarNotaResponse)
async def consultar_nota(
    id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Consulta nota fiscal por ID

    Args:
        id: ID da nota fiscal
        session: Sessão do banco de dados

    Returns:
        ConsultarNotaResponse com dados completos da nota

    Raises:
        HTTPException 404: Se nota não encontrada
    """
    service = NotaFiscalService(session)
    try:
        nota = await service.consultar_nota(id)
        return nota

    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar nota: {str(e)}",
        )


@router.get("/chave/{chave}", response_model=ConsultarNotaResponse)
async def consultar_por_chave(
    chave: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Consulta nota fiscal por chave de acesso

    Args:
        chave: Chave de acesso da nota (44 dígitos)
        session: Sessão do banco de dados

    Returns:
        ConsultarNotaResponse com dados completos da nota

    Raises:
        HTTPException 404: Se nota não encontrada
        HTTPException 400: Se chave inválida
    """
    service = NotaFiscalService(session)
    try:
        nota = await service.consultar_por_chave(chave)
        return nota

    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar nota: {str(e)}",
        )


@router.get("/", response_model=NotaFiscalList)
async def listar_notas(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Tamanho da página"),
    tipo: Optional[TipoNotaEnum] = Query(None, description="Filtrar por tipo"),
    status: Optional[StatusNotaEnum] = Query(None, description="Filtrar por status"),
    fornecedor_id: Optional[int] = Query(None, description="Filtrar por fornecedor"),
    venda_id: Optional[int] = Query(None, description="Filtrar por venda"),
    data_inicio: Optional[datetime] = Query(None, description="Data inicial"),
    data_fim: Optional[datetime] = Query(None, description="Data final"),
    session: AsyncSession = Depends(get_session),
):
    """
    Lista notas fiscais com paginação e filtros

    Args:
        page: Número da página (inicia em 1)
        page_size: Quantidade de itens por página
        tipo: Filtrar por tipo de nota
        status: Filtrar por status
        fornecedor_id: Filtrar por fornecedor
        venda_id: Filtrar por venda
        data_inicio: Data inicial do período
        data_fim: Data final do período
        session: Sessão do banco de dados

    Returns:
        NotaFiscalList com lista paginada de notas
    """
    service = NotaFiscalService(session)
    try:
        if data_inicio or data_fim:
            # Se filtrar por data, usa método específico
            inicio = data_inicio or datetime(2000, 1, 1)
            fim = data_fim or datetime.now()
            notas = await service.get_notas_periodo(
                data_inicio=inicio,
                data_fim=fim,
                page=page,
                page_size=page_size,
                tipo=tipo,
                status=status,
            )
        else:
            # Senão, lista geral
            notas = await service.listar_notas(
                page=page,
                page_size=page_size,
                tipo=tipo,
                status=status,
                fornecedor_id=fornecedor_id,
                venda_id=venda_id,
            )

        return notas

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar notas: {str(e)}",
        )


@router.post("/{id}/cancelar", response_model=NotaFiscalResponse)
async def cancelar_nota(
    id: int,
    cancelamento: CancelarNotaRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Cancela uma nota fiscal

    Args:
        id: ID da nota fiscal
        cancelamento: Dados do cancelamento (motivo)
        session: Sessão do banco de dados

    Returns:
        NotaFiscalResponse com nota cancelada

    Raises:
        HTTPException 404: Se nota não encontrada
        HTTPException 400: Se nota não pode ser cancelada
    """
    service = NotaFiscalService(session)
    try:
        nota = await service.cancelar_nota(id, cancelamento.motivo)
        await session.commit()
        return nota

    except NotFoundException as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except BusinessRuleException as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao cancelar nota: {str(e)}",
        )
