"""
Router para Documentos Auxiliares
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.documentos_auxiliares.service import DocumentoAuxiliarService
from app.modules.documentos_auxiliares.models import TipoDocumento
from app.modules.documentos_auxiliares.schemas import (
    GerarDocumentoRequest,
    DocumentoAuxiliarResponse,
    DocumentoGeradoResponse,
)

router = APIRouter()


@router.post(
    "/gerar",
    response_model=DocumentoGeradoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar documento auxiliar",
    description="Gera documento auxiliar não fiscal em PDF",
)
async def gerar_documento(
    request: GerarDocumentoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera documento auxiliar não fiscal em PDF.

    **Tipos de documentos:**
    - PEDIDO_VENDA - Pedido de venda impresso
    - ORCAMENTO - Orçamento impresso
    - NOTA_ENTREGA - Nota de entrega (acompanha mercadoria)
    - ROMANEIO - Lista de produtos para separação
    - COMPROVANTE_ENTREGA - Comprovante de recebimento
    - RECIBO - Recibo simples
    - PEDIDO_COMPRA - Pedido de compra

    **Exemplo de requisição:**
    ```json
    {
        "tipo_documento": "PEDIDO_VENDA",
        "referencia_tipo": "pedido_venda",
        "referencia_id": 1,
        "opcoes": {
            "incluir_observacoes": true
        }
    }
    ```

    **Resposta:**
    ```json
    {
        "documento_id": 1,
        "tipo_documento": "PEDIDO_VENDA",
        "numero_documento": "PV000001",
        "arquivo_pdf": "/storage/documentos/pedido_venda_PV000001_20251123.pdf",
        "url_download": "/api/v1/documentos-auxiliares/1/download",
        "mensagem": "Documento gerado com sucesso"
    }
    ```
    """
    service = DocumentoAuxiliarService(db)
    return await service.gerar_documento(request, current_user.id)


@router.get(
    "/{documento_id}",
    response_model=DocumentoAuxiliarResponse,
    summary="Obter documento",
    description="Retorna informações de um documento auxiliar",
)
async def get_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna informações de um documento auxiliar gerado.

    **Parâmetros:**
    - **documento_id**: ID do documento

    **Resposta:**
    - Metadados do documento (tipo, data, cliente, arquivo)
    """
    service = DocumentoAuxiliarService(db)
    documento = await service.get_documento(documento_id)
    return DocumentoAuxiliarResponse.model_validate(documento)


@router.get(
    "/{documento_id}/download",
    response_class=FileResponse,
    summary="Download do PDF",
    description="Faz download do arquivo PDF do documento",
)
async def download_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Faz download do arquivo PDF do documento.

    **Parâmetros:**
    - **documento_id**: ID do documento

    **Resposta:**
    - Arquivo PDF para download
    """
    service = DocumentoAuxiliarService(db)
    documento = await service.get_documento(documento_id)

    # Retornar arquivo
    return FileResponse(
        path=documento.arquivo_pdf,
        media_type="application/pdf",
        filename=f"{documento.tipo_documento.value}_{documento.numero_documento}.pdf",
    )


@router.get(
    "/{documento_id}/visualizar",
    response_class=Response,
    summary="Visualizar HTML",
    description="Visualiza o HTML do documento no navegador",
)
async def visualizar_documento(
    documento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Visualiza o HTML do documento no navegador.

    Útil para pré-visualização antes de gerar PDF.

    **Parâmetros:**
    - **documento_id**: ID do documento

    **Resposta:**
    - HTML renderizado
    """
    service = DocumentoAuxiliarService(db)
    documento = await service.get_documento(documento_id)

    return Response(content=documento.conteudo_html, media_type="text/html")


@router.get(
    "/",
    response_model=List[DocumentoAuxiliarResponse],
    summary="Listar documentos",
    description="Lista documentos auxiliares com filtros",
)
async def listar_documentos(
    skip: int = Query(0, ge=0, description="Offset para paginação"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    tipo_documento: Optional[TipoDocumento] = Query(
        None, description="Filtrar por tipo"
    ),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista documentos auxiliares gerados.

    **Parâmetros:**
    - **skip**: Offset para paginação (padrão: 0)
    - **limit**: Limite de resultados (padrão: 100, máximo: 1000)
    - **tipo_documento**: Filtrar por tipo de documento
    - **cliente_id**: Filtrar por cliente

    **Resposta:**
    - Lista de documentos gerados
    """
    service = DocumentoAuxiliarService(db)
    documentos = await service.listar_documentos(
        skip=skip, limit=limit, tipo_documento=tipo_documento, cliente_id=cliente_id
    )

    return [DocumentoAuxiliarResponse.model_validate(d) for d in documentos]


@router.post(
    "/pedido-venda/{pedido_id}",
    response_model=DocumentoGeradoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar PDF de Pedido de Venda",
    description="Atalho para gerar PDF de um pedido de venda",
)
async def gerar_pdf_pedido_venda(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atalho para gerar PDF de um pedido de venda.

    Equivalente a chamar /gerar com tipo_documento=PEDIDO_VENDA.

    **Parâmetros:**
    - **pedido_id**: ID do pedido de venda

    **Resposta:**
    - Informações do documento gerado
    """
    service = DocumentoAuxiliarService(db)
    request = GerarDocumentoRequest(
        tipo_documento="PEDIDO_VENDA",
        referencia_tipo="pedido_venda",
        referencia_id=pedido_id,
    )
    return await service.gerar_documento(request, current_user.id)


@router.post(
    "/orcamento/{orcamento_id}",
    response_model=DocumentoGeradoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar PDF de Orçamento",
    description="Atalho para gerar PDF de um orçamento",
)
async def gerar_pdf_orcamento(
    orcamento_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atalho para gerar PDF de um orçamento.

    **Parâmetros:**
    - **orcamento_id**: ID do orçamento

    **Resposta:**
    - Informações do documento gerado
    """
    service = DocumentoAuxiliarService(db)
    request = GerarDocumentoRequest(
        tipo_documento="ORCAMENTO",
        referencia_tipo="orcamento",
        referencia_id=orcamento_id,
    )
    return await service.gerar_documento(request, current_user.id)


@router.post(
    "/nota-entrega/{pedido_id}",
    response_model=DocumentoGeradoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gerar Nota de Entrega",
    description="Gera nota de entrega para um pedido",
)
async def gerar_nota_entrega(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera nota de entrega para um pedido.

    **Parâmetros:**
    - **pedido_id**: ID do pedido de venda

    **Resposta:**
    - Informações do documento gerado
    """
    service = DocumentoAuxiliarService(db)
    request = GerarDocumentoRequest(
        tipo_documento="NOTA_ENTREGA",
        referencia_tipo="pedido_venda",
        referencia_id=pedido_id,
    )
    return await service.gerar_documento(request, current_user.id)
