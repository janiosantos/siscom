"""
Modelos de Fornecedores
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Fornecedor(Base):
    """Modelo de Fornecedor"""

    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    razao_social: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    nome_fantasia: Mapped[str] = mapped_column(String(200), nullable=True)
    cnpj: Mapped[str] = mapped_column(
        String(18), unique=True, nullable=False, index=True
    )
    ie: Mapped[str] = mapped_column(String(20), nullable=True)  # Inscrição Estadual
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    telefone: Mapped[str] = mapped_column(String(20), nullable=True)
    celular: Mapped[str] = mapped_column(String(20), nullable=True)
    contato_nome: Mapped[str] = mapped_column(
        String(100), nullable=True
    )  # Nome do contato principal

    # Endereço
    endereco: Mapped[str] = mapped_column(String(200), nullable=True)
    numero: Mapped[str] = mapped_column(String(20), nullable=True)
    complemento: Mapped[str] = mapped_column(String(100), nullable=True)
    bairro: Mapped[str] = mapped_column(String(100), nullable=True)
    cidade: Mapped[str] = mapped_column(String(100), nullable=True)
    estado: Mapped[str] = mapped_column(String(2), nullable=True)
    cep: Mapped[str] = mapped_column(String(10), nullable=True)

    # Dados bancários
    banco: Mapped[str] = mapped_column(String(100), nullable=True)
    agencia: Mapped[str] = mapped_column(String(20), nullable=True)
    conta: Mapped[str] = mapped_column(String(30), nullable=True)

    # Observações
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)

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
        Index("idx_fornecedor_razao_social_ativo", "razao_social", "ativo"),
        Index("idx_fornecedor_cnpj", "cnpj"),
    )

    def __repr__(self) -> str:
        return f"<Fornecedor(id={self.id}, razao_social='{self.razao_social}', cnpj='{self.cnpj}')>"
