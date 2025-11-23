"""
Schemas Pydantic para Compras
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from enum import Enum


class StatusPedidoCompraEnum(str, Enum):
    """Enum para status de pedido de compra"""

    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    RECEBIDO_PARCIAL = "RECEBIDO_PARCIAL"
    RECEBIDO = "RECEBIDO"
    CANCELADO = "CANCELADO"


# ============================================
# SCHEMAS DE ITEM PEDIDO COMPRA
# ============================================


class ItemPedidoCompraBase(BaseModel):
    """Schema base de Item de Pedido de Compra"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade_solicitada: float = Field(..., gt=0, description="Quantidade solicitada")
    preco_unitario: float = Field(..., ge=0, description="Preço unitário do produto")
    observacao: Optional[str] = Field(None, max_length=500, description="Observação do item")


class ItemPedidoCompraCreate(ItemPedidoCompraBase):
    """Schema para criação de Item de Pedido de Compra"""

    pass


class ItemPedidoCompraResponse(ItemPedidoCompraBase):
    """Schema de resposta de Item de Pedido de Compra"""

    id: int
    pedido_id: int
    quantidade_recebida: float
    subtotal_item: float
    created_at: datetime
    produto: Optional[dict] = None  # Simplificado para evitar imports circulares

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def convert_produto(cls, data):
        """Converter produto SQLAlchemy para dict"""
        if hasattr(data, '__dict__'):
            obj_dict = data.__dict__
            if 'produto' in obj_dict and obj_dict['produto'] is not None:
                if not isinstance(obj_dict['produto'], dict):
                    produto = obj_dict['produto']
                    obj_dict['produto'] = {
                        'id': getattr(produto, 'id', None),
                        'descricao': getattr(produto, 'descricao', None),
                        'codigo_barras': getattr(produto, 'codigo_barras', None),
                    }
        return data


# ============================================
# SCHEMAS DE PEDIDO COMPRA
# ============================================


class PedidoCompraBase(BaseModel):
    """Schema base de Pedido de Compra"""

    fornecedor_id: int = Field(..., gt=0, description="ID do fornecedor")
    data_pedido: date = Field(..., description="Data do pedido")
    data_entrega_prevista: date = Field(..., description="Data de entrega prevista")
    desconto: float = Field(default=0.0, ge=0, description="Desconto do pedido")
    valor_frete: float = Field(default=0.0, ge=0, description="Valor do frete")
    observacoes: Optional[str] = Field(None, description="Observações do pedido")

    @field_validator("data_entrega_prevista")
    @classmethod
    def validar_data_entrega(cls, v: date, info) -> date:
        """Valida que data de entrega não seja anterior à data do pedido"""
        data_pedido = info.data.get("data_pedido")
        if data_pedido and v < data_pedido:
            raise ValueError("Data de entrega prevista não pode ser anterior à data do pedido")
        return v


class PedidoCompraCreate(PedidoCompraBase):
    """Schema para criação de Pedido de Compra"""

    itens: List[ItemPedidoCompraCreate] = Field(
        ..., min_length=1, description="Lista de itens do pedido"
    )


class PedidoCompraUpdate(BaseModel):
    """Schema para atualização de Pedido de Compra"""

    fornecedor_id: Optional[int] = Field(None, gt=0)
    data_pedido: Optional[date] = None
    data_entrega_prevista: Optional[date] = None
    desconto: Optional[float] = Field(None, ge=0)
    valor_frete: Optional[float] = Field(None, ge=0)
    observacoes: Optional[str] = None


class PedidoCompraResponse(PedidoCompraBase):
    """Schema de resposta de Pedido de Compra"""

    id: int
    data_entrega_real: Optional[date] = None
    subtotal: float
    valor_total: float
    status: StatusPedidoCompraEnum
    created_at: datetime
    updated_at: datetime
    fornecedor: Optional[dict] = None  # Simplificado para evitar imports circulares
    itens: List[ItemPedidoCompraResponse] = []

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='before')
    @classmethod
    def convert_fornecedor(cls, data):
        """Converter fornecedor SQLAlchemy para dict"""
        if hasattr(data, '__dict__'):
            obj_dict = data.__dict__
            if 'fornecedor' in obj_dict and obj_dict['fornecedor'] is not None:
                if not isinstance(obj_dict['fornecedor'], dict):
                    fornecedor = obj_dict['fornecedor']
                    obj_dict['fornecedor'] = {
                        'id': getattr(fornecedor, 'id', None),
                        'nome_fantasia': getattr(fornecedor, 'nome_fantasia', None),
                        'razao_social': getattr(fornecedor, 'razao_social', None),
                    }
        return data


class PedidoCompraList(BaseModel):
    """Schema para lista paginada de pedidos de compra"""

    items: List[PedidoCompraResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ============================================
# SCHEMAS AUXILIARES
# ============================================


class ReceberPedidoRequest(BaseModel):
    """Schema para recebimento de pedido (total ou parcial)"""

    itens_recebidos: List[dict] = Field(
        ...,
        min_length=1,
        description="Lista de itens recebidos com formato: [{item_id: int, quantidade_recebida: float}]",
    )
    data_recebimento: date = Field(..., description="Data do recebimento")
    observacao: Optional[str] = Field(None, description="Observação do recebimento")

    @field_validator("itens_recebidos")
    @classmethod
    def validar_itens_recebidos(cls, v: List[dict]) -> List[dict]:
        """Valida estrutura dos itens recebidos"""
        for item in v:
            if "item_id" not in item or "quantidade_recebida" not in item:
                raise ValueError(
                    "Cada item recebido deve conter 'item_id' e 'quantidade_recebida'"
                )
            if not isinstance(item["item_id"], int) or item["item_id"] <= 0:
                raise ValueError("item_id deve ser um inteiro positivo")
            if not isinstance(item["quantidade_recebida"], (int, float)) or item["quantidade_recebida"] <= 0:
                raise ValueError("quantidade_recebida deve ser um número positivo")
        return v


class SugestaoCompraResponse(BaseModel):
    """Schema de resposta de Sugestão de Compra"""

    produto_id: int
    produto_descricao: str
    codigo_barras: str
    estoque_atual: float
    estoque_minimo: float
    quantidade_sugerida: float
    preco_custo: float
    valor_total_sugestao: float
    classe_abc: str = Field(
        default="C", description="Classe ABC do produto (A=alta prioridade, B=média, C=baixa)"
    )

    model_config = ConfigDict(from_attributes=True)


class SugestaoCompraList(BaseModel):
    """Schema para lista de sugestões de compra"""

    items: List[SugestaoCompraResponse]
    total: int
    valor_total_geral: float
