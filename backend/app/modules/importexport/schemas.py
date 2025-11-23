"""
Schemas Pydantic para Import/Export
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ImportFormatEnum(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class ExportFormatEnum(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PDF = "pdf"


class ImportStatusEnum(str, Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATED = "validated"
    IMPORTING = "importing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


# ============================================================================
# IMPORT SCHEMAS
# ============================================================================

class ImportValidationError(BaseModel):
    """Erro de validação"""
    row: int
    column: str
    value: Any
    error: str


class ImportPreviewRow(BaseModel):
    """Preview de uma linha da importação"""
    row_number: int
    data: Dict[str, Any]
    is_valid: bool
    errors: List[str] = Field(default_factory=list)


class ImportPreviewResponse(BaseModel):
    """Preview da importação"""
    total_rows: int
    sample_rows: List[ImportPreviewRow]
    columns: List[str]
    detected_format: ImportFormatEnum
    validation_errors: List[ImportValidationError] = Field(default_factory=list)
    is_valid: bool
    mapping_suggestions: Dict[str, str] = Field(default_factory=dict)


class ImportStartRequest(BaseModel):
    """Request para iniciar importação"""
    module: str = Field(..., description="Módulo alvo (produtos, clientes, etc)")
    format: ImportFormatEnum
    mapping: Dict[str, str] = Field(
        ...,
        description="Mapeamento de colunas do arquivo para campos do sistema"
    )
    skip_errors: bool = Field(
        default=False,
        description="Continuar importação mesmo com erros"
    )
    dry_run: bool = Field(
        default=False,
        description="Simular importação sem persistir dados"
    )


class ImportStatusResponse(BaseModel):
    """Status da importação"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    module: str
    format: ImportFormatEnum
    filename: str
    status: ImportStatusEnum
    total_rows: int
    processed_rows: int
    success_rows: int
    failed_rows: int
    validation_errors: Optional[str] = None
    import_errors: Optional[str] = None
    can_rollback: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    @property
    def progress_percentage(self) -> float:
        """Percentual de progresso"""
        if self.total_rows == 0:
            return 0.0
        return (self.processed_rows / self.total_rows) * 100


class ImportRollbackRequest(BaseModel):
    """Request para rollback de importação"""
    import_id: int
    reason: Optional[str] = None


# ============================================================================
# EXPORT SCHEMAS
# ============================================================================

class ExportRequest(BaseModel):
    """Request para exportação"""
    module: str = Field(..., description="Módulo a exportar")
    format: ExportFormatEnum
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filtros a aplicar na exportação"
    )
    columns: Optional[List[str]] = Field(
        default=None,
        description="Colunas específicas a exportar (None = todas)"
    )
    include_headers: bool = Field(default=True, description="Incluir cabeçalhos")
    filename: Optional[str] = Field(default=None, description="Nome do arquivo")


class ExportStatusResponse(BaseModel):
    """Status da exportação"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    module: str
    format: ExportFormatEnum
    filename: str
    file_path: Optional[str]
    status: str
    total_records: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime


# ============================================================================
# TEMPLATE SCHEMAS
# ============================================================================

class TemplateColumnMapping(BaseModel):
    """Mapeamento de coluna"""
    file_column: str = Field(..., description="Nome da coluna no arquivo")
    system_field: str = Field(..., description="Campo do sistema")
    required: bool = Field(default=False)
    data_type: str = Field(default="string", description="Tipo de dado esperado")
    validation_rule: Optional[str] = None


class ImportTemplateCreate(BaseModel):
    """Criar template de importação"""
    name: str = Field(..., min_length=3, max_length=100)
    module: str = Field(..., description="Módulo alvo")
    description: Optional[str] = None
    format: ImportFormatEnum
    column_mapping: Dict[str, str] = Field(
        ...,
        description="Mapeamento de colunas"
    )
    required_columns: List[str] = Field(
        ...,
        description="Colunas obrigatórias"
    )
    validation_rules: Optional[Dict[str, Any]] = None


class ImportTemplateResponse(BaseModel):
    """Response de template"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    module: str
    description: Optional[str]
    format: ImportFormatEnum
    column_mapping: str  # JSON string
    required_columns: str  # JSON string
    validation_rules: Optional[str]  # JSON string
    is_active: bool
    is_system: bool
    created_at: datetime
    updated_at: datetime


class ImportTemplateListResponse(BaseModel):
    """Lista de templates"""
    templates: List[ImportTemplateResponse]
    total: int


# ============================================================================
# BULK OPERATIONS
# ============================================================================

class BulkOperationResult(BaseModel):
    """Resultado de operação em lote"""
    total: int
    success: int
    failed: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================================================
# STATISTICS
# ============================================================================

class ImportExportStats(BaseModel):
    """Estatísticas de import/export"""
    total_imports: int
    successful_imports: int
    failed_imports: int
    total_exports: int
    successful_exports: int
    failed_exports: int
    most_imported_module: Optional[str] = None
    most_exported_module: Optional[str] = None
