"""
Modelos de Condicoes de Pagamento
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Boolean, Integer, Numeric, ForeignKey, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TipoCondicao(str, PyEnum):
    """Tipo de condição de pagamento"""
    AVISTA = "AVISTA"      # À vista - 1 parcela, 0 dias
    PRAZO = "PRAZO"        # A prazo - 1+ parcelas com intervalos
    PARCELADO = "PARCELADO"  # Parcelado - 2+ parcelas


class CondicaoPagamento(Base):
    """Modelo de Condição de Pagamento"""

    __tablename__ = "condicoes_pagamento"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    descricao: Mapped[str] = mapped_column(String(500), nullable=True)
    tipo: Mapped[TipoCondicao] = mapped_column(
        Enum(TipoCondicao), nullable=False, default=TipoCondicao.AVISTA
    )
    quantidade_parcelas: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    intervalo_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    entrada_percentual: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.0
    )
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    parcelas: Mapped[list["ParcelaPadrao"]] = relationship(
        "ParcelaPadrao",
        back_populates="condicao",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_condicao_nome_ativa", "nome", "ativa"),
        Index("idx_condicao_tipo_ativa", "tipo", "ativa"),
    )

    def __repr__(self) -> str:
        return f"<CondicaoPagamento(id={self.id}, nome='{self.nome}', tipo='{self.tipo}')>"


class ParcelaPadrao(Base):
    """Modelo de Parcela Padrão"""

    __tablename__ = "parcelas_padrao"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    condicao_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("condicoes_pagamento.id", ondelete="CASCADE"), nullable=False, index=True
    )
    numero_parcela: Mapped[int] = mapped_column(Integer, nullable=False)
    dias_vencimento: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percentual_valor: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    condicao: Mapped["CondicaoPagamento"] = relationship(
        "CondicaoPagamento",
        back_populates="parcelas",
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_parcela_condicao_numero", "condicao_id", "numero_parcela"),
    )

    def __repr__(self) -> str:
        return f"<ParcelaPadrao(id={self.id}, condicao_id={self.condicao_id}, numero={self.numero_parcela})>"
