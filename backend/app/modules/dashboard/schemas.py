"""
Dashboard Schemas - Pydantic models for dashboard endpoints
"""
from pydantic import BaseModel, Field
from datetime import date


class DashboardStats(BaseModel):
    """Dashboard statistics - main KPIs"""

    vendas_hoje: int = Field(..., description="Total de vendas hoje")
    vendas_mes: int = Field(..., description="Total de vendas no mês")
    pedidos_abertos: int = Field(..., description="Pedidos em aberto")
    pedidos_atrasados: int = Field(..., description="Pedidos atrasados")
    ticket_medio: float = Field(..., description="Ticket médio das vendas")
    faturamento_mes: float = Field(..., description="Faturamento total do mês")
    crescimento_mes: float = Field(..., description="Crescimento % vs mês anterior")
    meta_mes: float = Field(..., description="Meta de vendas do mês")


class VendasPorDia(BaseModel):
    """Vendas agrupadas por dia"""

    data: str = Field(..., description="Data no formato YYYY-MM-DD")
    vendas: int = Field(..., description="Número de vendas no dia")
    faturamento: float = Field(..., description="Faturamento total do dia")


class ProdutoMaisVendido(BaseModel):
    """Produto mais vendido"""

    produto_id: int
    produto_nome: str
    quantidade: float = Field(..., description="Quantidade vendida")
    faturamento: float = Field(..., description="Faturamento gerado")


class VendasPorVendedor(BaseModel):
    """Vendas agrupadas por vendedor"""

    vendedor_id: int
    vendedor_nome: str
    total_vendas: int = Field(..., description="Número de vendas")
    ticket_medio: float = Field(..., description="Ticket médio")


class StatusPedidos(BaseModel):
    """Pedidos agrupados por status"""

    status: str = Field(..., description="Status do pedido")
    quantidade: int = Field(..., description="Quantidade de pedidos")
    valor_total: float = Field(..., description="Valor total dos pedidos")
