"""
Router para Relatórios e Dashboard
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.relatorios.service import RelatoriosService
from app.modules.relatorios.schemas import (
    DashboardResponse,
    RelatorioVendedoresResponse,
    RelatorioVendasResponse,
    RelatorioEstoqueBaixoResponse,
)

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Dashboard principal",
    description="Retorna dashboard com principais KPIs",
)
async def get_dashboard(
    data_inicio: date = Query(default=None, description="Data inicial (padrão: há 30 dias)"),
    data_fim: date = Query(default=None, description="Data final (padrão: hoje)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Dashboard com principais métricas:
    - Faturamento total e variação
    - Total de vendas e ticket médio
    - Produtos mais vendidos
    - Alertas de estoque
    - Contas a receber e vencidas
    """
    if not data_fim:
        data_fim = date.today()
    if not data_inicio:
        data_inicio = data_fim - timedelta(days=30)

    service = RelatoriosService(db)
    return await service.get_dashboard(data_inicio, data_fim)


@router.get(
    "/vendedores",
    response_model=RelatorioVendedoresResponse,
    summary="Relatório de vendedores",
    description="Desempenho individual de vendedores",
)
async def relatorio_vendedores(
    data_inicio: date = Query(..., description="Data inicial"),
    data_fim: date = Query(..., description="Data final"),
    db: AsyncSession = Depends(get_db),
):
    """Relatório de desempenho de vendedores"""
    service = RelatoriosService(db)
    return await service.relatorio_vendedores(data_inicio, data_fim)


@router.get(
    "/vendas",
    response_model=RelatorioVendasResponse,
    summary="Relatório de vendas",
    description="Produtos vendidos no período",
)
async def relatorio_vendas(
    data_inicio: date = Query(..., description="Data inicial"),
    data_fim: date = Query(..., description="Data final"),
    db: AsyncSession = Depends(get_db),
):
    """Relatório de produtos vendidos no período"""
    service = RelatoriosService(db)
    return await service.relatorio_vendas(data_inicio, data_fim)


@router.get(
    "/estoque-baixo",
    response_model=RelatorioEstoqueBaixoResponse,
    summary="Relatório de estoque baixo",
    description="Produtos abaixo do estoque mínimo",
)
async def relatorio_estoque_baixo(db: AsyncSession = Depends(get_db)):
    """Produtos com estoque abaixo do mínimo"""
    service = RelatoriosService(db)
    return await service.relatorio_estoque_baixo()
