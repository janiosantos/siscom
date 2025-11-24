"""
Dashboard Router - API endpoints for dashboard
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.schemas import (
    DashboardStats,
    VendasPorDia,
    ProdutoMaisVendido,
    VendasPorVendedor,
    StatusPedidos,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Dashboard principal - estatísticas",
    description="Retorna KPIs principais do dashboard",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obter estatísticas principais do dashboard

    Retorna:
    - Vendas hoje
    - Vendas do mês
    - Pedidos em aberto
    - Pedidos atrasados
    - Ticket médio
    - Faturamento do mês
    - Crescimento vs mês anterior
    - Meta do mês
    """
    service = DashboardService(db)
    return await service.get_stats()


@router.get(
    "/vendas-por-dia",
    response_model=List[VendasPorDia],
    summary="Vendas por dia",
    description="Retorna vendas agrupadas por dia",
)
async def get_vendas_por_dia(
    dias: int = Query(30, ge=1, le=365, description="Número de dias para retornar"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obter vendas agrupadas por dia

    Retorna série temporal de vendas para os últimos N dias.
    Dias sem vendas são preenchidos com zero.

    Args:
        dias: Número de dias para retornar (1-365)

    Returns:
        Lista de vendas por dia com data, quantidade e faturamento
    """
    service = DashboardService(db)
    return await service.get_vendas_por_dia(dias=dias)


@router.get(
    "/produtos-mais-vendidos",
    response_model=List[ProdutoMaisVendido],
    summary="Produtos mais vendidos",
    description="Retorna produtos mais vendidos no mês",
)
async def get_produtos_mais_vendidos(
    limit: int = Query(10, ge=1, le=100, description="Número de produtos para retornar"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obter produtos mais vendidos

    Retorna top N produtos com maior quantidade vendida no mês atual.

    Args:
        limit: Número de produtos para retornar (1-100)

    Returns:
        Lista de produtos com id, nome, quantidade e faturamento
    """
    service = DashboardService(db)
    return await service.get_produtos_mais_vendidos(limit=limit)


@router.get(
    "/vendas-por-vendedor",
    response_model=List[VendasPorVendedor],
    summary="Vendas por vendedor",
    description="Retorna vendas agrupadas por vendedor no mês",
)
async def get_vendas_por_vendedor(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obter vendas agrupadas por vendedor

    Retorna performance de cada vendedor no mês atual.

    Returns:
        Lista de vendedores com total de vendas e ticket médio
    """
    service = DashboardService(db)
    return await service.get_vendas_por_vendedor()


@router.get(
    "/status-pedidos",
    response_model=List[StatusPedidos],
    summary="Pedidos por status",
    description="Retorna pedidos agrupados por status",
)
async def get_status_pedidos(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obter pedidos agrupados por status

    Retorna distribuição de pedidos por status com quantidade e valor total.

    Returns:
        Lista de status com quantidade de pedidos e valor total
    """
    service = DashboardService(db)
    return await service.get_status_pedidos()
