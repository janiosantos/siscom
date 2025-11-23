"""
Schemas Pydantic para Categorias
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class CategoriaBase(BaseModel):
    """Schema base de Categoria"""

    nome: str = Field(..., min_length=1, max_length=100, description="Nome da categoria")
    descricao: Optional[str] = Field(None, description="Descrição da categoria")
    ativa: bool = Field(True, description="Categoria ativa")


class CategoriaCreate(CategoriaBase):
    """Schema para criação de Categoria"""
    pass


class CategoriaUpdate(BaseModel):
    """Schema para atualização de Categoria"""

    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    ativa: Optional[bool] = None


class CategoriaResponse(CategoriaBase):
    """Schema de resposta de Categoria"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoriaList(BaseModel):
    """Schema para lista paginada de categorias"""

    items: list[CategoriaResponse]
    total: int
    page: int
    page_size: int
    pages: int
