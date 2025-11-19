"""
Router para endpoints de Compras
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.compras.service import ComprasService
from app.modules.compras.schemas import (
    PedidoCompraCreate,
    PedidoCompraUpdate,
    PedidoCompraResponse,
    PedidoCompraList,
    ReceberPedidoRequest,
    SugestaoCompraList,
)

router = APIRouter(prefix="/compras", tags=["Compras"])


@router.post(
    "/",
    response_model=PedidoCompraResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar pedido de compra",
    description="Cria um novo pedido de compra com itens",
)
async def criar_pedido(
    pedido_data: PedidoCompraCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Cria um novo pedido de compra

    - **fornecedor_id**: ID do fornecedor
    - **data_pedido**: Data do pedido
    - **data_entrega_prevista**: Data de entrega prevista
    - **desconto**: Desconto do pedido (opcional)
    - **valor_frete**: Valor do frete (opcional)
    - **observacoes**: Observações (opcional)
    - **itens**: Lista de itens do pedido (mínimo 1)
    """
    service = ComprasService(db)
    return await service.criar_pedido_compra(pedido_data)


@router.get(
    "/{pedido_id}",
    response_model=PedidoCompraResponse,
    summary="Buscar pedido de compra",
    description="Busca um pedido de compra por ID",
)
async def buscar_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Busca pedido de compra por ID

    - **pedido_id**: ID do pedido
    """
    service = ComprasService(db)
    return await service.get_pedido(pedido_id)


@router.get(
    "/",
    response_model=PedidoCompraList,
    summary="Listar pedidos de compra",
    description="Lista pedidos de compra com paginação e filtros",
)
async def listar_pedidos(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Tamanho da página"),
    fornecedor_id: Optional[int] = Query(None, description="Filtrar por fornecedor"),
    status: Optional[str] = Query(
        None,
        description="Filtrar por status (PENDENTE, APROVADO, RECEBIDO_PARCIAL, RECEBIDO, CANCELADO)",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista pedidos de compra com paginação e filtros

    - **page**: Número da página (padrão: 1)
    - **page_size**: Tamanho da página (padrão: 50, máximo: 100)
    - **fornecedor_id**: Filtrar por fornecedor (opcional)
    - **status**: Filtrar por status (opcional)
    """
    service = ComprasService(db)
    return await service.list_pedidos(page, page_size, fornecedor_id, status)


@router.put(
    "/{pedido_id}",
    response_model=PedidoCompraResponse,
    summary="Atualizar pedido de compra",
    description="Atualiza um pedido de compra (apenas se não estiver recebido ou cancelado)",
)
async def atualizar_pedido(
    pedido_id: int,
    pedido_data: PedidoCompraUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza um pedido de compra

    - **pedido_id**: ID do pedido
    - Não pode atualizar pedido recebido ou cancelado
    """
    service = ComprasService(db)
    return await service.atualizar_pedido(pedido_id, pedido_data)


@router.post(
    "/{pedido_id}/aprovar",
    response_model=PedidoCompraResponse,
    summary="Aprovar pedido de compra",
    description="Aprova um pedido de compra (muda status de PENDENTE para APROVADO)",
)
async def aprovar_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Aprova um pedido de compra

    - **pedido_id**: ID do pedido
    - Apenas pedidos PENDENTES podem ser aprovados
    """
    service = ComprasService(db)
    return await service.aprovar_pedido(pedido_id)


@router.post(
    "/{pedido_id}/receber",
    response_model=PedidoCompraResponse,
    summary="Receber pedido de compra",
    description="Registra recebimento total ou parcial do pedido, cria entrada de estoque e conta a pagar",
)
async def receber_pedido(
    pedido_id: int,
    recebimento_data: ReceberPedidoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra recebimento de pedido (total ou parcial)

    - **pedido_id**: ID do pedido
    - **itens_recebidos**: Lista de itens recebidos com quantidade
    - **data_recebimento**: Data do recebimento
    - **observacao**: Observação do recebimento (opcional)

    Ações automáticas:
    - Cria entrada de estoque para cada item recebido
    - Cria conta a pagar no financeiro
    - Atualiza status do pedido (RECEBIDO_PARCIAL ou RECEBIDO)
    """
    service = ComprasService(db)
    return await service.receber_pedido(pedido_id, recebimento_data)


@router.delete(
    "/{pedido_id}",
    response_model=PedidoCompraResponse,
    summary="Cancelar pedido de compra",
    description="Cancela um pedido de compra (não pode cancelar se já foi recebido)",
)
async def cancelar_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancela um pedido de compra

    - **pedido_id**: ID do pedido
    - Não pode cancelar pedido recebido (total ou parcial)
    """
    service = ComprasService(db)
    return await service.cancelar_pedido(pedido_id)


@router.get(
    "/sugestao-compras/",
    response_model=SugestaoCompraList,
    summary="Sugestão automática de compras",
    description="Gera lista de produtos sugeridos para compra baseado em estoque mínimo e curva ABC",
)
async def sugestao_compras(
    db: AsyncSession = Depends(get_db),
):
    """
    Gera sugestão automática de compras

    Regras:
    - Analisa produtos com estoque_atual < estoque_minimo
    - Classifica por curva ABC (A=alta prioridade, B=média, C=baixa)
    - Quantidade sugerida = (estoque_minimo * 2) - estoque_atual
    - Ordena por classe ABC e déficit de estoque

    Retorna:
    - Lista de produtos sugeridos
    - Quantidade sugerida para cada produto
    - Valor total da sugestão
    """
    service = ComprasService(db)
    return await service.sugerir_compras()


@router.get(
    "/atrasados/",
    response_model=PedidoCompraList,
    summary="Listar pedidos atrasados",
    description="Lista pedidos com data de entrega prevista vencida e ainda não recebidos",
)
async def listar_atrasados(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Tamanho da página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista pedidos atrasados

    - **page**: Número da página (padrão: 1)
    - **page_size**: Tamanho da página (padrão: 50, máximo: 100)

    Critério de atraso:
    - data_entrega_prevista < hoje
    - Status diferente de RECEBIDO e CANCELADO
    """
    service = ComprasService(db)
    return await service.get_pedidos_atrasados(page, page_size)
