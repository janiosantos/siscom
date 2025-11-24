"""
Schemas para Relatórios Avançados
"""
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional


# ==================== REQUEST SCHEMAS ====================

class RelatorioFiltros(BaseModel):
    """Filtros comuns para relatórios"""
    data_inicio: date = Field(..., description="Data início do período")
    data_fim: date = Field(..., description="Data fim do período")
    vendedor_id: Optional[int] = Field(None, description="Filtrar por vendedor")
    cliente_id: Optional[int] = Field(None, description="Filtrar por cliente")


# ==================== VENDAS POR PERÍODO ====================

class VendaDiaria(BaseModel):
    """Venda de um dia específico"""
    data: str = Field(..., description="Data no formato YYYY-MM-DD")
    vendas: int = Field(..., description="Número de vendas")
    faturamento: float = Field(..., description="Faturamento do dia")
    ticket_medio: float = Field(..., description="Ticket médio")


class RelatorioVendasPorPeriodoResponse(BaseModel):
    """Relatório de vendas por período"""
    # Período
    data_inicio: str
    data_fim: str

    # Totais
    total_vendas: int = Field(..., description="Total de vendas no período")
    faturamento_total: float = Field(..., description="Faturamento total")
    ticket_medio: float = Field(..., description="Ticket médio")
    clientes_atendidos: int = Field(..., description="Quantidade de clientes únicos")

    # Comparação
    variacao_vendas_percent: float = Field(..., description="% vs período anterior")
    variacao_faturamento_percent: float = Field(..., description="% vs período anterior")

    # Detalhamento
    vendas_diarias: List[VendaDiaria] = Field(default_factory=list)


# ==================== DESEMPENHO DE VENDEDORES ====================

class VendedorDesempenho(BaseModel):
    """Desempenho de um vendedor"""
    vendedor_id: int
    vendedor_nome: str
    total_vendas: int = Field(..., description="Número de vendas")
    faturamento_total: float = Field(..., description="Faturamento total")
    ticket_medio: float = Field(..., description="Ticket médio")
    comissao_estimada: float = Field(0.0, description="Comissão estimada (5%)")


class RelatorioDesempenhoVendedoresResponse(BaseModel):
    """Relatório de desempenho de vendedores"""
    data_inicio: str
    data_fim: str
    vendedores: List[VendedorDesempenho]
    total_geral: float = Field(..., description="Faturamento total de todos")


# ==================== PRODUTOS MAIS VENDIDOS ====================

class ProdutoMaisVendido(BaseModel):
    """Produto mais vendido"""
    produto_id: int
    produto_nome: str
    produto_codigo: str
    quantidade_vendida: float = Field(..., description="Quantidade total vendida")
    faturamento: float = Field(..., description="Faturamento gerado")
    quantidade_vendas: int = Field(..., description="Número de vendas")


class RelatorioProdutosMaisVendidosResponse(BaseModel):
    """Relatório de produtos mais vendidos"""
    data_inicio: str
    data_fim: str
    produtos: List[ProdutoMaisVendido]
    total_quantidade: float
    total_faturamento: float


# ==================== CURVA ABC DE CLIENTES ====================

class ClasseABC(BaseModel):
    """Resumo de uma classe ABC"""
    classe: str = Field(..., description="A, B ou C")
    quantidade_clientes: int
    faturamento_total: float
    percentual_faturamento: float = Field(..., description="% do faturamento total")


class ClienteCurvaABC(BaseModel):
    """Cliente na curva ABC"""
    cliente_id: int
    cliente_nome: str
    classe: str = Field(..., description="A, B ou C")
    faturamento: float
    quantidade_compras: int
    ticket_medio: float


class RelatorioCurvaABCResponse(BaseModel):
    """Relatório de Curva ABC de clientes"""
    data_inicio: str
    data_fim: str

    # Resumo por classe
    classe_a: ClasseABC
    classe_b: ClasseABC
    classe_c: ClasseABC

    # Lista de clientes
    clientes: List[ClienteCurvaABC]


# ==================== ANÁLISE DE MARGEM ====================

class MargemCategoria(BaseModel):
    """Margem de uma categoria"""
    categoria_id: int
    categoria_nome: str
    faturamento: float
    custo_total: float
    lucro_bruto: float
    margem_percentual: float = Field(..., description="(lucro/faturamento) * 100")


class RelatorioMargemLucroResponse(BaseModel):
    """Relatório de análise de margem de lucro"""
    data_inicio: str
    data_fim: str

    # Totais gerais
    faturamento_total: float
    custo_total: float
    lucro_bruto: float
    margem_media: float = Field(..., description="Margem média em %")

    # Por categoria
    categorias: List[MargemCategoria]
