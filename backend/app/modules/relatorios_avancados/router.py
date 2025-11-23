"""
Router de Relatórios Avançados
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.relatorios_avancados.service import RelatoriosAvancadosService
from app.modules.relatorios_avancados.schemas import (
    RelatorioFiltros,
    RelatorioVendasPorPeriodoResponse,
    RelatorioDesempenhoVendedoresResponse,
    RelatorioProdutosMaisVendidosResponse,
    RelatorioCurvaABCResponse,
    RelatorioMargemLucroResponse,
)

router = APIRouter(prefix="/relatorios-avancados", tags=["Relatórios Avançados"])


@router.post(
    "/vendas-por-periodo",
    response_model=RelatorioVendasPorPeriodoResponse,
    summary="Relatório de vendas por período",
    description="Análise completa de vendas com comparação vs período anterior",
)
async def relatorio_vendas_por_periodo(
    filtros: RelatorioFiltros,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera relatório de vendas por período

    **Retorna:**
    - Total de vendas e faturamento
    - Ticket médio
    - Quantidade de clientes atendidos
    - Comparação % vs período anterior
    - Detalhamento diário (vendas por dia)

    **Filtros opcionais:**
    - vendedor_id: Filtrar por vendedor específico
    - cliente_id: Filtrar por cliente específico

    **Exemplo de requisição:**
    ```json
    {
        "data_inicio": "2025-11-01",
        "data_fim": "2025-11-30",
        "vendedor_id": 5,
        "cliente_id": null
    }
    ```
    """
    service = RelatoriosAvancadosService(db)
    return await service.relatorio_vendas_por_periodo(
        data_inicio=filtros.data_inicio,
        data_fim=filtros.data_fim,
        vendedor_id=filtros.vendedor_id,
        cliente_id=filtros.cliente_id,
    )


@router.post(
    "/desempenho-vendedores",
    response_model=RelatorioDesempenhoVendedoresResponse,
    summary="Desempenho de vendedores",
    description="Ranking de vendedores por faturamento e número de vendas",
)
async def relatorio_desempenho_vendedores(
    filtros: RelatorioFiltros,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera relatório de desempenho de vendedores

    **Retorna:**
    - Lista de vendedores ordenada por faturamento
    - Total de vendas por vendedor
    - Faturamento total
    - Ticket médio
    - Comissão estimada (5% do faturamento)

    **Exemplo de requisição:**
    ```json
    {
        "data_inicio": "2025-11-01",
        "data_fim": "2025-11-30"
    }
    ```

    **Nota:** Os filtros vendedor_id e cliente_id são ignorados neste relatório
    """
    service = RelatoriosAvancadosService(db)
    return await service.relatorio_desempenho_vendedores(
        data_inicio=filtros.data_inicio,
        data_fim=filtros.data_fim,
    )


@router.post(
    "/produtos-mais-vendidos",
    response_model=RelatorioProdutosMaisVendidosResponse,
    summary="Produtos mais vendidos",
    description="Ranking de produtos por quantidade vendida e faturamento",
)
async def relatorio_produtos_mais_vendidos(
    filtros: RelatorioFiltros,
    limit: int = Query(50, ge=1, le=500, description="Número máximo de produtos"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera relatório de produtos mais vendidos

    **Retorna:**
    - Lista de produtos ordenada por quantidade vendida
    - Quantidade total vendida
    - Faturamento gerado
    - Número de vendas
    - Totais gerais

    **Parâmetros:**
    - limit: Número máximo de produtos (1-500, padrão: 50)

    **Exemplo de requisição:**
    ```json
    {
        "data_inicio": "2025-11-01",
        "data_fim": "2025-11-30"
    }
    ```

    **Nota:** Os filtros vendedor_id e cliente_id são ignorados neste relatório
    """
    service = RelatoriosAvancadosService(db)
    return await service.relatorio_produtos_mais_vendidos(
        data_inicio=filtros.data_inicio,
        data_fim=filtros.data_fim,
        limit=limit,
    )


@router.post(
    "/curva-abc-clientes",
    response_model=RelatorioCurvaABCResponse,
    summary="Curva ABC de clientes",
    description="Classificação de clientes em A, B, C por faturamento",
)
async def relatorio_curva_abc_clientes(
    filtros: RelatorioFiltros,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera relatório de Curva ABC de clientes

    **Classificação:**
    - **Classe A**: Top clientes que representam 80% do faturamento
    - **Classe B**: Clientes intermediários que representam 15% do faturamento
    - **Classe C**: Demais clientes que representam 5% do faturamento

    **Retorna:**
    - Resumo por classe (quantidade, faturamento, percentual)
    - Lista completa de clientes com classificação
    - Faturamento e ticket médio por cliente

    **Exemplo de requisição:**
    ```json
    {
        "data_inicio": "2025-11-01",
        "data_fim": "2025-11-30"
    }
    ```

    **Nota:** Os filtros vendedor_id e cliente_id são ignorados neste relatório
    """
    service = RelatoriosAvancadosService(db)
    return await service.relatorio_curva_abc_clientes(
        data_inicio=filtros.data_inicio,
        data_fim=filtros.data_fim,
    )


@router.post(
    "/margem-lucro",
    response_model=RelatorioMargemLucroResponse,
    summary="Análise de margem de lucro",
    description="Análise de margem por categoria de produtos",
)
async def relatorio_margem_lucro(
    filtros: RelatorioFiltros,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera relatório de análise de margem de lucro

    **Retorna:**
    - Margem média geral (%)
    - Faturamento total, custo total e lucro bruto
    - Análise por categoria:
      - Faturamento
      - Custo total
      - Lucro bruto
      - Margem percentual

    **Cálculo:**
    - Lucro Bruto = Faturamento - Custo
    - Margem % = (Lucro / Faturamento) * 100

    **Exemplo de requisição:**
    ```json
    {
        "data_inicio": "2025-11-01",
        "data_fim": "2025-11-30"
    }
    ```

    **Nota:** Os filtros vendedor_id e cliente_id são ignorados neste relatório
    """
    service = RelatoriosAvancadosService(db)
    return await service.relatorio_margem_lucro(
        data_inicio=filtros.data_inicio,
        data_fim=filtros.data_fim,
    )
