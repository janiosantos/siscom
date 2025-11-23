"""
Modelos de Clientes
"""
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Boolean, Date, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TipoPessoa(str, PyEnum):
    """Tipo de pessoa"""
    PF = "PF"  # Pessoa Física
    PJ = "PJ"  # Pessoa Jurídica


class Cliente(Base):
    """Modelo de Cliente"""

    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    tipo_pessoa: Mapped[TipoPessoa] = mapped_column(
        Enum(TipoPessoa), nullable=False, default=TipoPessoa.PF
    )
    cpf_cnpj: Mapped[str] = mapped_column(
        String(18), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    telefone: Mapped[str] = mapped_column(String(20), nullable=True)
    celular: Mapped[str] = mapped_column(String(20), nullable=True)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=True)

    # Endereço
    endereco: Mapped[str] = mapped_column(String(200), nullable=True)
    numero: Mapped[str] = mapped_column(String(20), nullable=True)
    complemento: Mapped[str] = mapped_column(String(100), nullable=True)
    bairro: Mapped[str] = mapped_column(String(100), nullable=True)
    cidade: Mapped[str] = mapped_column(String(100), nullable=True)
    estado: Mapped[str] = mapped_column(String(2), nullable=True)
    cep: Mapped[str] = mapped_column(String(10), nullable=True)

    # Controle
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_cliente_nome_ativo", "nome", "ativo"),
        Index("idx_cliente_cpf_cnpj", "cpf_cnpj"),
        Index("idx_cliente_data_nascimento", "data_nascimento"),
    )

    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, nome='{self.nome}', cpf_cnpj='{self.cpf_cnpj}')>"
