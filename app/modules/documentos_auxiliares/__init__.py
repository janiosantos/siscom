"""
Módulo de Documentos Auxiliares

Gera documentos não fiscais em PDF:
- Pedidos de Venda
- Orçamentos
- Notas de Entrega
- Romaneios
- Comprovantes de Entrega
- Recibos
"""

from app.modules.documentos_auxiliares.models import DocumentoAuxiliar, TipoDocumento
from app.modules.documentos_auxiliares.schemas import (
    GerarDocumentoRequest,
    DocumentoAuxiliarResponse,
    DocumentoGeradoResponse,
)
from app.modules.documentos_auxiliares.service import DocumentoAuxiliarService
from app.modules.documentos_auxiliares.router import router

__all__ = [
    "DocumentoAuxiliar",
    "TipoDocumento",
    "GerarDocumentoRequest",
    "DocumentoAuxiliarResponse",
    "DocumentoGeradoResponse",
    "DocumentoAuxiliarService",
    "router",
]
