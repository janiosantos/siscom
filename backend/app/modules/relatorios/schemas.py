"""
Schemas para Relatórios e Dashboard
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ==================== DASHBOARD ====================


class DashboardVendasResponse(BaseModel):
    """Schema de Dashboard de Vendas"""

    # Período
    data_inicio: date
    data_fim: date

    # Vendas
    total_vendas: int = Field(..., description="Total de vendas no período")
    valor_total_vendas: float = Field(..., description="Valor total faturado")
    ticket_medio: float = Field(..., description="Ticket médio das vendas")

    # Comparação com período anterior
    variacao_vendas_percentual: float = Field(
        ..., description="Variação percentual de vendas vs período anterior"
    )
    variacao_valor_percentual: float = Field(
        ..., description="Variação percentual de faturamento vs período anterior"
    )

    # Produtos mais vendidos
    produto_mais_vendido: Optional[str] = None
    quantidade_produto_mais_vendido: Optional[float] = None

    # Estoque
    total_produtos_estoque: int = Field(..., description="Total de produtos em estoque")
    total_produtos_abaixo_minimo: int = Field(
        ..., description="Produtos abaixo do estoque mínimo"
    )

    # Financeiro
    total_contas_receber: float = Field(..., description="Total a receber")
    total_contas_vencidas: float = Field(..., description="Total de contas vencidas")


class KPICard(BaseModel):
    """Card de KPI individual"""

    titulo: str
    valor: float
    unidade: str = ""
    variacao_percentual: Optional[float] = None
    icone: Optional[str] = None


class DashboardResponse(BaseModel):
    """Dashboard completo"""

    periodo: str
    data_atualizacao: datetime
    kpis: list[KPICard]
    vendas: DashboardVendasResponse


# ==================== RELATÓRIOS ====================


class VendedorDesempenho(BaseModel):
    """Desempenho individual de vendedor"""

    vendedor_id: int
    vendedor_nome: str
    total_vendas: int
    valor_total_vendido: float
    ticket_medio: float
    margem_lucro_percentual: float
    comissao_estimada: float


class RelatorioVendedoresResponse(BaseModel):
    """Relatório de desempenho de vendedores"""

    data_inicio: date
    data_fim: date
    vendedores: list[VendedorDesempenho]
    total_geral: float


class ProdutoVendido(BaseModel):
    """Produto vendido no período"""

    produto_id: int
    produto_nome: str
    codigo_barras: str
    quantidade_vendida: float
    valor_total: float
    quantidade_vendas: int


class RelatorioVendasResponse(BaseModel):
    """Relatório de vendas"""

    data_inicio: date
    data_fim: date
    produtos: list[ProdutoVendido]
    total_quantidade: float
    total_valor: float


class FluxoCaixaDia(BaseModel):
    """Fluxo de caixa de um dia"""

    data: date
    entradas: float
    saidas: float
    saldo: float


class RelatorioFluxoCaixaResponse(BaseModel):
    """Relatório de fluxo de caixa"""

    data_inicio: date
    data_fim: date
    dias: list[FluxoCaixaDia]
    total_entradas: float
    total_saidas: float
    saldo_final: float


class EstoqueBaixo(BaseModel):
    """Produto com estoque baixo"""

    produto_id: int
    produto_nome: str
    codigo_barras: str
    estoque_atual: float
    estoque_minimo: float
    deficit: float
    valor_reposicao_estimado: float


class RelatorioEstoqueBaixoResponse(BaseModel):
    """Relatório de produtos com estoque baixo"""

    produtos: list[EstoqueBaixo]
    total_produtos: int
    valor_total_reposicao: float
