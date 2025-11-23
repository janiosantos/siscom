"""
Modelos para Documentos Auxiliares
"""
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from datetime import datetime
from typing import Optional

from app.core.database import Base


class TipoDocumento(str, Enum):
    """Tipos de documentos auxiliares"""
    PEDIDO_VENDA = "PEDIDO_VENDA"
    ORCAMENTO = "ORCAMENTO"
    NOTA_ENTREGA = "NOTA_ENTREGA"
    ROMANEIO = "ROMANEIO"
    COMPROVANTE_ENTREGA = "COMPROVANTE_ENTREGA"
    RECIBO = "RECIBO"
    PEDIDO_COMPRA = "PEDIDO_COMPRA"


class DocumentoAuxiliar(Base):
    """Modelo para documentos auxiliares (PDFs, recibos, etc)"""
    __tablename__ = "documentos_auxiliares"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tipo_documento: Mapped[str] = mapped_column(String(50), nullable=False)
    referencia_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    referencia_id: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(50), nullable=False)

    cliente_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    gerado_por_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    arquivo_pdf: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    conteudo_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadados: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
