"""
Modelos de Estoque
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Index, Enum
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
