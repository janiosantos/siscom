"""
Router para CRM e Análise RFM
"""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.crm.service import CRMService
from app.modules.crm.schemas import (
    AnaliseRFMResponse,
    RelatorioSegmentosResponse,
    TopClientesResponse,
)

router = APIRouter(prefix="/crm", tags=["CRM"])


@router.get(
    "/analise-rfm",
    response_model=AnaliseRFMResponse,
    summary="Análise RFM de clientes",
    description="Análise de Recência, Frequência e Monetário dos clientes",
)
async def analise_rfm(
    data_inicio: date = Query(default=None, description="Data inicial (padrão: há 1 ano)"),
    data_fim: date = Query(default=None, description="Data final (padrão: hoje)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Análise RFM (Recência, Frequência, Monetário).

    **Scores (1-5):**
    - **Recência (R)**: Dias desde última compra (menor = melhor)
    - **Frequência (F)**: Total de compras (maior = melhor)
    - **Monetário (M)**: Valor total gasto (maior = melhor)

    **Segmentos:**
    - CAMPEÕES: Melhores clientes
    - CLIENTES FIÉIS: Regulares e consistentes
    - NOVOS CLIENTES: Compraram recentemente
    - EM RISCO: Não compram há algum tempo
    - PERDIDOS: Não compram há muito tempo
    - ALTO VALOR: Gastam muito
    - POTENCIAL: Com potencial de crescimento
    """
    service = CRMService(db)
    return await service.analise_rfm(data_inicio, data_fim)


@router.get(
    "/segmentos",
    response_model=RelatorioSegmentosResponse,
    summary="Relatório de segmentos",
    description="Clientes agrupados por segmento RFM",
)
async def relatorio_segmentos(
    data_inicio: date = Query(default=None, description="Data inicial"),
    data_fim: date = Query(default=None, description="Data final"),
    db: AsyncSession = Depends(get_db),
):
    """
    Relatório de clientes por segmento RFM.

    **Retorna:**
    - Total de clientes por segmento
    - Valor total por segmento
    - Percentuais sobre total
    """
    service = CRMService(db)
    return await service.relatorio_segmentos(data_inicio, data_fim)


@router.get(
    "/top-clientes",
    response_model=TopClientesResponse,
    summary="Top clientes",
    description="Clientes que mais gastaram no período",
)
async def top_clientes(
    limit: int = Query(20, ge=1, le=100, description="Quantidade de clientes"),
    data_inicio: date = Query(default=None, description="Data inicial"),
    data_fim: date = Query(default=None, description="Data final"),
    db: AsyncSession = Depends(get_db),
):
    """
    Top clientes por valor gasto.

    **Retorna:**
    - Clientes ordenados por valor total
    - Total de compras e ticket médio
    - Dias desde última compra
    """
    service = CRMService(db)
    return await service.top_clientes(limit, data_inicio, data_fim)
