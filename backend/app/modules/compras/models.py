"""
Modelos de Compras
"""
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Date, Numeric, Integer, ForeignKey, Index, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StatusPedidoCompra(str, PyEnum):
    """Enum para status de pedido de compra"""

    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    RECEBIDO_PARCIAL = "RECEBIDO_PARCIAL"
    RECEBIDO = "RECEBIDO"
    CANCELADO = "CANCELADO"


class PedidoCompra(Base):
    """Modelo de Pedido de Compra"""

    __tablename__ = "pedidos_compra"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id"), nullable=False, index=True
    )
    data_pedido: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    data_entrega_prevista: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    data_entrega_real: Mapped[date] = mapped_column(
        Date, nullable=True
    )
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    desconto: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_frete: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    status: Mapped[StatusPedidoCompra] = mapped_column(
        Enum(StatusPedidoCompra), nullable=False, default=StatusPedidoCompra.PENDENTE, index=True
    )
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    fornecedor: Mapped["Fornecedor"] = relationship("Fornecedor", lazy="selectin")
    itens: Mapped[list["ItemPedidoCompra"]] = relationship(
        "ItemPedidoCompra", back_populates="pedido", lazy="selectin", cascade="all, delete-orphan"
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_pedido_compra_fornecedor_status", "fornecedor_id", "status"),
        Index("idx_pedido_compra_data_pedido", "data_pedido"),
        Index("idx_pedido_compra_data_entrega", "data_entrega_prevista"),
        Index("idx_pedido_compra_status_data", "status", "data_entrega_prevista"),
    )

    def __repr__(self) -> str:
        return f"<PedidoCompra(id={self.id}, fornecedor_id={self.fornecedor_id}, status='{self.status}', valor_total={self.valor_total})>"


class ItemPedidoCompra(Base):
    """Modelo de Item de Pedido de Compra"""

    __tablename__ = "itens_pedido_compra"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos_compra.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    quantidade_solicitada: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    quantidade_recebida: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    preco_unitario: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    subtotal_item: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    observacao: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    pedido: Mapped["PedidoCompra"] = relationship("PedidoCompra", back_populates="itens")
    produto: Mapped["Produto"] = relationship("Produto", lazy="selectin")

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_item_pedido_compra_pedido", "pedido_id"),
        Index("idx_item_pedido_compra_produto", "produto_id"),
    )

    def __repr__(self) -> str:
        return f"<ItemPedidoCompra(id={self.id}, pedido_id={self.pedido_id}, produto_id={self.produto_id}, quantidade_solicitada={self.quantidade_solicitada})>"
