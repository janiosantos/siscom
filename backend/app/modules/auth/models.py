"""
Models para Autenticação e Autorização (RBAC)
"""
from datetime import datetime
from typing import List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Table, Column, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# Tabela de associação User-Role (Many-to-Many)
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
)


# Tabela de associação Role-Permission (Many-to-Many)
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True),
)


class User(Base):
    """
    Modelo de Usuário

    Representa um usuário do sistema com autenticação e autorização
    """
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relacionamentos
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
        lazy="selectin"
    )

    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Role(Base):
    """
    Modelo de Papel/Função (Role)

    Representa um conjunto de permissões que podem ser atribuídas a usuários
    """
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relacionamentos
    users: Mapped[List["User"]] = relationship(
        "User",
        secondary=user_roles,
        back_populates="roles"
    )

    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"


class Permission(Base):
    """
    Modelo de Permissão

    Representa uma permissão específica no sistema (ex: vendas:create, produtos:read)
    """
    __tablename__ = 'permissions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # ex: vendas, produtos
    action: Mapped[str] = mapped_column(String(20), nullable=False, index=True)    # ex: create, read, update, delete

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relacionamentos
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}', resource='{self.resource}', action='{self.action}')>"


class AuditLog(Base):
    """
    Modelo de Log de Auditoria

    Registra todas as ações realizadas por usuários no sistema
    """
    __tablename__ = 'audit_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # login, create_venda, etc
    resource: Mapped[str] = mapped_column(String(50), nullable=True, index=True)  # vendas, produtos, etc
    resource_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)  # JSON com detalhes da ação
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)  # IPv4 ou IPv6
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relacionamentos
    user: Mapped["User"] = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, user_id={self.user_id}, action='{self.action}', resource='{self.resource}')>"


class RefreshToken(Base):
    """
    Modelo de Refresh Token

    Armazena tokens de refresh para renovação de access tokens
    """
    __tablename__ = 'refresh_tokens'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
