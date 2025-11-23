"""
Models para Multiempresa/Multifilial - Estratégia tenant_id
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, DECIMAL
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List

from app.core.database import Base


class Empresa(Base):
    """Empresa/Tenant - Multi-tenancy"""
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    razao_social: Mapped[str] = mapped_column(String(255))
    nome_fantasia: Mapped[Optional[str]] = mapped_column(String(255))
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, index=True)
    ie: Mapped[Optional[str]] = mapped_column(String(20))
    im: Mapped[Optional[str]] = mapped_column(String(20))

    # Endereço
    endereco: Mapped[Optional[str]] = mapped_column(String(255))
    numero: Mapped[Optional[str]] = mapped_column(String(20))
    complemento: Mapped[Optional[str]] = mapped_column(String(100))
    bairro: Mapped[Optional[str]] = mapped_column(String(100))
    cidade: Mapped[Optional[str]] = mapped_column(String(100))
    uf: Mapped[Optional[str]] = mapped_column(String(2))
    cep: Mapped[Optional[str]] = mapped_column(String(8))
    municipio_codigo: Mapped[Optional[str]] = mapped_column(String(7))

    # Contato
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))

    # Configurações fiscais
    regime_tributario: Mapped[str] = mapped_column(String(20), default="simples_nacional")
    # 1=Simples, 2=Simples excesso, 3=Regime normal
    crt: Mapped[str] = mapped_column(String(1), default="1")

    # Status
    ativa: Mapped[bool] = mapped_column(default=True)
    matriz: Mapped[bool] = mapped_column(default=True)  # É matriz?

    # Configurações
    configuracoes: Mapped[Optional[str]] = mapped_column(Text)  # JSON

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    filiais: Mapped[List["Filial"]] = relationship("Filial", back_populates="empresa")
    usuarios: Mapped[List["EmpresaUsuario"]] = relationship("EmpresaUsuario", back_populates="empresa")


class Filial(Base):
    """Filial de uma empresa"""
    __tablename__ = "filiais"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)

    codigo: Mapped[str] = mapped_column(String(20), index=True)
    nome: Mapped[str] = mapped_column(String(255))
    cnpj: Mapped[Optional[str]] = mapped_column(String(14), unique=True)
    ie: Mapped[Optional[str]] = mapped_column(String(20))

    # Endereço
    endereco: Mapped[Optional[str]] = mapped_column(String(255))
    numero: Mapped[Optional[str]] = mapped_column(String(20))
    complemento: Mapped[Optional[str]] = mapped_column(String(100))
    bairro: Mapped[Optional[str]] = mapped_column(String(100))
    cidade: Mapped[Optional[str]] = mapped_column(String(100))
    uf: Mapped[Optional[str]] = mapped_column(String(2))
    cep: Mapped[Optional[str]] = mapped_column(String(8))

    # Contato
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    gerente: Mapped[Optional[str]] = mapped_column(String(255))

    # Status
    ativa: Mapped[bool] = mapped_column(default=True)
    eh_matriz: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="filiais")


class EmpresaUsuario(Base):
    """Relação Usuário <-> Empresa (Multi-tenant access)"""
    __tablename__ = "empresa_usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Role específica para esta empresa
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"))

    # Filiais que o usuário tem acesso (NULL = todas)
    filiais_ids: Mapped[Optional[str]] = mapped_column(Text)  # JSON array

    # Status
    ativo: Mapped[bool] = mapped_column(default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    empresa: Mapped["Empresa"] = relationship("Empresa", back_populates="usuarios")
    # user relationship será adicionado ao model User existente
