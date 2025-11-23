"""
Schemas para Documentos Auxiliares
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any, Dict
from enum import Enum


class TipoDocumentoEnum(str, Enum):
    """Enum de tipos de documentos"""
    PEDIDO_VENDA = "PEDIDO_VENDA"
    ORCAMENTO = "ORCAMENTO"
    NOTA_ENTREGA = "NOTA_ENTREGA"
    ROMANEIO = "ROMANEIO"
    COMPROVANTE_ENTREGA = "COMPROVANTE_ENTREGA"
    RECIBO = "RECIBO"
    PEDIDO_COMPRA = "PEDIDO_COMPRA"


class GerarDocumentoRequest(BaseModel):
    """Request para gerar documento"""
    tipo_documento: TipoDocumentoEnum
    referencia_tipo: str = Field(..., description="Tipo da referência (pedido_venda, orcamento, venda)")
    referencia_id: int = Field(..., gt=0, description="ID do documento de origem")
    opcoes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Opções adicionais (ex: incluir_observacoes, layout, etc)"
    )


class DocumentoAuxiliarResponse(BaseModel):
    """Response de documento auxiliar"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_documento: TipoDocumentoEnum
    referencia_tipo: str
    referencia_id: int
    numero_documento: str
    cliente_id: Optional[int]
    arquivo_pdf: Optional[str]
    gerado_por_id: Optional[int]
    created_at: datetime


class DocumentoGeradoResponse(BaseModel):
    """Response após gerar documento"""
    documento_id: int
    tipo_documento: TipoDocumentoEnum
    numero_documento: str
    arquivo_pdf: str
    url_download: str
    mensagem: str = "Documento gerado com sucesso"


class ListarDocumentosResponse(BaseModel):
    """Response para listagem de documentos"""
    items: list[DocumentoAuxiliarResponse]
    total: int
    page: int
    page_size: int
    pages: int
