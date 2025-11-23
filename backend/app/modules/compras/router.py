"""
Router para endpoints de Compras
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.compras.service import ComprasService
from app.modules.compras.fornecedor_analise_service import FornecedorAnaliseService
from app.modules.compras.schemas import (
    PedidoCompraCreate,
    PedidoCompraUpdate,
    PedidoCompraResponse,
    PedidoCompraList,
    ReceberPedidoRequest,
    SugestaoCompraList,
)

router = APIRouter()


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
    status_code=status.HTTP_204_NO_CONTENT,
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
    await service.cancelar_pedido(pedido_id)
    return None


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


# Endpoints de Análise de Fornecedores


@router.get(
    "/analise/fornecedor/{fornecedor_id}",
    summary="Analisar desempenho de fornecedor",
    description="Analisa o desempenho de um fornecedor baseado em pedidos realizados",
)
async def analisar_fornecedor(
    fornecedor_id: int,
    periodo_dias: int = Query(
        180, ge=30, le=730, description="Período de análise em dias (30-730)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Analisa o desempenho de um fornecedor

    Métricas analisadas:
    - Total de pedidos no período
    - Valor total comprado
    - Ticket médio
    - Taxa de entrega no prazo (%)
    - Média de dias de atraso
    - Taxa de recebimento completo (%)
    - Classificação (EXCELENTE, BOM, REGULAR, RUIM)

    Critérios de classificação:
    - EXCELENTE: >90% prazo, <2 dias atraso, >95% completo
    - BOM: >75% prazo, <5 dias atraso, >85% completo
    - REGULAR: >60% prazo, <10 dias atraso, >70% completo
    - RUIM: abaixo dos critérios acima
    """
    service = FornecedorAnaliseService(db)
    return await service.analisar_desempenho_fornecedor(fornecedor_id, periodo_dias)


@router.get(
    "/analise/ranking",
    summary="Ranking de fornecedores",
    description="Ranking de fornecedores por desempenho",
)
async def ranking_fornecedores(
    periodo_dias: int = Query(
        180, ge=30, le=730, description="Período de análise em dias (30-730)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Gera ranking de fornecedores por desempenho

    - Ordena fornecedores por classificação e taxa de entrega
    - Apenas fornecedores ativos com pedidos no período
    - Útil para decisões de compra e negociação
    """
    service = FornecedorAnaliseService(db)
    return await service.ranking_fornecedores(periodo_dias)


@router.post(
    "/analise/comparar",
    summary="Comparar fornecedores",
    description="Compara o desempenho de múltiplos fornecedores",
)
async def comparar_fornecedores(
    fornecedor_ids: list[int],
    periodo_dias: int = Query(
        180, ge=30, le=730, description="Período de análise em dias (30-730)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Compara o desempenho de múltiplos fornecedores

    - Fornece análise lado a lado
    - Útil para decisão entre fornecedores
    - Retorna métricas completas para cada fornecedor
    """
    service = FornecedorAnaliseService(db)
    return await service.comparar_fornecedores(fornecedor_ids, periodo_dias)


# ========== ROTAS ALTERNATIVAS PARA COMPATIBILIDADE COM TESTES ==========


@router.post(
    "/{pedido_id}/cancelar",
    response_model=PedidoCompraResponse,
    summary="Cancelar pedido de compra (POST)",
    description="Cancela um pedido de compra via POST (alternativa ao DELETE)",
)
async def cancelar_pedido_post(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancela um pedido de compra (rota alternativa POST)

    - **pedido_id**: ID do pedido
    - Não pode cancelar pedido recebido (total ou parcial)
    """
    service = ComprasService(db)
    return await service.cancelar_pedido(pedido_id)


@router.get(
    "/sugestoes",
    response_model=SugestaoCompraList,
    summary="Sugestão de compras (rota alternativa)",
    description="Gera lista de produtos sugeridos para compra (rota alternativa)",
)
async def sugestoes_compras_alt(
    db: AsyncSession = Depends(get_db),
):
    """
    Gera sugestão automática de compras (rota alternativa /sugestoes)

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
