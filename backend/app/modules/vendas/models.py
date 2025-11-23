"""
Modelos de Vendas
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StatusVenda(str, PyEnum):
    """Status de uma venda"""
    PENDENTE = "PENDENTE"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"


class Venda(Base):
    """Modelo de Venda"""

    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("clientes.id"), nullable=True, index=True
    )
    vendedor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    data_venda: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
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
    forma_pagamento: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    status: Mapped[StatusVenda] = mapped_column(
        Enum(StatusVenda), nullable=False, default=StatusVenda.PENDENTE, index=True
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
    itens: Mapped[list["ItemVenda"]] = relationship(
        "ItemVenda", back_populates="venda", lazy="selectin", cascade="all, delete-orphan"
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_venda_data_status", "data_venda", "status"),
        Index("idx_venda_cliente", "cliente_id", "data_venda"),
        Index("idx_venda_vendedor", "vendedor_id", "data_venda"),
    )

    def __repr__(self) -> str:
        return f"<Venda(id={self.id}, valor_total={self.valor_total}, status='{self.status}')>"


class ItemVenda(Base):
    """Modelo de Item de Venda"""

    __tablename__ = "itens_venda"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    venda_id: Mapped[int] = mapped_column(
        ForeignKey("vendas.id"), nullable=False, index=True
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
    subtotal_item: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    desconto_item: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    total_item: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    venda: Mapped["Venda"] = relationship(
        "Venda", back_populates="itens", lazy="selectin"
    )
    produto: Mapped["Produto"] = relationship(
        "Produto", lazy="selectin"
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_item_venda_produto", "venda_id", "produto_id"),
    )

    def __repr__(self) -> str:
        return f"<ItemVenda(id={self.id}, venda_id={self.venda_id}, produto_id={self.produto_id}, quantidade={self.quantidade})>"
