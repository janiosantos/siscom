"""
Modelos de Ordens de Serviço
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    String,
    DateTime,
    Boolean,
    Numeric,
    Integer,
    ForeignKey,
    Enum,
    Text,
    Index,
    Date,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StatusOS(str, PyEnum):
    """Status da Ordem de Serviço"""

    ABERTA = "ABERTA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"
    FATURADA = "FATURADA"


class TipoServico(Base):
    """Modelo de Tipo de Serviço"""

    __tablename__ = "tipos_servico"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    preco_padrao: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Índices
    __table_args__ = (Index("idx_tipo_servico_nome_ativo", "nome", "ativo"),)

    def __repr__(self) -> str:
        return f"<TipoServico(id={self.id}, nome='{self.nome}')>"


class Tecnico(Base):
    """Modelo de Técnico"""

    __tablename__ = "tecnicos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False, index=True)
    telefone: Mapped[str] = mapped_column(String(20), nullable=True)
    especialidades: Mapped[str] = mapped_column(Text, nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Índices
    __table_args__ = (
        Index("idx_tecnico_nome_ativo", "nome", "ativo"),
        Index("idx_tecnico_cpf", "cpf"),
    )

    def __repr__(self) -> str:
        return f"<Tecnico(id={self.id}, nome='{self.nome}', cpf='{self.cpf}')>"


class OrdemServico(Base):
    """Modelo de Ordem de Serviço"""

    __tablename__ = "ordens_servico"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id"), nullable=False, index=True
    )
    tecnico_id: Mapped[int] = mapped_column(
        ForeignKey("tecnicos.id"), nullable=False, index=True
    )
    tipo_servico_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_servico.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=True, index=True
    )
    numero_serie: Mapped[str] = mapped_column(String(100), nullable=True)
    data_abertura: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    data_prevista: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    data_conclusao: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[StatusOS] = mapped_column(
        Enum(StatusOS), nullable=False, default=StatusOS.ABERTA, index=True
    )
    descricao_problema: Mapped[str] = mapped_column(Text, nullable=True)
    descricao_solucao: Mapped[str] = mapped_column(Text, nullable=True)
    valor_mao_obra: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship("Cliente", lazy="selectin")
    tecnico: Mapped["Tecnico"] = relationship("Tecnico", lazy="selectin")
    tipo_servico: Mapped["TipoServico"] = relationship("TipoServico", lazy="selectin")
    produto: Mapped["Produto"] = relationship("Produto", lazy="selectin")
    itens: Mapped[list["ItemOS"]] = relationship(
        "ItemOS", back_populates="ordem_servico", lazy="selectin"
    )
    apontamentos: Mapped[list["ApontamentoHoras"]] = relationship(
        "ApontamentoHoras", back_populates="ordem_servico", lazy="selectin"
    )

    # Índices compostos
    __table_args__ = (
        Index("idx_os_cliente_status", "cliente_id", "status"),
        Index("idx_os_tecnico_status", "tecnico_id", "status"),
        Index("idx_os_data_abertura", "data_abertura"),
        Index("idx_os_data_prevista", "data_prevista"),
        Index("idx_os_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<OrdemServico(id={self.id}, cliente_id={self.cliente_id}, status='{self.status}')>"


class ItemOS(Base):
    """Modelo de Item de Ordem de Serviço (materiais usados)"""

    __tablename__ = "itens_os"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    os_id: Mapped[int] = mapped_column(
        ForeignKey("ordens_servico.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    total_item: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    ordem_servico: Mapped["OrdemServico"] = relationship(
        "OrdemServico", back_populates="itens"
    )
    produto: Mapped["Produto"] = relationship("Produto", lazy="selectin")

    # Índices
    __table_args__ = (
        Index("idx_item_os_os_id", "os_id"),
        Index("idx_item_os_produto_id", "produto_id"),
    )

    def __repr__(self) -> str:
        return f"<ItemOS(id={self.id}, os_id={self.os_id}, produto_id={self.produto_id})>"


class ApontamentoHoras(Base):
    """Modelo de Apontamento de Horas Trabalhadas"""

    __tablename__ = "apontamentos_horas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    os_id: Mapped[int] = mapped_column(
        ForeignKey("ordens_servico.id"), nullable=False, index=True
    )
    tecnico_id: Mapped[int] = mapped_column(
        ForeignKey("tecnicos.id"), nullable=False, index=True
    )
    data: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    horas_trabalhadas: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    ordem_servico: Mapped["OrdemServico"] = relationship(
        "OrdemServico", back_populates="apontamentos"
    )
    tecnico: Mapped["Tecnico"] = relationship("Tecnico", lazy="selectin")

    # Índices
    __table_args__ = (
        Index("idx_apontamento_os_id", "os_id"),
        Index("idx_apontamento_tecnico_id", "tecnico_id"),
        Index("idx_apontamento_data", "data"),
    )

    def __repr__(self) -> str:
        return f"<ApontamentoHoras(id={self.id}, os_id={self.os_id}, horas={self.horas_trabalhadas})>"
