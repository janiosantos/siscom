"""
Módulo de Pedidos de Venda

Gerencia o ciclo completo de pedidos desde a criação até o faturamento:
- RASCUNHO: Pedido em criação
- CONFIRMADO: Pedido confirmado pelo cliente
- EM_SEPARACAO: Produtos sendo separados
- SEPARADO: Produtos separados, pronto para entrega
- EM_ENTREGA: Saiu para entrega
- ENTREGUE: Entregue ao cliente
- FATURADO: Gerou venda e NF-e
- CANCELADO: Pedido cancelado
"""

from app.modules.pedidos_venda.models import (
    PedidoVenda,
    ItemPedidoVenda,
    StatusPedidoVenda,
    TipoEntrega,
)
from app.modules.pedidos_venda.schemas import (
    PedidoVendaCreate,
    PedidoVendaUpdate,
    PedidoVendaResponse,
    ItemPedidoVendaCreate,
    ItemPedidoVendaResponse,
)
from app.modules.pedidos_venda.service import PedidoVendaService
from app.modules.pedidos_venda.repository import PedidoVendaRepository
from app.modules.pedidos_venda.router import router

__all__ = [
    "PedidoVenda",
    "ItemPedidoVenda",
    "StatusPedidoVenda",
    "TipoEntrega",
    "PedidoVendaCreate",
    "PedidoVendaUpdate",
    "PedidoVendaResponse",
    "ItemPedidoVendaCreate",
    "ItemPedidoVendaResponse",
    "PedidoVendaService",
    "PedidoVendaRepository",
    "router",
]
