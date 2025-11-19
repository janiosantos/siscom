"""
Router para Integração E-commerce
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.ecommerce.service import EcommerceService
from app.modules.ecommerce.schemas import (
    ConfiguracaoEcommerceCreate,
    ConfiguracaoEcommerceUpdate,
    ConfiguracaoEcommerceResponse,
    PedidoEcommerceCreate,
    PedidoEcommerceResponse,
    PedidoEcommerceList,
    ProcessarPedidoRequest,
    SincronizarProdutoRequest,
    ResultadoSincronizacao,
)

router = APIRouter(prefix="/ecommerce", tags=["E-commerce"])


# ==================== CONFIGURAÇÃO ====================


@router.post(
    "/configuracoes",
    response_model=ConfiguracaoEcommerceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar configuração de e-commerce",
    description="Cria configuração de integração com plataforma de e-commerce",
)
async def criar_configuracao(
    data: ConfiguracaoEcommerceCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Cria configuração de e-commerce.

    **Plataformas suportadas:**
    - WOOCOMMERCE
    - MAGENTO
    - TRAY
    - SHOPIFY
    - VTEX
    - OUTRO
    """
    service = EcommerceService(db)
    return await service.criar_configuracao(data)


@router.get(
    "/configuracoes/{config_id}",
    response_model=ConfiguracaoEcommerceResponse,
    summary="Buscar configuração",
    description="Busca configuração de e-commerce por ID",
)
async def get_configuracao(config_id: int, db: AsyncSession = Depends(get_db)):
    """Busca configuração de e-commerce"""
    service = EcommerceService(db)
    return await service.get_configuracao(config_id)


@router.put(
    "/configuracoes/{config_id}",
    response_model=ConfiguracaoEcommerceResponse,
    summary="Atualizar configuração",
    description="Atualiza configuração de e-commerce",
)
async def atualizar_configuracao(
    config_id: int,
    data: ConfiguracaoEcommerceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza configuração de e-commerce"""
    service = EcommerceService(db)
    return await service.atualizar_configuracao(config_id, data)


# ==================== PEDIDOS ====================


@router.post(
    "/pedidos",
    response_model=PedidoEcommerceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Importar pedido do e-commerce",
    description="Importa pedido recebido do e-commerce",
)
async def criar_pedido(
    data: PedidoEcommerceCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Importa pedido do e-commerce.

    **Ações automáticas:**
    - Tenta mapear produtos por SKU
    - Status inicial: PENDENTE
    """
    service = EcommerceService(db)
    return await service.criar_pedido(data)


@router.get(
    "/pedidos/{pedido_id}",
    response_model=PedidoEcommerceResponse,
    summary="Buscar pedido",
    description="Busca pedido do e-commerce por ID",
)
async def get_pedido(pedido_id: int, db: AsyncSession = Depends(get_db)):
    """Busca pedido do e-commerce"""
    service = EcommerceService(db)
    return await service.get_pedido(pedido_id)


@router.get(
    "/pedidos",
    response_model=PedidoEcommerceList,
    summary="Listar pedidos",
    description="Lista pedidos do e-commerce com filtros",
)
async def listar_pedidos(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    config_id: Optional[int] = Query(None, description="Filtrar por configuração"),
    db: AsyncSession = Depends(get_db),
):
    """Lista pedidos do e-commerce"""
    service = EcommerceService(db)
    return await service.list_pedidos(page, page_size, status, config_id)


@router.post(
    "/pedidos/{pedido_id}/processar",
    response_model=PedidoEcommerceResponse,
    summary="Processar pedido",
    description="Processa pedido do e-commerce e cria venda no ERP",
)
async def processar_pedido(
    pedido_id: int,
    data: ProcessarPedidoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Processa pedido do e-commerce.

    **Ações automáticas:**
    - Busca ou cria cliente
    - Mapeia produtos
    - Cria venda no ERP
    - Dá baixa em estoque
    - Atualiza status para FATURADO
    """
    service = EcommerceService(db)
    return await service.processar_pedido(pedido_id, data)


# ==================== SINCRONIZAÇÃO ====================


@router.post(
    "/configuracoes/{config_id}/sincronizar-produtos",
    response_model=ResultadoSincronizacao,
    summary="Sincronizar produtos",
    description="Sincroniza produtos do ERP para e-commerce",
)
async def sincronizar_produtos(
    config_id: int,
    data: SincronizarProdutoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Sincroniza produtos do ERP para e-commerce.

    **Nota:** Esta é uma implementação base.
    Conectores específicos para cada plataforma devem ser implementados.
    """
    service = EcommerceService(db)
    return await service.sincronizar_produtos(config_id, data.produto_ids)
