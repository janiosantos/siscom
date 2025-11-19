"""
Router para endpoints de Vendas
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.vendas.service import VendasService
from app.modules.vendas.schemas import (
    VendaCreate,
    VendaResponse,
    VendaList,
    StatusVendaEnum,
)

router = APIRouter()


@router.post(
    "/",
    response_model=VendaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova venda",
    description="Cria uma nova venda completa com itens",
)
async def create_venda(
    venda_data: VendaCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova venda completa com itens.

    **Regras:**
    - Valida se todos os produtos existem e estão ativos
    - Valida estoque disponível para todos os itens
    - Calcula totais automaticamente
    - Registra saídas de estoque automaticamente
    - Cria a venda com status PENDENTE

    **Exemplo de requisição:**
    ```json
    {
        "cliente_id": 1,
        "vendedor_id": 1,
        "forma_pagamento": "DINHEIRO",
        "desconto": 5.00,
        "observacoes": "Venda balcão",
        "itens": [
            {
                "produto_id": 1,
                "quantidade": 2.0,
                "preco_unitario": 32.90,
                "desconto_item": 0.0
            },
            {
                "produto_id": 2,
                "quantidade": 1.0,
                "preco_unitario": 15.50,
                "desconto_item": 1.00
            }
        ]
    }
    ```
    """
    service = VendasService(db)
    return await service.criar_venda(venda_data)


@router.get(
    "/{venda_id}",
    response_model=VendaResponse,
    summary="Buscar venda por ID",
    description="Retorna os dados completos de uma venda com seus itens",
)
async def get_venda(venda_id: int, db: AsyncSession = Depends(get_db)):
    """Busca uma venda por ID com todos os seus itens"""
    service = VendasService(db)
    return await service.get_venda(venda_id)


@router.get(
    "/",
    response_model=VendaList,
    summary="Listar vendas",
    description="Lista todas as vendas com paginação e filtros",
)
async def list_vendas(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    status: Optional[StatusVendaEnum] = Query(None, description="Filtrar por status"),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    vendedor_id: Optional[int] = Query(None, description="Filtrar por vendedor"),
    data_inicio: Optional[datetime] = Query(None, description="Data inicial"),
    data_fim: Optional[datetime] = Query(None, description="Data final"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista vendas com paginação e filtros.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **status**: Filtrar por status (PENDENTE, FINALIZADA, CANCELADA)
    - **cliente_id**: Filtrar por cliente
    - **vendedor_id**: Filtrar por vendedor
    - **data_inicio**: Data inicial do filtro
    - **data_fim**: Data final do filtro
    """
    service = VendasService(db)
    return await service.list_vendas(
        page=page,
        page_size=page_size,
        status=status,
        cliente_id=cliente_id,
        vendedor_id=vendedor_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@router.put(
    "/{venda_id}/finalizar",
    response_model=VendaResponse,
    summary="Finalizar venda",
    description="Finaliza uma venda pendente",
)
async def finalizar_venda(venda_id: int, db: AsyncSession = Depends(get_db)):
    """
    Finaliza uma venda (altera status para FINALIZADA).

    **Regras:**
    - Venda deve estar PENDENTE
    - Altera status para FINALIZADA
    - Gera conta a receber (quando módulo financeiro estiver implementado)

    **Exemplo de uso:**
    - PUT /vendas/1/finalizar
    """
    service = VendasService(db)
    return await service.finalizar_venda(venda_id)


@router.delete(
    "/{venda_id}",
    response_model=VendaResponse,
    summary="Cancelar venda",
    description="Cancela uma venda e devolve o estoque",
)
async def cancelar_venda(venda_id: int, db: AsyncSession = Depends(get_db)):
    """
    Cancela uma venda e devolve o estoque.

    **Regras:**
    - Venda deve estar PENDENTE ou FINALIZADA
    - Altera status para CANCELADA
    - Devolve estoque automaticamente (registra ajustes de entrada)

    **Exemplo de uso:**
    - DELETE /vendas/1
    """
    service = VendasService(db)
    return await service.cancelar_venda(venda_id)


@router.get(
    "/periodo/relatorio",
    response_model=VendaList,
    summary="Vendas por período",
    description="Retorna vendas de um período específico",
)
async def get_vendas_periodo(
    data_inicio: datetime = Query(..., description="Data inicial"),
    data_fim: datetime = Query(..., description="Data final"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna vendas de um período específico.

    **Parâmetros:**
    - **data_inicio**: Data inicial do período (obrigatório)
    - **data_fim**: Data final do período (obrigatório)
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)

    **Exemplo de uso:**
    - GET /vendas/periodo/relatorio?data_inicio=2025-01-01T00:00:00&data_fim=2025-01-31T23:59:59
    """
    service = VendasService(db)
    return await service.get_vendas_periodo(
        data_inicio=data_inicio,
        data_fim=data_fim,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/periodo/total",
    summary="Total de vendas por período",
    description="Retorna o valor total de vendas em um período",
)
async def get_total_vendas_periodo(
    data_inicio: datetime = Query(..., description="Data inicial"),
    data_fim: datetime = Query(..., description="Data final"),
    status: Optional[StatusVendaEnum] = Query(None, description="Filtrar por status"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna o valor total de vendas em um período.

    **Parâmetros:**
    - **data_inicio**: Data inicial do período (obrigatório)
    - **data_fim**: Data final do período (obrigatório)
    - **status**: Filtrar por status (opcional)

    **Retorno:**
    ```json
    {
        "data_inicio": "2025-01-01T00:00:00",
        "data_fim": "2025-01-31T23:59:59",
        "total": 15350.50,
        "status": "FINALIZADA"
    }
    ```

    **Exemplo de uso:**
    - GET /vendas/periodo/total?data_inicio=2025-01-01T00:00:00&data_fim=2025-01-31T23:59:59&status=FINALIZADA
    """
    service = VendasService(db)
    total = await service.get_total_vendas_periodo(
        data_inicio=data_inicio,
        data_fim=data_fim,
        status=status,
    )

    return {
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "total": total,
        "status": status.value if status else None,
    }
