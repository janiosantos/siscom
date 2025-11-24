"""
Models de Import/Export
"""
from sqlalchemy import String, Integer, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional
import enum

from app.core.database import Base


class ImportStatus(str, enum.Enum):
    """Status de importação"""
    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATED = "validated"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ExportStatus(str, enum.Enum):
    """Status de exportação"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportFormat(str, enum.Enum):
    """Formatos de importação"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class ExportFormat(str, enum.Enum):
    """Formatos de exportação"""
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PDF = "pdf"


class ImportLog(Base):
    """Log de importações realizadas"""
    __tablename__ = "import_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Informações básicas
    module: Mapped[str] = mapped_column(String(50), nullable=False)  # produtos, clientes, etc
    format: Mapped[ImportFormat] = mapped_column(SQLEnum(ImportFormat), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status e controle
    status: Mapped[ImportStatus] = mapped_column(
        SQLEnum(ImportStatus),
        default=ImportStatus.PENDING,
        nullable=False
    )

    # Estatísticas
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0)
    success_rows: Mapped[int] = mapped_column(Integer, default=0)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0)

    # Erros e validações
    validation_errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    import_errors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    preview_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    mapping: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON - mapeamento de colunas

    # Rollback
    can_rollback: Mapped[bool] = mapped_column(Boolean, default=True)
    rollback_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON - IDs criados

    # Auditoria
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])


class ExportLog(Base):
    """Log de exportações realizadas"""
    __tablename__ = "export_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Informações básicas
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    format: Mapped[ExportFormat] = mapped_column(SQLEnum(ExportFormat), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[ExportStatus] = mapped_column(
        SQLEnum(ExportStatus),
        default=ExportStatus.PENDING,
        nullable=False
    )

    # Estatísticas
    total_records: Mapped[int] = mapped_column(Integer, default=0)

    # Filtros aplicados
    filters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # Erro
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Auditoria
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])


class ImportTemplate(Base):
    """Templates de importação pré-configurados"""
    __tablename__ = "import_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Informações básicas
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Configuração
    format: Mapped[ImportFormat] = mapped_column(SQLEnum(ImportFormat), nullable=False)
    column_mapping: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    required_columns: Mapped[str] = mapped_column(Text, nullable=False)  # JSON
    validation_rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # Controle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)  # Template do sistema

    # Auditoria
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relacionamentos
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
