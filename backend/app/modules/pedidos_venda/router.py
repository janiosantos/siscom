"""
Router para endpoints de Pedidos de Venda
"""
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.pedidos_venda.service import PedidoVendaService
from app.modules.pedidos_venda.models import StatusPedidoVenda
from app.modules.pedidos_venda.schemas import (
    PedidoVendaCreate,
    PedidoVendaUpdate,
    PedidoVendaResponse,
    PedidoVendaListResponse,
    ConfirmarPedidoRequest,
    SepararPedidoRequest,
    FaturarPedidoRequest,
    CancelarPedidoRequest,
    RelatorioPedidosResponse,
)

router = APIRouter()


@router.post(
    "/",
    response_model=PedidoVendaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo pedido de venda",
    description="Cria um novo pedido de venda completo com itens",
)
async def criar_pedido(
    pedido_data: PedidoVendaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cria um novo pedido de venda completo com itens.

    **Regras:**
    - Valida se todos os produtos existem e estão ativos
    - Pode ser criado a partir de um orçamento aprovado
    - Calcula totais automaticamente
    - NÃO mexe em estoque (reserva apenas na separação)
    - Cria o pedido com status RASCUNHO
    - Gera número sequencial (PV000001)

    **Exemplo de requisição:**
    ```json
    {
        "cliente_id": 1,
        "orcamento_id": null,
        "data_entrega_prevista": "2025-12-01",
        "tipo_entrega": "ENTREGA",
        "endereco_entrega": "Rua X, 123",
        "desconto": 5.00,
        "valor_frete": 15.00,
        "outras_despesas": 0.0,
        "condicao_pagamento_id": 1,
        "forma_pagamento": "CARTAO_CREDITO",
        "observacoes": "Cliente preferencial",
        "itens": [
            {
                "produto_id": 1,
                "quantidade": 2.0,
                "preco_unitario": 32.90,
                "desconto_item": 0.0,
                "observacao_item": null
            }
        ]
    }
    ```

    **Resposta:**
    - Status RASCUNHO criado
    - Número do pedido gerado automaticamente
    - Subtotal e valor_total calculados
    """
    service = PedidoVendaService(db)
    return await service.criar_pedido(pedido_data, current_user.id)


@router.get(
    "/{pedido_id}",
    response_model=PedidoVendaResponse,
    summary="Buscar pedido por ID",
    description="Retorna os dados completos de um pedido com seus itens",
)
async def get_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Busca um pedido por ID com todos os seus itens"""
    service = PedidoVendaService(db)
    return await service.get_pedido(pedido_id)


@router.get(
    "/",
    response_model=List[PedidoVendaResponse],
    summary="Listar pedidos de venda",
    description="Lista todos os pedidos com filtros",
)
async def list_pedidos(
    skip: int = Query(0, ge=0, description="Offset para paginação"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados"),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    vendedor_id: Optional[int] = Query(None, description="Filtrar por vendedor"),
    status: Optional[StatusPedidoVenda] = Query(
        None, description="Filtrar por status"
    ),
    data_inicio: Optional[date] = Query(None, description="Data inicial"),
    data_fim: Optional[date] = Query(None, description="Data final"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lista pedidos com filtros.

    **Parâmetros:**
    - **skip**: Offset para paginação (padrão: 0)
    - **limit**: Limite de resultados (padrão: 100, máximo: 1000)
    - **cliente_id**: Filtrar por cliente
    - **vendedor_id**: Filtrar por vendedor
    - **status**: Filtrar por status (RASCUNHO, CONFIRMADO, etc.)
    - **data_inicio**: Data inicial do filtro
    - **data_fim**: Data final do filtro
    """
    service = PedidoVendaService(db)
    return await service.list_pedidos(
        skip=skip,
        limit=limit,
        cliente_id=cliente_id,
        vendedor_id=vendedor_id,
        status=status,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@router.put(
    "/{pedido_id}",
    response_model=PedidoVendaResponse,
    summary="Atualizar pedido de venda",
    description="Atualiza um pedido (apenas se status = RASCUNHO)",
)
async def atualizar_pedido(
    pedido_id: int,
    pedido_data: PedidoVendaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza um pedido de venda.

    **Regras:**
    - Só pode editar pedidos com status RASCUNHO
    - Recalcula valor_total automaticamente se houver mudanças

    **Exemplo de requisição:**
    ```json
    {
        "desconto": 10.00,
        "valor_frete": 20.00,
        "observacoes": "Atualização de valores"
    }
    ```
    """
    service = PedidoVendaService(db)
    return await service.atualizar_pedido(pedido_id, pedido_data)


@router.post(
    "/{pedido_id}/confirmar",
    response_model=PedidoVendaResponse,
    summary="Confirmar pedido",
    description="Confirma um pedido (RASCUNHO → CONFIRMADO)",
)
async def confirmar_pedido(
    pedido_id: int,
    request: ConfirmarPedidoRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirma um pedido (RASCUNHO → CONFIRMADO).

    **Regras:**
    - Pedido deve estar RASCUNHO
    - Altera status para CONFIRMADO

    **Exemplo de requisição:**
    ```json
    {
        "observacao": "Pedido confirmado pelo cliente via telefone"
    }
    ```
    """
    service = PedidoVendaService(db)
    return await service.confirmar_pedido(pedido_id, request, current_user.id)


@router.post(
    "/{pedido_id}/iniciar-separacao",
    response_model=PedidoVendaResponse,
    summary="Iniciar separação",
    description="Inicia separação de produtos (CONFIRMADO → EM_SEPARACAO)",
)
async def iniciar_separacao(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia separação de produtos (CONFIRMADO → EM_SEPARACAO).

    **Regras:**
    - Pedido deve estar CONFIRMADO
    - Registra usuário que está fazendo a separação
    """
    service = PedidoVendaService(db)
    return await service.iniciar_separacao(pedido_id, current_user.id)


@router.post(
    "/{pedido_id}/separar",
    response_model=PedidoVendaResponse,
    summary="Marcar como separado",
    description="Marca pedido como separado (EM_SEPARACAO → SEPARADO)",
)
async def separar_pedido(
    pedido_id: int,
    request: SepararPedidoRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Marca pedido como separado (EM_SEPARACAO → SEPARADO).

    Registra quantidade separada para cada item.

    **Regras:**
    - Pedido deve estar EM_SEPARACAO
    - Registra data de separação

    **Exemplo de requisição:**
    ```json
    {
        "itens_separados": [
            {"produto_id": 1, "quantidade_separada": 2.0},
            {"produto_id": 2, "quantidade_separada": 1.0}
        ]
    }
    ```
    """
    service = PedidoVendaService(db)
    return await service.separar_pedido(pedido_id, request, current_user.id)


@router.post(
    "/{pedido_id}/enviar-entrega",
    response_model=PedidoVendaResponse,
    summary="Enviar para entrega",
    description="Marca pedido como em entrega (SEPARADO → EM_ENTREGA)",
)
async def enviar_para_entrega(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Marca pedido como em entrega (SEPARADO → EM_ENTREGA).

    **Regras:**
    - Pedido deve estar SEPARADO
    """
    service = PedidoVendaService(db)
    return await service.enviar_para_entrega(pedido_id, current_user.id)


@router.post(
    "/{pedido_id}/confirmar-entrega",
    response_model=PedidoVendaResponse,
    summary="Confirmar entrega",
    description="Confirma entrega (EM_ENTREGA → ENTREGUE)",
)
async def confirmar_entrega(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Confirma entrega (EM_ENTREGA → ENTREGUE).

    **Regras:**
    - Pedido deve estar EM_ENTREGA
    - Registra data_entrega_real
    """
    service = PedidoVendaService(db)
    return await service.confirmar_entrega(pedido_id, current_user.id)


@router.post(
    "/{pedido_id}/faturar",
    response_model=dict,
    summary="Faturar pedido",
    description="Fatura pedido criando venda (ENTREGUE → FATURADO)",
)
async def faturar_pedido(
    pedido_id: int,
    request: FaturarPedidoRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fatura pedido criando venda (ENTREGUE → FATURADO).

    **Regras:**
    - Pedido deve estar ENTREGUE
    - Cria Venda através de VendasService
    - VendasService já valida estoque e cria saídas
    - Opcionalmente gera NF-e

    **Exemplo de requisição:**
    ```json
    {
        "gerar_nfe": true,
        "observacao": "Faturamento conforme solicitado"
    }
    ```

    **Resposta:**
    ```json
    {
        "pedido": {...},
        "venda": {...}
    }
    ```
    """
    service = PedidoVendaService(db)
    return await service.faturar_pedido(pedido_id, request, current_user.id)


@router.post(
    "/{pedido_id}/cancelar",
    response_model=PedidoVendaResponse,
    summary="Cancelar pedido",
    description="Cancela um pedido (qualquer status → CANCELADO)",
)
async def cancelar_pedido(
    pedido_id: int,
    request: CancelarPedidoRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancela um pedido (qualquer status → CANCELADO).

    **Regras:**
    - Pedidos FATURADOS não podem ser cancelados
    - Registra motivo nas observações internas

    **Exemplo de requisição:**
    ```json
    {
        "motivo": "Cliente desistiu da compra"
    }
    ```
    """
    service = PedidoVendaService(db)
    return await service.cancelar_pedido(pedido_id, request, current_user.id)


@router.get(
    "/relatorios/atrasados",
    response_model=List[PedidoVendaResponse],
    summary="Pedidos atrasados",
    description="Lista pedidos com data_entrega_prevista vencida",
)
async def get_pedidos_atrasados(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Busca pedidos atrasados (data_entrega_prevista vencida e não entregues).

    **Retorna:**
    - Pedidos com status: CONFIRMADO, EM_SEPARACAO, SEPARADO, EM_ENTREGA
    - Que tenham data_entrega_prevista menor que hoje
    """
    service = PedidoVendaService(db)
    return await service.get_pedidos_atrasados()


@router.get(
    "/relatorios/estatisticas",
    response_model=RelatorioPedidosResponse,
    summary="Relatório de pedidos",
    description="Gera relatório estatístico de pedidos",
)
async def get_relatorio_pedidos(
    data_inicio: Optional[date] = Query(None, description="Data inicial"),
    data_fim: Optional[date] = Query(None, description="Data final"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Gera relatório de pedidos com estatísticas.

    **Parâmetros:**
    - **data_inicio**: Data inicial (opcional)
    - **data_fim**: Data final (opcional)

    **Retorna:**
    - Total de pedidos
    - Total de valor
    - Pedidos por status
    - Pedidos atrasados
    - Ticket médio
    """
    service = PedidoVendaService(db)
    return await service.get_relatorio_pedidos(data_inicio, data_fim)
