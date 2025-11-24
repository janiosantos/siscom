"""
Schemas Pydantic para Pedidos de Venda
"""
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.modules.pedidos_venda.models import StatusPedidoVenda, TipoEntrega


# ============= Item Pedido Venda =============

class ItemPedidoVendaBase(BaseModel):
    """Schema base de item de pedido"""
    produto_id: int
    quantidade: float = Field(..., gt=0)
    preco_unitario: float = Field(..., gt=0)
    desconto_item: float = Field(default=0.0, ge=0)
    observacao_item: Optional[str] = None


class ItemPedidoVendaCreate(ItemPedidoVendaBase):
    """Schema para criar item de pedido"""
    pass


class ItemPedidoVendaUpdate(BaseModel):
    """Schema para atualizar item de pedido"""
    quantidade: Optional[float] = Field(None, gt=0)
    preco_unitario: Optional[float] = Field(None, gt=0)
    desconto_item: Optional[float] = Field(None, ge=0)
    observacao_item: Optional[str] = None


class ItemPedidoVendaResponse(ItemPedidoVendaBase):
    """Schema de resposta de item de pedido"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    pedido_id: int
    quantidade_separada: float
    total_item: float
    created_at: datetime

    # Dados do produto (nested)
    produto_codigo: Optional[str] = None
    produto_descricao: Optional[str] = None


# ============= Pedido Venda =============

class PedidoVendaBase(BaseModel):
    """Schema base de pedido de venda"""
    cliente_id: int
    data_entrega_prevista: date
    tipo_entrega: TipoEntrega = TipoEntrega.RETIRADA
    endereco_entrega: Optional[str] = None
    desconto: float = Field(default=0.0, ge=0)
    valor_frete: float = Field(default=0.0, ge=0)
    outras_despesas: float = Field(default=0.0, ge=0)
    condicao_pagamento_id: Optional[int] = None
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    observacoes_internas: Optional[str] = None


class PedidoVendaCreate(PedidoVendaBase):
    """Schema para criar pedido de venda"""
    orcamento_id: Optional[int] = None
    itens: List[ItemPedidoVendaCreate] = Field(..., min_length=1)


class PedidoVendaUpdate(BaseModel):
    """Schema para atualizar pedido de venda"""
    cliente_id: Optional[int] = None
    data_entrega_prevista: Optional[date] = None
    tipo_entrega: Optional[TipoEntrega] = None
    endereco_entrega: Optional[str] = None
    desconto: Optional[float] = Field(None, ge=0)
    valor_frete: Optional[float] = Field(None, ge=0)
    outras_despesas: Optional[float] = Field(None, ge=0)
    condicao_pagamento_id: Optional[int] = None
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    observacoes_internas: Optional[str] = None
    status: Optional[StatusPedidoVenda] = None


class PedidoVendaResponse(PedidoVendaBase):
    """Schema de resposta de pedido de venda"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_pedido: str
    orcamento_id: Optional[int]
    vendedor_id: int
    data_pedido: date
    data_entrega_real: Optional[date]
    subtotal: float
    valor_total: float
    status: StatusPedidoVenda
    venda_id: Optional[int]
    usuario_separacao_id: Optional[int]
    data_separacao: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Dados do cliente (nested)
    cliente_nome: Optional[str] = None
    cliente_documento: Optional[str] = None

    # Dados do vendedor (nested)
    vendedor_nome: Optional[str] = None

    # Itens
    itens: List[ItemPedidoVendaResponse] = []


class PedidoVendaListResponse(BaseModel):
    """Schema para lista de pedidos"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero_pedido: str
    cliente_nome: str
    vendedor_nome: str
    data_pedido: date
    data_entrega_prevista: date
    valor_total: float
    status: StatusPedidoVenda
    tipo_entrega: TipoEntrega


# ============= Ações Específicas =============

class ConfirmarPedidoRequest(BaseModel):
    """Request para confirmar pedido"""
    observacao: Optional[str] = None


class SepararPedidoRequest(BaseModel):
    """Request para separar pedido"""
    itens_separados: List[dict] = Field(..., description="Lista com produto_id e quantidade_separada")


class FaturarPedidoRequest(BaseModel):
    """Request para faturar pedido"""
    gerar_nfe: bool = Field(default=True, description="Gerar NF-e automaticamente")
    observacao: Optional[str] = None


class CancelarPedidoRequest(BaseModel):
    """Request para cancelar pedido"""
    motivo: str = Field(..., min_length=10, description="Motivo do cancelamento")


# ============= Relatórios =============

class RelatorioPedidosResponse(BaseModel):
    """Relatório de pedidos"""
    total_pedidos: int
    total_valor: float
    pedidos_por_status: dict
    pedidos_atrasados: int
    ticket_medio: float
