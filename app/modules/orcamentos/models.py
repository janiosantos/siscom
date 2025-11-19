"""
Modelos de Orçamentos
"""
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Index, Enum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StatusOrcamento(str, PyEnum):
    """Status de um orçamento"""
    ABERTO = "ABERTO"
    APROVADO = "APROVADO"
    PERDIDO = "PERDIDO"
    CONVERTIDO = "CONVERTIDO"


class Orcamento(Base):
    """Modelo de Orçamento"""

    __tablename__ = "orcamentos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("clientes.id"), nullable=True, index=True
    )
    vendedor_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    data_orcamento: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    validade_dias: Mapped[int] = mapped_column(
        Integer, nullable=False, default=15
    )
    data_validade: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    desconto: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    status: Mapped[StatusOrcamento] = mapped_column(
        Enum(StatusOrcamento), nullable=False, default=StatusOrcamento.ABERTO, index=True
    )
    observacoes: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    itens: Mapped[list["ItemOrcamento"]] = relationship(
        "ItemOrcamento", back_populates="orcamento", lazy="selectin", cascade="all, delete-orphan"
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_orcamento_data_status", "data_orcamento", "status"),
        Index("idx_orcamento_cliente", "cliente_id", "data_orcamento"),
        Index("idx_orcamento_vendedor", "vendedor_id", "data_orcamento"),
        Index("idx_orcamento_validade", "data_validade", "status"),
    )

    def __repr__(self) -> str:
        return f"<Orcamento(id={self.id}, valor_total={self.valor_total}, status='{self.status}')>"


class ItemOrcamento(Base):
    """Modelo de Item de Orçamento"""

    __tablename__ = "itens_orcamento"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    orcamento_id: Mapped[int] = mapped_column(
        ForeignKey("orcamentos.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    quantidade: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    preco_unitario: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    desconto_item: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    total_item: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    observacao_item: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    orcamento: Mapped["Orcamento"] = relationship(
        "Orcamento", back_populates="itens", lazy="selectin"
    )
    produto: Mapped["Produto"] = relationship(
        "Produto", lazy="selectin"
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_item_orcamento_produto", "orcamento_id", "produto_id"),
    )

    def __repr__(self) -> str:
        return f"<ItemOrcamento(id={self.id}, orcamento_id={self.orcamento_id}, produto_id={self.produto_id}, quantidade={self.quantidade})>"
