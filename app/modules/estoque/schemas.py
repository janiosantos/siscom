"""
Schemas Pydantic para Estoque
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.modules.produtos.schemas import ProdutoResponse


class TipoMovimentacaoEnum(str, Enum):
    """Enum para tipos de movimentação de estoque"""

    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    AJUSTE = "AJUSTE"
    TRANSFERENCIA = "TRANSFERENCIA"
    DEVOLUCAO = "DEVOLUCAO"


class MovimentacaoBase(BaseModel):
    """Schema base de Movimentação de Estoque"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    tipo: TipoMovimentacaoEnum = Field(..., description="Tipo de movimentação")
    quantidade: float = Field(..., gt=0, description="Quantidade movimentada")
    custo_unitario: float = Field(..., ge=0, description="Custo unitário do produto")
    documento_referencia: Optional[str] = Field(
        None, max_length=100, description="Documento de referência (NF, pedido, etc)"
    )
    observacao: Optional[str] = Field(None, max_length=500, description="Observação")
    usuario_id: Optional[int] = Field(None, description="ID do usuário responsável")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que a quantidade seja positiva"""
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v

    @field_validator("custo_unitario")
    @classmethod
    def validar_custo_unitario(cls, v: float) -> float:
        """Valida que o custo unitário não seja negativo"""
        if v < 0:
            raise ValueError("Custo unitário não pode ser negativo")
        return v


class MovimentacaoCreate(MovimentacaoBase):
    """Schema para criação de Movimentação de Estoque"""

    pass


class EntradaEstoqueCreate(BaseModel):
    """Schema para entrada de estoque via NF ou compra"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: float = Field(..., gt=0, description="Quantidade de entrada")
    custo_unitario: float = Field(..., ge=0, description="Custo unitário do produto")
    documento_referencia: Optional[str] = Field(
        None, max_length=100, description="Número da NF ou documento"
    )
    observacao: Optional[str] = Field(None, max_length=500, description="Observação")
    usuario_id: Optional[int] = Field(None, description="ID do usuário responsável")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que a quantidade seja positiva"""
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v


class SaidaEstoqueCreate(BaseModel):
    """Schema para saída de estoque por venda ou consumo"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: float = Field(..., gt=0, description="Quantidade de saída")
    custo_unitario: Optional[float] = Field(
        None, ge=0, description="Custo unitário (opcional, usa preço de custo do produto se não informado)"
    )
    documento_referencia: Optional[str] = Field(
        None, max_length=100, description="Número da venda ou documento"
    )
    observacao: Optional[str] = Field(None, max_length=500, description="Observação")
    usuario_id: Optional[int] = Field(None, description="ID do usuário responsável")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que a quantidade seja positiva"""
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v


class AjusteEstoqueCreate(BaseModel):
    """Schema para ajuste manual de estoque"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: float = Field(
        ..., description="Quantidade do ajuste (positivo para adicionar, negativo para remover)"
    )
    custo_unitario: Optional[float] = Field(
        None, ge=0, description="Custo unitário (opcional, usa preço de custo do produto se não informado)"
    )
    observacao: str = Field(
        ..., min_length=10, max_length=500, description="Justificativa obrigatória para o ajuste"
    )
    usuario_id: Optional[int] = Field(None, description="ID do usuário responsável")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que a quantidade não seja zero"""
        if v == 0:
            raise ValueError("Quantidade do ajuste não pode ser zero")
        return v

    @field_validator("observacao")
    @classmethod
    def validar_observacao(cls, v: str) -> str:
        """Valida que a observação não esteja vazia"""
        if not v or not v.strip():
            raise ValueError("Observação é obrigatória para ajustes de estoque")
        if len(v.strip()) < 10:
            raise ValueError(
                "Observação deve ter no mínimo 10 caracteres para justificar o ajuste"
            )
        return v.strip()


class MovimentacaoResponse(MovimentacaoBase):
    """Schema de resposta de Movimentação de Estoque"""

    id: int
    valor_total: float = Field(..., description="Valor total da movimentação")
    produto: ProdutoResponse
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MovimentacaoList(BaseModel):
    """Schema para lista paginada de movimentações"""

    items: list[MovimentacaoResponse]
    total: int
    page: int
    page_size: int
    pages: int


class EstoqueAtualResponse(BaseModel):
    """Schema de resposta para saldo atual de estoque"""

    produto_id: int
    produto_descricao: str
    produto_codigo_barras: str
    estoque_atual: float
    estoque_minimo: float
    unidade: str
    custo_medio: float = Field(..., description="Custo médio ponderado")
    valor_total_estoque: float = Field(
        ..., description="Valor total do estoque (quantidade * custo médio)"
    )
    abaixo_minimo: bool = Field(..., description="Indica se está abaixo do estoque mínimo")

    model_config = ConfigDict(from_attributes=True)
