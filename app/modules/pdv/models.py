"""
Modelos de PDV (Ponto de Venda)
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Index, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StatusCaixa(str, PyEnum):
    """Status de um caixa"""
    ABERTO = "ABERTO"
    FECHADO = "FECHADO"


class TipoMovimentacaoCaixa(str, PyEnum):
    """Tipo de movimentação de caixa"""
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    SANGRIA = "SANGRIA"
    SUPRIMENTO = "SUPRIMENTO"


class Caixa(Base):
    """Modelo de Caixa"""

    __tablename__ = "caixas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    operador_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    data_abertura: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    valor_abertura: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    data_fechamento: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    valor_fechamento: Mapped[float | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    status: Mapped[StatusCaixa] = mapped_column(
        Enum(StatusCaixa), nullable=False, default=StatusCaixa.ABERTO, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    movimentacoes: Mapped[list["MovimentacaoCaixa"]] = relationship(
        "MovimentacaoCaixa", back_populates="caixa", lazy="selectin", cascade="all, delete-orphan"
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_caixa_operador_status", "operador_id", "status"),
        Index("idx_caixa_data_abertura", "data_abertura"),
    )

    def __repr__(self) -> str:
        return f"<Caixa(id={self.id}, operador_id={self.operador_id}, status='{self.status}')>"


class MovimentacaoCaixa(Base):
    """Modelo de Movimentação de Caixa"""

    __tablename__ = "movimentacoes_caixa"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    caixa_id: Mapped[int] = mapped_column(
        ForeignKey("caixas.id"), nullable=False, index=True
    )
    venda_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendas.id"), nullable=True, index=True
    )
    tipo: Mapped[TipoMovimentacaoCaixa] = mapped_column(
        Enum(TipoMovimentacaoCaixa), nullable=False, index=True
    )
    valor: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    descricao: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    caixa: Mapped["Caixa"] = relationship(
        "Caixa", back_populates="movimentacoes", lazy="selectin"
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_movimentacao_caixa_tipo", "caixa_id", "tipo"),
        Index("idx_movimentacao_venda", "venda_id"),
    )

    def __repr__(self) -> str:
        return f"<MovimentacaoCaixa(id={self.id}, caixa_id={self.caixa_id}, tipo='{self.tipo}', valor={self.valor})>"
