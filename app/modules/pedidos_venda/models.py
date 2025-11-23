"""
Modelos de Pedidos de Venda
"""
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Date, Numeric, Integer, ForeignKey, Index, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StatusPedidoVenda(str, PyEnum):
    """Status de um pedido de venda"""
    RASCUNHO = "RASCUNHO"
    CONFIRMADO = "CONFIRMADO"
    EM_SEPARACAO = "EM_SEPARACAO"
    SEPARADO = "SEPARADO"
    EM_ENTREGA = "EM_ENTREGA"
    ENTREGUE = "ENTREGUE"
    FATURADO = "FATURADO"
    CANCELADO = "CANCELADO"


class TipoEntrega(str, PyEnum):
    """Tipo de entrega do pedido"""
    RETIRADA = "RETIRADA"
    ENTREGA = "ENTREGA"
    TRANSPORTADORA = "TRANSPORTADORA"


class PedidoVenda(Base):
    """Modelo de Pedido de Venda"""

    __tablename__ = "pedidos_venda"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero_pedido: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    orcamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("orcamentos.id"), nullable=True, index=True
    )
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"), nullable=False, index=True
    )
    vendedor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    data_pedido: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    data_entrega_prevista: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    data_entrega_real: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    tipo_entrega: Mapped[TipoEntrega] = mapped_column(
        Enum(TipoEntrega), nullable=False, default=TipoEntrega.RETIRADA
    )
    endereco_entrega: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Valores
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    desconto: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_frete: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    outras_despesas: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )

    # Pagamento
    condicao_pagamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("condicoes_pagamento.id"), nullable=True
    )
    forma_pagamento: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    # Status e observações
    status: Mapped[StatusPedidoVenda] = mapped_column(
        Enum(StatusPedidoVenda), nullable=False, default=StatusPedidoVenda.RASCUNHO, index=True
    )
    observacoes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    observacoes_internas: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Controle
    venda_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendas.id"), nullable=True, index=True
    )
    usuario_separacao_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    data_separacao: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    itens: Mapped[list["ItemPedidoVenda"]] = relationship(
        "ItemPedidoVenda", back_populates="pedido", lazy="selectin", cascade="all, delete-orphan"
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_pedido_venda_numero", "numero_pedido"),
        Index("idx_pedido_venda_cliente_data", "cliente_id", "data_pedido"),
        Index("idx_pedido_venda_vendedor_data", "vendedor_id", "data_pedido"),
        Index("idx_pedido_venda_status_data", "status", "data_pedido"),
        Index("idx_pedido_venda_entrega", "data_entrega_prevista", "status"),
    )

    def __repr__(self) -> str:
        return f"<PedidoVenda(id={self.id}, numero='{self.numero_pedido}', status='{self.status}', valor_total={self.valor_total})>"


class ItemPedidoVenda(Base):
    """Modelo de Item de Pedido de Venda"""

    __tablename__ = "itens_pedido_venda"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos_venda.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    quantidade: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    quantidade_separada: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
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
        Text, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    pedido: Mapped["PedidoVenda"] = relationship(
        "PedidoVenda", back_populates="itens", lazy="selectin"
    )
    produto: Mapped["Produto"] = relationship(
        "Produto", lazy="selectin"
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_item_pedido_venda_produto", "pedido_id", "produto_id"),
    )

    def __repr__(self) -> str:
        return f"<ItemPedidoVenda(id={self.id}, pedido_id={self.pedido_id}, produto_id={self.produto_id}, quantidade={self.quantidade})>"
