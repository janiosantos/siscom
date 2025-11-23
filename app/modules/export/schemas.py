"""
Schemas para exportação de dados
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date


class ExportFiltros(BaseModel):
    """Filtros para exportação de dados"""
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    vendedor_id: Optional[int] = None
    cliente_id: Optional[int] = None
    categoria_id: Optional[int] = None
    status: Optional[str] = None


class DashboardExportRequest(BaseModel):
    """Request para exportação de dados do dashboard"""
    formato: Literal["excel", "csv"] = Field(..., description="Formato do export")
    tipo: Literal["stats", "vendas_dia", "produtos", "vendedores", "status"] = Field(
        ..., description="Tipo de dados a exportar"
    )
    filtros: Optional[ExportFiltros] = None


class OrcamentosExportRequest(BaseModel):
    """Request para exportação bulk de orçamentos"""
    formato: Literal["excel", "csv"] = Field(..., description="Formato do export")
    filtros: Optional[ExportFiltros] = None
    ids: Optional[list[int]] = Field(None, description="IDs específicos para exportar")


class VendasExportRequest(BaseModel):
    """Request para exportação bulk de vendas"""
    formato: Literal["excel", "csv"] = Field(..., description="Formato do export")
    filtros: Optional[ExportFiltros] = None
    ids: Optional[list[int]] = Field(None, description="IDs específicos para exportar")


class ProdutosExportRequest(BaseModel):
    """Request para exportação de produtos"""
    formato: Literal["excel", "csv"] = Field(..., description="Formato do export")
    categoria_id: Optional[int] = None
    apenas_ativos: bool = True
