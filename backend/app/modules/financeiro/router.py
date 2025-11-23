"""
Router para endpoints de Financeiro
"""
from datetime import date
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.financeiro.service import FinanceiroService
from app.modules.financeiro.schemas import (
    ContaPagarCreate,
    ContaPagarUpdate,
    ContaPagarResponse,
    ContaPagarList,
    ContaReceberCreate,
    ContaReceberUpdate,
    ContaReceberResponse,
    ContaReceberList,
    BaixaPagamentoCreate,
    BaixaRecebimentoCreate,
    FluxoCaixaResponse,
    FluxoCaixaPeriodoResponse,
)

router = APIRouter()


# ============================================
# ENDPOINTS DE CONTAS A PAGAR
# ============================================

@router.post(
    "/contas-pagar",
    response_model=ContaPagarResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar conta a pagar",
    description="Cria uma nova conta a pagar no sistema",
)
async def create_conta_pagar(
    conta_data: ContaPagarCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova conta a pagar.

    **Validações:**
    - Data de vencimento não pode ser anterior à emissão
    - Valor original deve ser positivo

    **Exemplo de requisição:**
    ```json
    {
        "fornecedor_id": 1,
        "descricao": "Compra de material de construção",
        "valor_original": 1500.00,
        "data_emissao": "2025-11-19",
        "data_vencimento": "2025-12-19",
        "documento": "NF-12345",
        "categoria_financeira": "COMPRAS",
        "observacoes": "Pagamento em 30 dias"
    }
    ```
    """
    service = FinanceiroService(db)
    return await service.criar_conta_pagar(conta_data)


@router.get(
    "/contas-pagar/{conta_id}",
    response_model=ContaPagarResponse,
    summary="Buscar conta a pagar por ID",
    description="Retorna os dados de uma conta a pagar específica",
)
async def get_conta_pagar(conta_id: int, db: AsyncSession = Depends(get_db)):
    """Busca uma conta a pagar por ID"""
    service = FinanceiroService(db)
    return await service.get_conta_pagar(conta_id)


@router.get(
    "/contas-pagar",
    response_model=ContaPagarList,
    summary="Listar contas a pagar",
    description="Lista todas as contas a pagar com paginação e filtros",
)
async def list_contas_pagar(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    fornecedor_id: int = Query(None, description="Filtrar por fornecedor"),
    status: str = Query(None, description="Filtrar por status"),
    categoria: str = Query(None, description="Filtrar por categoria financeira"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista contas a pagar com paginação e filtros.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **fornecedor_id**: Se fornecido, filtra por fornecedor
    - **status**: Se fornecido, filtra por status (PENDENTE, PAGA, ATRASADA, CANCELADA)
    - **categoria**: Se fornecido, filtra por categoria financeira
    """
    service = FinanceiroService(db)
    return await service.list_contas_pagar(page, page_size, fornecedor_id, status, categoria)


@router.put(
    "/contas-pagar/{conta_id}",
    response_model=ContaPagarResponse,
    summary="Atualizar conta a pagar",
    description="Atualiza os dados de uma conta a pagar",
)
async def update_conta_pagar(
    conta_id: int,
    conta_data: ContaPagarUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza uma conta a pagar existente.

    **Regras:**
    - Não pode atualizar conta já paga ou cancelada

    **Exemplo de requisição:**
    ```json
    {
        "descricao": "Compra de material - Atualizado",
        "observacoes": "Negociado desconto de 5%"
    }
    ```
    """
    service = FinanceiroService(db)
    return await service.update_conta_pagar(conta_id, conta_data)


@router.post(
    "/contas-pagar/{conta_id}/baixar",
    response_model=ContaPagarResponse,
    summary="Baixar pagamento",
    description="Registra pagamento (total ou parcial) de conta a pagar",
)
async def baixar_pagamento(
    conta_id: int,
    baixa_data: BaixaPagamentoCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra pagamento de conta a pagar.

    **Regras:**
    - Permite pagamento parcial
    - Valor total pago não pode exceder valor original
    - Status é atualizado automaticamente para PAGA quando valor_pago >= valor_original
    - Não pode pagar conta cancelada

    **Exemplo de requisição:**
    ```json
    {
        "valor_pago": 750.00,
        "data_pagamento": "2025-12-15",
        "observacoes": "Pagamento parcial - 1ª parcela"
    }
    ```
    """
    service = FinanceiroService(db)
    return await service.baixar_pagamento(conta_id, baixa_data)


@router.delete(
    "/contas-pagar/{conta_id}",
    response_model=ContaPagarResponse,
    summary="Cancelar conta a pagar",
    description="Cancela uma conta a pagar",
)
async def cancelar_conta_pagar(conta_id: int, db: AsyncSession = Depends(get_db)):
    """
    Cancela uma conta a pagar.

    **Regras:**
    - Não pode cancelar conta já paga
    - Status é atualizado para CANCELADA
    """
    service = FinanceiroService(db)
    return await service.cancelar_conta_pagar(conta_id)


@router.get(
    "/contas-pagar/pendentes",
    response_model=ContaPagarList,
    summary="Listar contas a pagar pendentes",
    description="Lista apenas contas a pagar com status PENDENTE",
)
async def get_contas_pagar_pendentes(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """Lista contas a pagar pendentes"""
    service = FinanceiroService(db)
    return await service.get_contas_pagar_pendentes(page, page_size)


@router.get(
    "/contas-pagar/vencidas",
    response_model=ContaPagarList,
    summary="Listar contas a pagar vencidas",
    description="Lista contas a pagar vencidas (vencimento < hoje e status PENDENTE ou ATRASADA)",
)
async def get_contas_pagar_vencidas(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista contas a pagar vencidas.

    **Critérios:**
    - Data de vencimento menor que hoje
    - Status PENDENTE ou ATRASADA
    - Status é automaticamente atualizado para ATRASADA
    """
    service = FinanceiroService(db)
    return await service.get_contas_pagar_vencidas(page, page_size)


# ============================================
# ENDPOINTS DE CONTAS A RECEBER
# ============================================

@router.post(
    "/contas-receber",
    response_model=ContaReceberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar conta a receber",
    description="Cria uma nova conta a receber no sistema",
)
async def create_conta_receber(
    conta_data: ContaReceberCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova conta a receber.

    **Validações:**
    - Data de vencimento não pode ser anterior à emissão
    - Valor original deve ser positivo
    - Pode ser vinculada a uma venda (opcional)

    **Exemplo de requisição:**
    ```json
    {
        "cliente_id": 1,
        "venda_id": 123,
        "descricao": "Venda de material - Pedido #123",
        "valor_original": 2500.00,
        "data_emissao": "2025-11-19",
        "data_vencimento": "2025-12-19",
        "documento": "DUPLICATA-001",
        "categoria_financeira": "VENDAS",
        "observacoes": "Recebimento em 30 dias"
    }
    ```
    """
    service = FinanceiroService(db)
    return await service.criar_conta_receber(conta_data)


@router.get(
    "/contas-receber/{conta_id}",
    response_model=ContaReceberResponse,
    summary="Buscar conta a receber por ID",
    description="Retorna os dados de uma conta a receber específica",
)
async def get_conta_receber(conta_id: int, db: AsyncSession = Depends(get_db)):
    """Busca uma conta a receber por ID"""
    service = FinanceiroService(db)
    return await service.get_conta_receber(conta_id)


@router.get(
    "/contas-receber",
    response_model=ContaReceberList,
    summary="Listar contas a receber",
    description="Lista todas as contas a receber com paginação e filtros",
)
async def list_contas_receber(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    cliente_id: int = Query(None, description="Filtrar por cliente"),
    status: str = Query(None, description="Filtrar por status"),
    categoria: str = Query(None, description="Filtrar por categoria financeira"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista contas a receber com paginação e filtros.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **cliente_id**: Se fornecido, filtra por cliente
    - **status**: Se fornecido, filtra por status (PENDENTE, RECEBIDA, ATRASADA, CANCELADA)
    - **categoria**: Se fornecido, filtra por categoria financeira
    """
    service = FinanceiroService(db)
    return await service.list_contas_receber(page, page_size, cliente_id, status, categoria)


@router.put(
    "/contas-receber/{conta_id}",
    response_model=ContaReceberResponse,
    summary="Atualizar conta a receber",
    description="Atualiza os dados de uma conta a receber",
)
async def update_conta_receber(
    conta_id: int,
    conta_data: ContaReceberUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza uma conta a receber existente.

    **Regras:**
    - Não pode atualizar conta já recebida ou cancelada

    **Exemplo de requisição:**
    ```json
    {
        "descricao": "Venda de material - Atualizado",
        "observacoes": "Cliente solicitou extensão de prazo"
    }
    ```
    """
    service = FinanceiroService(db)
    return await service.update_conta_receber(conta_id, conta_data)


@router.post(
    "/contas-receber/{conta_id}/baixar",
    response_model=ContaReceberResponse,
    summary="Baixar recebimento",
    description="Registra recebimento (total ou parcial) de conta a receber",
)
async def baixar_recebimento(
    conta_id: int,
    baixa_data: BaixaRecebimentoCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra recebimento de conta a receber.

    **Regras:**
    - Permite recebimento parcial
    - Valor total recebido não pode exceder valor original
    - Status é atualizado automaticamente para RECEBIDA quando valor_recebido >= valor_original
    - Não pode receber conta cancelada

    **Exemplo de requisição:**
    ```json
    {
        "valor_recebido": 1250.00,
        "data_recebimento": "2025-12-15",
        "observacoes": "Recebimento parcial - 1ª parcela"
    }
    ```
    """
    service = FinanceiroService(db)
    return await service.baixar_recebimento(conta_id, baixa_data)


@router.delete(
    "/contas-receber/{conta_id}",
    response_model=ContaReceberResponse,
    summary="Cancelar conta a receber",
    description="Cancela uma conta a receber",
)
async def cancelar_conta_receber(conta_id: int, db: AsyncSession = Depends(get_db)):
    """
    Cancela uma conta a receber.

    **Regras:**
    - Não pode cancelar conta já recebida
    - Status é atualizado para CANCELADA
    """
    service = FinanceiroService(db)
    return await service.cancelar_conta_receber(conta_id)


@router.get(
    "/contas-receber/pendentes",
    response_model=ContaReceberList,
    summary="Listar contas a receber pendentes",
    description="Lista apenas contas a receber com status PENDENTE",
)
async def get_contas_receber_pendentes(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """Lista contas a receber pendentes"""
    service = FinanceiroService(db)
    return await service.get_contas_receber_pendentes(page, page_size)


@router.get(
    "/contas-receber/vencidas",
    response_model=ContaReceberList,
    summary="Listar contas a receber vencidas",
    description="Lista contas a receber vencidas (vencimento < hoje e status PENDENTE ou ATRASADA)",
)
async def get_contas_receber_vencidas(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista contas a receber vencidas.

    **Critérios:**
    - Data de vencimento menor que hoje
    - Status PENDENTE ou ATRASADA
    - Status é automaticamente atualizado para ATRASADA
    """
    service = FinanceiroService(db)
    return await service.get_contas_receber_vencidas(page, page_size)


# ============================================
# ENDPOINTS DE FLUXO DE CAIXA
# ============================================

@router.get(
    "/fluxo-caixa",
    response_model=FluxoCaixaResponse,
    summary="Resumo do fluxo de caixa",
    description="Retorna resumo consolidado do fluxo de caixa",
)
async def get_fluxo_caixa(db: AsyncSession = Depends(get_db)):
    """
    Retorna resumo do fluxo de caixa.

    **Inclui:**
    - Total a pagar (contas pendentes)
    - Total a receber (contas pendentes)
    - Saldo projetado (a receber - a pagar)
    - Total já pago
    - Total já recebido
    - Quantidade de contas vencidas (a pagar e a receber)
    - Valor total vencido (a pagar e a receber)

    **Útil para:**
    - Dashboard financeiro
    - Visão geral da situação financeira
    - Alertas de contas vencidas
    """
    service = FinanceiroService(db)
    return await service.get_fluxo_caixa()


@router.get(
    "/fluxo-caixa/periodo",
    response_model=FluxoCaixaPeriodoResponse,
    summary="Fluxo de caixa por período",
    description="Retorna fluxo de caixa detalhado de um período específico",
)
async def get_fluxo_periodo(
    data_inicio: date = Query(..., description="Data de início do período"),
    data_fim: date = Query(..., description="Data de fim do período"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna fluxo de caixa por período.

    **Parâmetros:**
    - **data_inicio**: Data de início do período (formato: YYYY-MM-DD)
    - **data_fim**: Data de fim do período (formato: YYYY-MM-DD)

    **Retorna:**
    - Todas as contas a pagar do período
    - Todas as contas a receber do período
    - Totais calculados (a pagar, a receber, pago, recebido)
    - Saldo do período

    **Exemplo:**
    - `/fluxo-caixa/periodo?data_inicio=2025-11-01&data_fim=2025-11-30`

    **Útil para:**
    - Relatórios mensais
    - Análise de períodos específicos
    - Planejamento financeiro
    """
    service = FinanceiroService(db)
    return await service.get_fluxo_periodo(data_inicio, data_fim)
