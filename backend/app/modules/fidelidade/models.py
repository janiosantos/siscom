"""
Modelos para Programa de Fidelidade
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Boolean, Integer, Numeric, Text, Enum, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TipoMovimentacaoPontos(str, PyEnum):
    """Enum para tipo de movimentação de pontos"""

    ACUMULO = "ACUMULO"
    RESGATE = "RESGATE"
    EXPIRACAO = "EXPIRACAO"
    AJUSTE = "AJUSTE"
    CANCELAMENTO = "CANCELAMENTO"


class ProgramaFidelidade(Base):
    """Modelo de Programa de Fidelidade"""

    __tablename__ = "programas_fidelidade"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    pontos_por_real: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=1.0,
        comment="Quantos pontos o cliente ganha por R$ 1,00 gasto"
    )
    valor_ponto_resgate: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.01,
        comment="Valor em R$ de cada ponto no resgate"
    )
    pontos_minimo_resgate: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100,
        comment="Mínimo de pontos para resgate"
    )
    dias_validade_pontos: Mapped[int] = mapped_column(
        Integer, nullable=True,
        comment="Dias de validade dos pontos (NULL = sem expiração)"
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<ProgramaFidelidade(id={self.id}, nome='{self.nome}')>"


class SaldoPontos(Base):
    """Modelo de Saldo de Pontos por Cliente"""

    __tablename__ = "saldos_pontos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"), nullable=False, unique=True, index=True
    )
    programa_id: Mapped[int] = mapped_column(
        ForeignKey("programas_fidelidade.id"), nullable=False, index=True
    )
    pontos_disponiveis: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Saldo atual de pontos disponíveis"
    )
    pontos_acumulados_total: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Total de pontos acumulados historicamente"
    )
    pontos_resgatados_total: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Total de pontos resgatados historicamente"
    )
    ultima_movimentacao: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    programa: Mapped["ProgramaFidelidade"] = relationship(
        "ProgramaFidelidade", lazy="selectin"
    )

    # Índices
    __table_args__ = (
        Index("idx_saldo_cliente_programa", "cliente_id", "programa_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<SaldoPontos(cliente_id={self.cliente_id}, pontos={self.pontos_disponiveis})>"


class MovimentacaoPontos(Base):
    """Modelo de Movimentação de Pontos (Histórico)"""

    __tablename__ = "movimentacoes_pontos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"), nullable=False, index=True
    )
    programa_id: Mapped[int] = mapped_column(
        ForeignKey("programas_fidelidade.id"), nullable=False, index=True
    )
    tipo: Mapped[TipoMovimentacaoPontos] = mapped_column(
        Enum(TipoMovimentacaoPontos), nullable=False, index=True
    )
    pontos: Mapped[int] = mapped_column(
        Integer, nullable=False,
        comment="Quantidade de pontos (positivo para acúmulo, negativo para resgate)"
    )
    venda_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendas.id"), nullable=True, index=True,
        comment="Venda que gerou o acúmulo ou resgate"
    )
    descricao: Mapped[str] = mapped_column(String(500), nullable=True)
    saldo_anterior: Mapped[int] = mapped_column(Integer, nullable=False)
    saldo_posterior: Mapped[int] = mapped_column(Integer, nullable=False)
    data_validade: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True,
        comment="Data de validade dos pontos (apenas para ACUMULO)"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relacionamentos
    programa: Mapped["ProgramaFidelidade"] = relationship(
        "ProgramaFidelidade", lazy="selectin"
    )

    # Índices
    __table_args__ = (
        Index("idx_movimentacao_cliente_data", "cliente_id", "created_at"),
        Index("idx_movimentacao_tipo", "tipo"),
    )

    def __repr__(self) -> str:
        return f"<MovimentacaoPontos(id={self.id}, cliente_id={self.cliente_id}, tipo='{self.tipo}', pontos={self.pontos})>"
