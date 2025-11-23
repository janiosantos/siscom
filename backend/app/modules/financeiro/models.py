"""
Modelos de Financeiro
"""
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey, Index, Enum, Date, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class StatusFinanceiro(str, PyEnum):
    """Enum para status financeiro"""

    PENDENTE = "PENDENTE"
    PAGA = "PAGA"
    RECEBIDA = "RECEBIDA"
    ATRASADA = "ATRASADA"
    CANCELADA = "CANCELADA"


class ContaPagar(Base):
    """Modelo de Contas a Pagar"""

    __tablename__ = "contas_pagar"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    fornecedor_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    descricao: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    valor_original: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    valor_pago: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    data_emissao: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    data_vencimento: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    data_pagamento: Mapped[date] = mapped_column(
        Date, nullable=True, index=True
    )
    status: Mapped[StatusFinanceiro] = mapped_column(
        Enum(StatusFinanceiro), nullable=False, default=StatusFinanceiro.PENDENTE, index=True
    )
    documento: Mapped[str] = mapped_column(
        String(100), nullable=True, index=True
    )
    categoria_financeira: Mapped[str] = mapped_column(
        String(100), nullable=True, index=True
    )
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_conta_pagar_fornecedor_status", "fornecedor_id", "status"),
        Index("idx_conta_pagar_vencimento_status", "data_vencimento", "status"),
        Index("idx_conta_pagar_categoria", "categoria_financeira"),
        Index("idx_conta_pagar_emissao", "data_emissao"),
    )

    def __repr__(self) -> str:
        return f"<ContaPagar(id={self.id}, descricao='{self.descricao}', valor={self.valor_original}, status='{self.status}')>"


class ContaReceber(Base):
    """Modelo de Contas a Receber"""

    __tablename__ = "contas_receber"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    venda_id: Mapped[int] = mapped_column(
        Integer, nullable=True, index=True
    )
    descricao: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    valor_original: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    valor_recebido: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    data_emissao: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    data_vencimento: Mapped[date] = mapped_column(
        Date, nullable=False, index=True
    )
    data_recebimento: Mapped[date] = mapped_column(
        Date, nullable=True, index=True
    )
    status: Mapped[StatusFinanceiro] = mapped_column(
        Enum(StatusFinanceiro), nullable=False, default=StatusFinanceiro.PENDENTE, index=True
    )
    documento: Mapped[str] = mapped_column(
        String(100), nullable=True, index=True
    )
    categoria_financeira: Mapped[str] = mapped_column(
        String(100), nullable=True, index=True
    )
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_conta_receber_cliente_status", "cliente_id", "status"),
        Index("idx_conta_receber_vencimento_status", "data_vencimento", "status"),
        Index("idx_conta_receber_categoria", "categoria_financeira"),
        Index("idx_conta_receber_emissao", "data_emissao"),
        Index("idx_conta_receber_venda", "venda_id"),
    )

    def __repr__(self) -> str:
        return f"<ContaReceber(id={self.id}, descricao='{self.descricao}', valor={self.valor_original}, status='{self.status}')>"
