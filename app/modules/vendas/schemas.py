"""
Schemas Pydantic para Vendas
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


class StatusVendaEnum(str, Enum):
    """Enum de Status de Venda"""
    PENDENTE = "PENDENTE"
    FINALIZADA = "FINALIZADA"
    CANCELADA = "CANCELADA"


# ========== ITEM VENDA SCHEMAS ==========

class ItemVendaBase(BaseModel):
    """Schema base de Item de Venda"""
    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: float = Field(..., gt=0, description="Quantidade do produto")
    preco_unitario: float = Field(..., gt=0, description="Preço unitário do produto")
    desconto_item: float = Field(default=0.0, ge=0, description="Desconto no item")

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


class ItemVendaCreate(ItemVendaBase):
    """Schema para criação de Item de Venda"""
    pass


class ItemVendaResponse(ItemVendaBase):
    """Schema de resposta de Item de Venda"""
    id: int
    venda_id: int
    subtotal_item: float
    total_item: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== VENDA SCHEMAS ==========

class VendaBase(BaseModel):
    """Schema base de Venda"""
    cliente_id: Optional[int] = Field(None, gt=0, description="ID do cliente (opcional)")
    vendedor_id: int = Field(..., gt=0, description="ID do vendedor")
    forma_pagamento: str = Field(..., min_length=1, max_length=50, description="Forma de pagamento")
    desconto: float = Field(default=0.0, ge=0, description="Desconto total na venda")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações da venda")

    @field_validator("desconto")
    @classmethod
    def validar_desconto(cls, v: float) -> float:
        """Valida que desconto não seja negativo"""
        if v < 0:
            raise ValueError("Desconto não pode ser negativo")
        return v

    @field_validator("forma_pagamento")
    @classmethod
    def validar_forma_pagamento(cls, v: str) -> str:
        """Valida forma de pagamento"""
        if not v or not v.strip():
            raise ValueError("Forma de pagamento não pode ser vazia")
        return v.strip().upper()


class VendaCreate(VendaBase):
    """Schema para criação de Venda"""
    itens: list[ItemVendaCreate] = Field(..., min_length=1, description="Itens da venda")

    @field_validator("itens")
    @classmethod
    def validar_itens(cls, v: list[ItemVendaCreate]) -> list[ItemVendaCreate]:
        """Valida que a venda tenha pelo menos um item"""
        if not v or len(v) == 0:
            raise ValueError("Venda deve ter pelo menos um item")
        return v


class VendaUpdate(BaseModel):
    """Schema para atualização de Venda"""
    cliente_id: Optional[int] = Field(None, gt=0)
    forma_pagamento: Optional[str] = Field(None, min_length=1, max_length=50)
    desconto: Optional[float] = Field(None, ge=0)
    observacoes: Optional[str] = Field(None, max_length=500)

    @field_validator("forma_pagamento")
    @classmethod
    def validar_forma_pagamento(cls, v: Optional[str]) -> Optional[str]:
        """Valida forma de pagamento"""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Forma de pagamento não pode ser vazia")
        return v.strip().upper()


class VendaResponse(VendaBase):
    """Schema de resposta de Venda"""
    id: int
    data_venda: datetime
    subtotal: float
    valor_total: float
    status: StatusVendaEnum
    created_at: datetime
    updated_at: datetime
    itens: list[ItemVendaResponse] = []

    model_config = ConfigDict(from_attributes=True)


class VendaList(BaseModel):
    """Schema para lista paginada de vendas"""
    items: list[VendaResponse]
    total: int
    page: int
    page_size: int
    pages: int


class VendaResumo(BaseModel):
    """Schema resumido de Venda (sem itens)"""
    id: int
    cliente_id: Optional[int]
    vendedor_id: int
    data_venda: datetime
    subtotal: float
    desconto: float
    valor_total: float
    forma_pagamento: str
    status: StatusVendaEnum
    observacoes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
