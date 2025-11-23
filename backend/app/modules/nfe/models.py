"""
Modelos de Notas Fiscais Eletrônicas
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Text, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TipoNota(str, PyEnum):
    """Tipos de Nota Fiscal"""

    NFE = "NFE"
    NFCE = "NFCE"
    NFSE = "NFSE"


class StatusNota(str, PyEnum):
    """Status da Nota Fiscal"""

    PENDENTE = "PENDENTE"
    AUTORIZADA = "AUTORIZADA"
    CANCELADA = "CANCELADA"
    REJEITADA = "REJEITADA"


class NotaFiscal(Base):
    """Modelo de Nota Fiscal Eletrônica"""

    __tablename__ = "notas_fiscais"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[TipoNota] = mapped_column(
        Enum(TipoNota), nullable=False, default=TipoNota.NFE, index=True
    )
    numero: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    serie: Mapped[str] = mapped_column(String(10), nullable=False, default="1")
    chave_acesso: Mapped[str] = mapped_column(
        String(44), unique=True, nullable=False, index=True
    )
    data_emissao: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relacionamentos (IDs opcionais)
    fornecedor_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True, index=True
    )
    cliente_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    venda_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendas.id"), nullable=True, index=True
    )

    # Valores
    valor_produtos: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_icms: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_ipi: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )

    # Status e controle
    status: Mapped[StatusNota] = mapped_column(
        Enum(StatusNota), nullable=False, default=StatusNota.PENDENTE, index=True
    )
    xml_nfe: Mapped[str | None] = mapped_column(Text, nullable=True)
    protocolo_autorizacao: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    data_autorizacao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Índices compostos para otimização
    __table_args__ = (
        Index("idx_nfe_tipo_status", "tipo", "status"),
        Index("idx_nfe_data_emissao", "data_emissao"),
        Index("idx_nfe_fornecedor", "fornecedor_id"),
        Index("idx_nfe_venda", "venda_id"),
    )

    def __repr__(self) -> str:
        return f"<NotaFiscal(id={self.id}, tipo={self.tipo}, numero={self.numero}, chave={self.chave_acesso})>"
