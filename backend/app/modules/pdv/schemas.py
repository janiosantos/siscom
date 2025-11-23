"""
Schemas Pydantic para PDV
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.modules.vendas.schemas import ItemVendaCreate


class StatusCaixaEnum(str, Enum):
    """Enum de Status de Caixa"""
    ABERTO = "ABERTO"
    FECHADO = "FECHADO"


class TipoMovimentacaoCaixaEnum(str, Enum):
    """Enum de Tipo de Movimentação de Caixa"""
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    SANGRIA = "SANGRIA"
    SUPRIMENTO = "SUPRIMENTO"


# ========== CAIXA SCHEMAS ==========

class CaixaBase(BaseModel):
    """Schema base de Caixa"""
    operador_id: int = Field(..., gt=0, description="ID do operador")
    valor_abertura: float = Field(..., ge=0, description="Valor de abertura do caixa")

    @field_validator("valor_abertura")
    @classmethod
    def validar_valor_abertura(cls, v: float) -> float:
        """Valida que valor de abertura não seja negativo"""
        if v < 0:
            raise ValueError("Valor de abertura não pode ser negativo")
        return v


class AbrirCaixaCreate(CaixaBase):
    """Schema para abertura de caixa"""
    pass


class FecharCaixaCreate(BaseModel):
    """Schema para fechamento de caixa"""
    valor_fechamento: float = Field(..., ge=0, description="Valor de fechamento do caixa")

    @field_validator("valor_fechamento")
    @classmethod
    def validar_valor_fechamento(cls, v: float) -> float:
        """Valida que valor de fechamento não seja negativo"""
        if v < 0:
            raise ValueError("Valor de fechamento não pode ser negativo")
        return v


class CaixaResponse(CaixaBase):
    """Schema de resposta de Caixa"""
    id: int
    data_abertura: datetime
    data_fechamento: Optional[datetime]
    valor_fechamento: Optional[float]
    status: StatusCaixaEnum
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ========== MOVIMENTACAO CAIXA SCHEMAS ==========

class MovimentacaoCaixaBase(BaseModel):
    """Schema base de Movimentação de Caixa"""
    tipo: TipoMovimentacaoCaixaEnum = Field(..., description="Tipo de movimentação")
    valor: float = Field(..., gt=0, description="Valor da movimentação")
    descricao: Optional[str] = Field(None, max_length=200, description="Descrição da movimentação")

    @field_validator("valor")
    @classmethod
    def validar_valor(cls, v: float) -> float:
        """Valida que valor seja maior que zero"""
        if v <= 0:
            raise ValueError("Valor deve ser maior que zero")
        return v


class MovimentacaoCaixaCreate(MovimentacaoCaixaBase):
    """Schema para criação de Movimentação de Caixa"""
    venda_id: Optional[int] = Field(None, gt=0, description="ID da venda (opcional)")


class MovimentacaoCaixaResponse(MovimentacaoCaixaBase):
    """Schema de resposta de Movimentação de Caixa"""
    id: int
    caixa_id: int
    venda_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MovimentacoesCaixaList(BaseModel):
    """Schema para lista de movimentações de caixa"""
    items: list[MovimentacaoCaixaResponse]
    total: int


# ========== VENDA PDV SCHEMAS ==========

class VendaPDVCreate(BaseModel):
    """Schema simplificado para venda no PDV"""
    cliente_id: Optional[int] = Field(None, gt=0, description="ID do cliente (opcional)")
    forma_pagamento: str = Field(..., min_length=1, max_length=50, description="Forma de pagamento")
    desconto: float = Field(default=0.0, ge=0, description="Desconto total na venda")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações da venda")
    itens: list[ItemVendaCreate] = Field(..., min_length=1, description="Itens da venda")

    @field_validator("itens")
    @classmethod
    def validar_itens(cls, v: list[ItemVendaCreate]) -> list[ItemVendaCreate]:
        """Valida que a venda tenha pelo menos um item"""
        if not v or len(v) == 0:
            raise ValueError("Venda deve ter pelo menos um item")
        return v

    @field_validator("forma_pagamento")
    @classmethod
    def validar_forma_pagamento(cls, v: str) -> str:
        """Valida forma de pagamento"""
        if not v or not v.strip():
            raise ValueError("Forma de pagamento não pode ser vazia")
        return v.strip().upper()


# ========== SANGRIA E SUPRIMENTO SCHEMAS ==========

class SangriaCreate(BaseModel):
    """Schema para sangria de caixa"""
    valor: float = Field(..., gt=0, description="Valor da sangria")
    descricao: str = Field(..., min_length=1, max_length=200, description="Descrição da sangria")

    @field_validator("valor")
    @classmethod
    def validar_valor(cls, v: float) -> float:
        """Valida que valor seja maior que zero"""
        if v <= 0:
            raise ValueError("Valor da sangria deve ser maior que zero")
        return v

    @field_validator("descricao")
    @classmethod
    def validar_descricao(cls, v: str) -> str:
        """Valida que descrição não seja vazia"""
        if not v or not v.strip():
            raise ValueError("Descrição da sangria é obrigatória")
        return v.strip()


class SuprimentoCreate(BaseModel):
    """Schema para suprimento de caixa"""
    valor: float = Field(..., gt=0, description="Valor do suprimento")
    descricao: str = Field(..., min_length=1, max_length=200, description="Descrição do suprimento")

    @field_validator("valor")
    @classmethod
    def validar_valor(cls, v: float) -> float:
        """Valida que valor seja maior que zero"""
        if v <= 0:
            raise ValueError("Valor do suprimento deve ser maior que zero")
        return v

    @field_validator("descricao")
    @classmethod
    def validar_descricao(cls, v: str) -> str:
        """Valida que descrição não seja vazia"""
        if not v or not v.strip():
            raise ValueError("Descrição do suprimento é obrigatória")
        return v.strip()


# ========== SALDO CAIXA SCHEMA ==========

class SaldoCaixaResponse(BaseModel):
    """Schema de resposta de saldo do caixa"""
    caixa_id: int
    operador_id: int
    data_abertura: datetime
    valor_abertura: float
    total_entradas: float
    total_saidas: float
    total_sangrias: float
    total_suprimentos: float
    saldo_atual: float
    saldo_esperado: float
    status: StatusCaixaEnum
