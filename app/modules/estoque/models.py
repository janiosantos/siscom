"""
Modelos de Estoque
"""
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Date, Numeric, Integer, ForeignKey, Index, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TipoMovimentacao(str, PyEnum):
    """Enum para tipos de movimentação de estoque"""

    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    AJUSTE = "AJUSTE"
    TRANSFERENCIA = "TRANSFERENCIA"
    DEVOLUCAO = "DEVOLUCAO"


class MovimentacaoEstoque(Base):
    """Modelo de Movimentação de Estoque"""

    __tablename__ = "movimentacoes_estoque"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    tipo: Mapped[TipoMovimentacao] = mapped_column(
        Enum(TipoMovimentacao), nullable=False, index=True
    )
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    custo_unitario: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    documento_referencia: Mapped[str] = mapped_column(
        String(100), nullable=True, index=True
    )
    observacao: Mapped[str] = mapped_column(String(500), nullable=True)
    usuario_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relacionamentos
    produto: Mapped["Produto"] = relationship("Produto", lazy="selectin")

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_movimentacao_produto_tipo", "produto_id", "tipo"),
        Index("idx_movimentacao_produto_data", "produto_id", "created_at"),
        Index("idx_movimentacao_data_tipo", "created_at", "tipo"),
    )

    def __repr__(self) -> str:
        return f"<MovimentacaoEstoque(id={self.id}, produto_id={self.produto_id}, tipo='{self.tipo}', quantidade={self.quantidade})>"


class LoteEstoque(Base):
    """Modelo de Lote de Estoque para controle FIFO"""

    __tablename__ = "lotes_estoque"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    numero_lote: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    data_fabricacao: Mapped[date] = mapped_column(Date, nullable=True)
    data_validade: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantidade_inicial: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    quantidade_atual: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, index=True
    )
    custo_unitario: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    documento_referencia: Mapped[str] = mapped_column(
        String(100), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relacionamentos
    produto: Mapped["Produto"] = relationship("Produto", lazy="selectin")

    # Índices compostos para otimização de consultas FIFO
    __table_args__ = (
        Index("idx_lote_produto_validade", "produto_id", "data_validade"),
        Index("idx_lote_produto_disponivel", "produto_id", "quantidade_atual"),
        Index("idx_lote_numero", "numero_lote"),
    )

    def __repr__(self) -> str:
        return f"<LoteEstoque(id={self.id}, numero_lote='{self.numero_lote}', produto_id={self.produto_id}, quantidade_atual={self.quantidade_atual})>"
