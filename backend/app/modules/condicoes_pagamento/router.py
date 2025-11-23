"""
Router para endpoints de Condicoes de Pagamento
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.modules.condicoes_pagamento.service import CondicaoPagamentoService
from app.modules.condicoes_pagamento.schemas import (
    CondicaoPagamentoCreate,
    CondicaoPagamentoUpdate,
    CondicaoPagamentoResponse,
    CondicaoPagamentoList,
    CalcularParcelasRequest,
    CalcularParcelasResponse,
)

router = APIRouter()


@router.post(
    "/",
    response_model=CondicaoPagamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova condição de pagamento",
    description="Cria uma nova condição de pagamento com suas parcelas padrão",
)
async def create_condicao(
    condicao_data: CondicaoPagamentoCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova condição de pagamento.

    **Validações:**
    - Nome único
    - Quantidade de parcelas >= 1
    - Soma de percentuais das parcelas = 100%
    - Para AVISTA: 1 parcela, 0 dias
    - Para PRAZO: 1+ parcelas
    - Para PARCELADO: 2+ parcelas

    **Exemplo de requisição - À Vista:**
    ```json
    {
        "nome": "À Vista",
        "descricao": "Pagamento à vista",
        "tipo": "AVISTA",
        "quantidade_parcelas": 1,
        "intervalo_dias": 0,
        "entrada_percentual": 0,
        "ativa": true,
        "parcelas": [
            {
                "numero_parcela": 1,
                "dias_vencimento": 0,
                "percentual_valor": 100.0
            }
        ]
    }
    ```

    **Exemplo de requisição - 30/60/90:**
    ```json
    {
        "nome": "30/60/90",
        "descricao": "3 parcelas - 30, 60 e 90 dias",
        "tipo": "PARCELADO",
        "quantidade_parcelas": 3,
        "intervalo_dias": 30,
        "entrada_percentual": 0,
        "ativa": true,
        "parcelas": [
            {
                "numero_parcela": 1,
                "dias_vencimento": 30,
                "percentual_valor": 33.33
            },
            {
                "numero_parcela": 2,
                "dias_vencimento": 60,
                "percentual_valor": 33.33
            },
            {
                "numero_parcela": 3,
                "dias_vencimento": 90,
                "percentual_valor": 33.34
            }
        ]
    }
    ```

    **Exemplo de requisição - 50% entrada + 30/60:**
    ```json
    {
        "nome": "50% + 30/60",
        "descricao": "50% de entrada + 2 parcelas (30 e 60 dias)",
        "tipo": "PARCELADO",
        "quantidade_parcelas": 3,
        "intervalo_dias": 30,
        "entrada_percentual": 50,
        "ativa": true,
        "parcelas": [
            {
                "numero_parcela": 1,
                "dias_vencimento": 0,
                "percentual_valor": 50.0
            },
            {
                "numero_parcela": 2,
                "dias_vencimento": 30,
                "percentual_valor": 25.0
            },
            {
                "numero_parcela": 3,
                "dias_vencimento": 60,
                "percentual_valor": 25.0
            }
        ]
    }
    ```
    """
    service = CondicaoPagamentoService(db)
    return await service.criar_condicao(condicao_data)


@router.get(
    "/{condicao_id}",
    response_model=CondicaoPagamentoResponse,
    summary="Buscar condição de pagamento por ID",
    description="Retorna os dados de uma condição de pagamento específica com suas parcelas",
)
async def get_condicao(condicao_id: int, db: AsyncSession = Depends(get_db)):
    """Busca uma condição de pagamento por ID"""
    service = CondicaoPagamentoService(db)
    return await service.buscar_condicao(condicao_id)


@router.get(
    "/",
    response_model=CondicaoPagamentoList,
    summary="Listar condições de pagamento",
    description="Lista todas as condições de pagamento com paginação e filtros",
)
async def list_condicoes(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    apenas_ativas: bool = Query(False, description="Listar apenas condições ativas"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista condições de pagamento com paginação e filtros.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **apenas_ativas**: Se True, lista apenas condições ativas
    """
    service = CondicaoPagamentoService(db)
    return await service.listar_condicoes(page, page_size, apenas_ativas)


@router.get(
    "/ativas/list",
    response_model=List[CondicaoPagamentoResponse],
    summary="Listar apenas condições ativas",
    description="Retorna lista de todas as condições de pagamento ativas (sem paginação)",
)
async def get_condicoes_ativas(db: AsyncSession = Depends(get_db)):
    """
    Retorna todas as condições de pagamento ativas.

    **Útil para:**
    - Dropdowns/selects em formulários
    - Seleção de condição ao criar venda/pedido
    """
    service = CondicaoPagamentoService(db)
    return await service.get_condicoes_ativas()


@router.put(
    "/{condicao_id}",
    response_model=CondicaoPagamentoResponse,
    summary="Atualizar condição de pagamento",
    description="Atualiza os dados de uma condição de pagamento",
)
async def update_condicao(
    condicao_id: int,
    condicao_data: CondicaoPagamentoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza uma condição de pagamento existente.

    **Validações:**
    - Se alterar nome, deve ser único
    - Se alterar parcelas, soma de percentuais deve ser 100%

    **Exemplo de requisição - Atualizar nome e descrição:**
    ```json
    {
        "nome": "À Vista com Desconto",
        "descricao": "Pagamento à vista com desconto de 5%"
    }
    ```

    **Exemplo de requisição - Atualizar parcelas:**
    ```json
    {
        "parcelas": [
            {
                "numero_parcela": 1,
                "dias_vencimento": 30,
                "percentual_valor": 50.0
            },
            {
                "numero_parcela": 2,
                "dias_vencimento": 60,
                "percentual_valor": 50.0
            }
        ]
    }
    ```
    """
    service = CondicaoPagamentoService(db)
    return await service.atualizar_condicao(condicao_id, condicao_data)


@router.delete(
    "/{condicao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Inativar condição de pagamento",
    description="Inativa uma condição de pagamento (soft delete)",
)
async def delete_condicao(condicao_id: int, db: AsyncSession = Depends(get_db)):
    """
    Inativa uma condição de pagamento (soft delete).
    A condição não é removida do banco, apenas marcada como inativa.
    """
    service = CondicaoPagamentoService(db)
    await service.delete_condicao(condicao_id)
    return None


@router.post(
    "/calcular/parcelas",
    response_model=CalcularParcelasResponse,
    summary="Calcular parcelas para um valor",
    description="Calcula as parcelas (valor e vencimento) para um valor total específico",
)
async def calcular_parcelas(
    request: CalcularParcelasRequest, db: AsyncSession = Depends(get_db)
):
    """
    Calcula as parcelas para um valor total específico.

    **Útil para:**
    - Simular parcelas antes de finalizar venda
    - Mostrar ao cliente como ficará o parcelamento
    - Gerar parcelas do contas a receber

    **Exemplo de requisição:**
    ```json
    {
        "condicao_id": 1,
        "valor_total": 1000.00,
        "data_base": "2025-01-15"
    }
    ```

    **Exemplo de resposta:**
    ```json
    {
        "condicao": {
            "id": 1,
            "nome": "30/60/90",
            "tipo": "PARCELADO",
            ...
        },
        "valor_total": 1000.00,
        "parcelas": [
            {
                "numero_parcela": 1,
                "valor": 333.33,
                "vencimento": "2025-02-14",
                "percentual": 33.33
            },
            {
                "numero_parcela": 2,
                "valor": 333.33,
                "vencimento": "2025-03-16",
                "percentual": 33.33
            },
            {
                "numero_parcela": 3,
                "valor": 333.34,
                "vencimento": "2025-04-15",
                "percentual": 33.34
            }
        ]
    }
    ```

    **Observações:**
    - A data_base é opcional (padrão: hoje)
    - O sistema ajusta arredondamentos para garantir que soma = valor_total
    - A diferença de arredondamento é adicionada na última parcela
    """
    service = CondicaoPagamentoService(db)
    return await service.calcular_parcelas_venda(request)


# ========== ROTA ALTERNATIVA PARA COMPATIBILIDADE COM TESTES ==========


@router.post(
    "/calcular-parcelas",
    response_model=CalcularParcelasResponse,
    summary="Calcular parcelas (rota alternativa)",
    description="Calcula as parcelas para um valor total (rota alternativa com hífen)",
)
async def calcular_parcelas_alt(
    request: CalcularParcelasRequest, db: AsyncSession = Depends(get_db)
):
    """
    Calcula as parcelas para um valor total específico (rota alternativa).

    Esta é uma rota alternativa a /calcular/parcelas para compatibilidade com testes.
    """
    service = CondicaoPagamentoService(db)
    return await service.calcular_parcelas_venda(request)
