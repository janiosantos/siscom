"""
Schemas para Programa de Fidelidade
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class TipoMovimentacaoPontosEnum(str, Enum):
    """Enum para tipo de movimentação"""

    ACUMULO = "ACUMULO"
    RESGATE = "RESGATE"
    EXPIRACAO = "EXPIRACAO"
    AJUSTE = "AJUSTE"
    CANCELAMENTO = "CANCELAMENTO"


# ==================== PROGRAMA ====================


class ProgramaFidelidadeBase(BaseModel):
    """Schema base de Programa de Fidelidade"""

    nome: str = Field(..., min_length=1, max_length=100)
    descricao: Optional[str] = None
    pontos_por_real: float = Field(1.0, ge=0, description="Pontos ganhos por R$ 1,00")
    valor_ponto_resgate: float = Field(0.01, ge=0, description="Valor de cada ponto em R$")
    pontos_minimo_resgate: int = Field(100, ge=1, description="Mínimo de pontos para resgate")
    dias_validade_pontos: Optional[int] = Field(None, ge=1, description="Validade em dias (NULL = sem expiração)")
    ativo: bool = True


class ProgramaFidelidadeCreate(ProgramaFidelidadeBase):
    """Schema para criação"""

    pass


class ProgramaFidelidadeUpdate(BaseModel):
    """Schema para atualização"""

    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    pontos_por_real: Optional[float] = Field(None, ge=0)
    valor_ponto_resgate: Optional[float] = Field(None, ge=0)
    pontos_minimo_resgate: Optional[int] = Field(None, ge=1)
    dias_validade_pontos: Optional[int] = Field(None, ge=1)
    ativo: Optional[bool] = None


class ProgramaFidelidadeResponse(ProgramaFidelidadeBase):
    """Schema de resposta"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== SALDO ====================


class SaldoPontosResponse(BaseModel):
    """Schema de resposta de saldo"""

    id: int
    cliente_id: int
    programa_id: int
    pontos_disponiveis: int
    pontos_acumulados_total: int
    pontos_resgatados_total: int
    ultima_movimentacao: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConsultarSaldoResponse(BaseModel):
    """Schema para consulta de saldo simplificada"""

    cliente_id: int
    pontos_disponiveis: int
    valor_disponivel_resgate: float = Field(..., description="Valor em R$ disponível para resgate")
    pontos_acumulados_total: int
    pontos_resgatados_total: int


# ==================== MOVIMENTAÇÃO ====================


class MovimentacaoPontosResponse(BaseModel):
    """Schema de resposta de movimentação"""

    id: int
    cliente_id: int
    programa_id: int
    tipo: TipoMovimentacaoPontosEnum
    pontos: int
    venda_id: Optional[int]
    descricao: Optional[str]
    saldo_anterior: int
    saldo_posterior: int
    data_validade: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AcumularPontosRequest(BaseModel):
    """Schema para acumular pontos"""

    cliente_id: int = Field(..., gt=0)
    valor_compra: float = Field(..., gt=0, description="Valor da compra em R$")
    venda_id: Optional[int] = None
    descricao: Optional[str] = None


class ResgatarPontosRequest(BaseModel):
    """Schema para resgatar pontos"""

    cliente_id: int = Field(..., gt=0)
    pontos: int = Field(..., gt=0, description="Quantidade de pontos a resgatar")
    venda_id: Optional[int] = None
    descricao: Optional[str] = Field(None, max_length=500)


class ResgatarPontosResponse(BaseModel):
    """Schema de resposta de resgate"""

    pontos_resgatados: int
    valor_desconto: float = Field(..., description="Valor do desconto em R$")
    saldo_anterior: int
    saldo_atual: int
    movimentacao: MovimentacaoPontosResponse


class ExtratoResponse(BaseModel):
    """Schema de extrato de pontos"""

    cliente_id: int
    saldo_atual: int
    movimentacoes: list[MovimentacaoPontosResponse]
    total_movimentacoes: int
