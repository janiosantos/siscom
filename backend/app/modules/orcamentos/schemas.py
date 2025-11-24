"""
Schemas Pydantic para Orçamentos
"""
from datetime import datetime, date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


class StatusOrcamentoEnum(str, Enum):
    """Enum de Status de Orçamento"""
    ABERTO = "ABERTO"
    APROVADO = "APROVADO"
    PERDIDO = "PERDIDO"
    CONVERTIDO = "CONVERTIDO"


# ========== ITEM ORCAMENTO SCHEMAS ==========

class ItemOrcamentoBase(BaseModel):
    """Schema base de Item de Orçamento"""
    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: float = Field(..., gt=0, description="Quantidade do produto")
    preco_unitario: float = Field(..., gt=0, description="Preço unitário do produto")
    desconto_item: float = Field(default=0.0, ge=0, description="Desconto no item")
    observacao_item: Optional[str] = Field(None, max_length=200, description="Observação do item")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que quantidade seja maior que zero"""
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v

    @field_validator("preco_unitario")
    @classmethod
    def validar_preco(cls, v: float) -> float:
        """Valida que preço seja maior que zero"""
        if v <= 0:
            raise ValueError("Preço unitário deve ser maior que zero")
        return v

    @field_validator("desconto_item")
    @classmethod
    def validar_desconto(cls, v: float) -> float:
        """Valida que desconto não seja negativo"""
        if v < 0:
            raise ValueError("Desconto não pode ser negativo")
        return v


class ItemOrcamentoCreate(ItemOrcamentoBase):
    """Schema para criação de Item de Orçamento"""
    pass


class ItemOrcamentoResponse(ItemOrcamentoBase):
    """Schema de resposta de Item de Orçamento"""
    id: int
    orcamento_id: int
    total_item: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== ORCAMENTO SCHEMAS ==========

class OrcamentoBase(BaseModel):
    """Schema base de Orçamento"""
    cliente_id: Optional[int] = Field(None, gt=0, description="ID do cliente (opcional)")
    vendedor_id: int = Field(..., gt=0, description="ID do vendedor")
    validade_dias: int = Field(default=15, gt=0, description="Validade em dias")
    desconto: float = Field(default=0.0, ge=0, description="Desconto total no orçamento")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações do orçamento")

    @field_validator("validade_dias")
    @classmethod
    def validar_validade_dias(cls, v: int) -> int:
        """Valida que validade_dias seja maior que zero"""
        if v <= 0:
            raise ValueError("Validade em dias deve ser maior que zero")
        return v

    @field_validator("desconto")
    @classmethod
    def validar_desconto(cls, v: float) -> float:
        """Valida que desconto não seja negativo"""
        if v < 0:
            raise ValueError("Desconto não pode ser negativo")
        return v


class OrcamentoCreate(OrcamentoBase):
    """Schema para criação de Orçamento"""
    itens: list[ItemOrcamentoCreate] = Field(..., min_length=1, description="Itens do orçamento")

    @field_validator("itens")
    @classmethod
    def validar_itens(cls, v: list[ItemOrcamentoCreate]) -> list[ItemOrcamentoCreate]:
        """Valida que o orçamento tenha pelo menos um item"""
        if not v or len(v) == 0:
            raise ValueError("Orçamento deve ter pelo menos um item")
        return v


class OrcamentoUpdate(BaseModel):
    """Schema para atualização de Orçamento"""
    cliente_id: Optional[int] = Field(None, gt=0)
    validade_dias: Optional[int] = Field(None, gt=0)
    desconto: Optional[float] = Field(None, ge=0)
    observacoes: Optional[str] = Field(None, max_length=500)

    @field_validator("validade_dias")
    @classmethod
    def validar_validade_dias(cls, v: Optional[int]) -> Optional[int]:
        """Valida que validade_dias seja maior que zero"""
        if v is not None and v <= 0:
            raise ValueError("Validade em dias deve ser maior que zero")
        return v


class OrcamentoResponse(OrcamentoBase):
    """Schema de resposta de Orçamento"""
    id: int
    data_orcamento: datetime
    data_validade: date
    subtotal: float
    valor_total: float
    status: StatusOrcamentoEnum
    created_at: datetime
    updated_at: datetime
    itens: list[ItemOrcamentoResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrcamentoList(BaseModel):
    """Schema para lista paginada de orçamentos"""
    items: list[OrcamentoResponse]
    total: int
    page: int
    page_size: int
    pages: int


class OrcamentoResumo(BaseModel):
    """Schema resumido de Orçamento (sem itens)"""
    id: int
    cliente_id: Optional[int]
    vendedor_id: int
    data_orcamento: datetime
    data_validade: date
    validade_dias: int
    subtotal: float
    desconto: float
    valor_total: float
    status: StatusOrcamentoEnum
    observacoes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConverterOrcamentoRequest(BaseModel):
    """Schema para conversão de orçamento"""
    forma_pagamento: str = Field(..., min_length=1, max_length=50, description="Forma de pagamento para a venda")

    @field_validator("forma_pagamento")
    @classmethod
    def validar_forma_pagamento(cls, v: str) -> str:
        """Valida forma de pagamento"""
        if not v or not v.strip():
            raise ValueError("Forma de pagamento não pode ser vazia")
        return v.strip().upper()
