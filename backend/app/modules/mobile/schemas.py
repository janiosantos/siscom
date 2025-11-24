"""
Schemas Pydantic para Mobile (versões otimizadas e resumidas)
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ========== SCHEMAS MOBILE RESUMIDOS ==========

class ProdutoMobileResponse(BaseModel):
    """Schema resumido de Produto para Mobile (apenas campos essenciais)"""
    id: int
    descricao: str
    codigo_barras: str
    preco_venda: float
    estoque_atual: float

    model_config = ConfigDict(from_attributes=True)


class ClienteMobileResponse(BaseModel):
    """Schema resumido de Cliente para Mobile (apenas campos essenciais)"""
    id: int
    nome: str
    telefone: Optional[str] = None
    celular: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ========== SCHEMAS PARA VENDAS MOBILE ==========

class ItemVendaMobileCreate(BaseModel):
    """Schema simplificado para Item de Venda Mobile"""
    produto_id: int = Field(..., gt=0)
    quantidade: float = Field(..., gt=0)
    preco_unitario: float = Field(..., gt=0)
    desconto_item: float = Field(default=0.0, ge=0)


class VendaMobileCreate(BaseModel):
    """Schema simplificado para criação de Venda via Mobile"""
    cliente_id: Optional[int] = Field(None, gt=0)
    vendedor_id: int = Field(..., gt=0)
    forma_pagamento: str = Field(..., min_length=1, max_length=50)
    desconto: float = Field(default=0.0, ge=0)
    observacoes: Optional[str] = Field(None, max_length=500)
    itens: List[ItemVendaMobileCreate] = Field(..., min_length=1)


# ========== SCHEMAS PARA ORÇAMENTOS MOBILE ==========

class ItemOrcamentoMobileCreate(BaseModel):
    """Schema simplificado para Item de Orçamento Mobile"""
    produto_id: int = Field(..., gt=0)
    quantidade: float = Field(..., gt=0)
    preco_unitario: float = Field(..., gt=0)
    desconto_item: float = Field(default=0.0, ge=0)


class OrcamentoMobileCreate(BaseModel):
    """Schema simplificado para criação de Orçamento via Mobile"""
    cliente_id: Optional[int] = Field(None, gt=0)
    vendedor_id: int = Field(..., gt=0)
    validade_dias: int = Field(default=7, gt=0)
    desconto: float = Field(default=0.0, ge=0)
    observacoes: Optional[str] = Field(None, max_length=500)
    itens: List[ItemOrcamentoMobileCreate] = Field(..., min_length=1)


# ========== SCHEMAS DE PESQUISA ==========

class PesquisaResponse(BaseModel):
    """Schema de resposta para pesquisas (genérico)"""
    produtos: List[ProdutoMobileResponse] = Field(default_factory=list)
    clientes: List[ClienteMobileResponse] = Field(default_factory=list)
    total_produtos: int = 0
    total_clientes: int = 0


# ========== SCHEMAS DE CONSULTA DE ESTOQUE ==========

class EstoqueConsultaResponse(BaseModel):
    """Schema para consulta rápida de estoque"""
    produto_id: int
    descricao: str
    codigo_barras: str
    estoque_atual: float
    estoque_minimo: float
    alerta_estoque_baixo: bool = False
    preco_venda: float

    model_config = ConfigDict(from_attributes=True)
