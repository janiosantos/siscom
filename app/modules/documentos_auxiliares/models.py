"""
Models para Documentos Auxiliares

Armazena histórico de documentos não fiscais gerados
"""
from enum import Enum as PyEnum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TipoDocumento(str, PyEnum):
    """Tipos de documentos auxiliares"""
    PEDIDO_VENDA = "PEDIDO_VENDA"
    ORCAMENTO = "ORCAMENTO"
    NOTA_ENTREGA = "NOTA_ENTREGA"
    ROMANEIO = "ROMANEIO"
    COMPROVANTE_ENTREGA = "COMPROVANTE_ENTREGA"
    RECIBO = "RECIBO"
    PEDIDO_COMPRA = "PEDIDO_COMPRA"


class DocumentoAuxiliar(Base):
    """
    Histórico de documentos auxiliares gerados

    Armazena informações sobre documentos não fiscais gerados
    para auditoria e re-impressão
    """
    __tablename__ = "documentos_auxiliares"

    # Chave primária
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Tipo de documento
    tipo_documento: Mapped[TipoDocumento] = mapped_column(
        Enum(TipoDocumento),
        nullable=False,
        index=True
    )

    # Referência ao documento origem
    # (pode ser pedido_venda_id, orcamento_id, venda_id, etc)
    referencia_tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Tipo da referência (pedido_venda, orcamento, venda, etc)"
    )
    referencia_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="ID do documento de origem"
    )

    # Número do documento (para exibição)
    numero_documento: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # Cliente relacionado (denormalizado para facilitar queries)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"),
        nullable=True,
        index=True
    )

    # Caminho do arquivo PDF gerado
    arquivo_pdf: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment="Caminho do arquivo PDF no sistema de arquivos"
    )

    # Conteúdo HTML usado para gerar o PDF (para re-geração)
    conteudo_html: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="HTML usado para gerar o PDF"
    )

    # Metadados do documento (JSON)
    metadados: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Metadados adicionais em JSON"
    )

    # Usuário que gerou
    gerado_por_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship(back_populates="documentos_auxiliares")
    gerado_por: Mapped["User"] = relationship()

    def __repr__(self):
        return f"<DocumentoAuxiliar {self.tipo_documento} #{self.numero_documento}>"
