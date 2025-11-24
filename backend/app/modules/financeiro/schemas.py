"""
Schemas Pydantic para Financeiro
"""
from datetime import datetime, date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal


class StatusFinanceiroEnum(str, Enum):
    """Enum para status financeiro nos schemas"""

    PENDENTE = "PENDENTE"
    PAGA = "PAGA"
    RECEBIDA = "RECEBIDA"
    ATRASADA = "ATRASADA"
    CANCELADA = "CANCELADA"


# ============================================
# SCHEMAS DE CONTAS A PAGAR
# ============================================

class ContaPagarBase(BaseModel):
    """Schema base de Conta a Pagar"""

    fornecedor_id: int = Field(..., gt=0, description="ID do fornecedor")
    descricao: str = Field(..., min_length=1, max_length=500, description="Descrição da conta")
    valor_original: float = Field(..., gt=0, description="Valor original da conta")
    data_emissao: date = Field(..., description="Data de emissão da conta")
    data_vencimento: date = Field(..., description="Data de vencimento da conta")
    documento: Optional[str] = Field(None, max_length=100, description="Número do documento")
    categoria_financeira: Optional[str] = Field(None, max_length=100, description="Categoria financeira")
    observacoes: Optional[str] = Field(None, description="Observações adicionais")

    @field_validator("data_vencimento")
    @classmethod
    def validar_data_vencimento(cls, v: date, info) -> date:
        """Valida que data de vencimento não pode ser anterior à emissão"""
        if "data_emissao" in info.data and v < info.data["data_emissao"]:
            raise ValueError("Data de vencimento não pode ser anterior à data de emissão")
        return v


class ContaPagarCreate(ContaPagarBase):
    """Schema para criação de Conta a Pagar"""

    pass


class ContaPagarUpdate(BaseModel):
    """Schema para atualização de Conta a Pagar"""

    fornecedor_id: Optional[int] = Field(None, gt=0)
    descricao: Optional[str] = Field(None, min_length=1, max_length=500)
    valor_original: Optional[float] = Field(None, gt=0)
    data_emissao: Optional[date] = None
    data_vencimento: Optional[date] = None
    documento: Optional[str] = Field(None, max_length=100)
    categoria_financeira: Optional[str] = Field(None, max_length=100)
    observacoes: Optional[str] = None


class BaixaPagamentoCreate(BaseModel):
    """Schema para registrar pagamento de conta a pagar"""

    valor_pago: float = Field(..., gt=0, description="Valor pago")
    data_pagamento: date = Field(..., description="Data do pagamento")
    observacoes: Optional[str] = Field(None, description="Observações sobre o pagamento")

    @field_validator("valor_pago")
    @classmethod
    def validar_valor_pago(cls, v: float) -> float:
        """Valida que valor pago seja positivo"""
        if v <= 0:
            raise ValueError("Valor pago deve ser maior que zero")
        return v


class ContaPagarResponse(ContaPagarBase):
    """Schema de resposta de Conta a Pagar"""

    id: int
    valor_pago: float
    data_pagamento: Optional[date]
    status: StatusFinanceiroEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContaPagarList(BaseModel):
    """Schema para lista paginada de contas a pagar"""

    items: list[ContaPagarResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# SCHEMAS DE CONTAS A RECEBER
# ============================================

class ContaReceberBase(BaseModel):
    """Schema base de Conta a Receber"""

    cliente_id: int = Field(..., gt=0, description="ID do cliente")
    venda_id: Optional[int] = Field(None, gt=0, description="ID da venda (opcional)")
    descricao: str = Field(..., min_length=1, max_length=500, description="Descrição da conta")
    valor_original: float = Field(..., gt=0, description="Valor original da conta")
    data_emissao: date = Field(..., description="Data de emissão da conta")
    data_vencimento: date = Field(..., description="Data de vencimento da conta")
    documento: Optional[str] = Field(None, max_length=100, description="Número do documento")
    categoria_financeira: Optional[str] = Field(None, max_length=100, description="Categoria financeira")
    observacoes: Optional[str] = Field(None, description="Observações adicionais")

    @field_validator("data_vencimento")
    @classmethod
    def validar_data_vencimento(cls, v: date, info) -> date:
        """Valida que data de vencimento não pode ser anterior à emissão"""
        if "data_emissao" in info.data and v < info.data["data_emissao"]:
            raise ValueError("Data de vencimento não pode ser anterior à data de emissão")
        return v


class ContaReceberCreate(ContaReceberBase):
    """Schema para criação de Conta a Receber"""

    pass


class ContaReceberUpdate(BaseModel):
    """Schema para atualização de Conta a Receber"""

    cliente_id: Optional[int] = Field(None, gt=0)
    venda_id: Optional[int] = Field(None, gt=0)
    descricao: Optional[str] = Field(None, min_length=1, max_length=500)
    valor_original: Optional[float] = Field(None, gt=0)
    data_emissao: Optional[date] = None
    data_vencimento: Optional[date] = None
    documento: Optional[str] = Field(None, max_length=100)
    categoria_financeira: Optional[str] = Field(None, max_length=100)
    observacoes: Optional[str] = None


class BaixaRecebimentoCreate(BaseModel):
    """Schema para registrar recebimento de conta a receber"""

    valor_recebido: float = Field(..., gt=0, description="Valor recebido")
    data_recebimento: date = Field(..., description="Data do recebimento")
    observacoes: Optional[str] = Field(None, description="Observações sobre o recebimento")

    @field_validator("valor_recebido")
    @classmethod
    def validar_valor_recebido(cls, v: float) -> float:
        """Valida que valor recebido seja positivo"""
        if v <= 0:
            raise ValueError("Valor recebido deve ser maior que zero")
        return v


class ContaReceberResponse(ContaReceberBase):
    """Schema de resposta de Conta a Receber"""

    id: int
    valor_recebido: float
    data_recebimento: Optional[date]
    status: StatusFinanceiroEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContaReceberList(BaseModel):
    """Schema para lista paginada de contas a receber"""

    items: list[ContaReceberResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# SCHEMAS DE FLUXO DE CAIXA
# ============================================

class FluxoCaixaResponse(BaseModel):
    """Schema de resposta para fluxo de caixa"""

    total_a_pagar: float = Field(..., description="Total de contas a pagar pendentes")
    total_a_receber: float = Field(..., description="Total de contas a receber pendentes")
    saldo_projetado: float = Field(..., description="Saldo projetado (a receber - a pagar)")
    total_pago: float = Field(..., description="Total já pago no período")
    total_recebido: float = Field(..., description="Total já recebido no período")
    contas_vencidas_pagar: int = Field(..., description="Quantidade de contas a pagar vencidas")
    contas_vencidas_receber: int = Field(..., description="Quantidade de contas a receber vencidas")
    valor_vencido_pagar: float = Field(..., description="Valor total vencido a pagar")
    valor_vencido_receber: float = Field(..., description="Valor total vencido a receber")


class FluxoCaixaPeriodoResponse(BaseModel):
    """Schema de resposta para fluxo de caixa por período"""

    data_inicio: date
    data_fim: date
    total_a_pagar: float
    total_a_receber: float
    total_pago: float
    total_recebido: float
    saldo_periodo: float
    contas_pagar: list[ContaPagarResponse]
    contas_receber: list[ContaReceberResponse]
