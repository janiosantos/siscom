"""
Router para endpoints de Orçamentos
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.orcamentos.service import OrcamentosService
from app.modules.orcamentos.schemas import (
    OrcamentoCreate,
    OrcamentoUpdate,
    OrcamentoResponse,
    OrcamentoList,
    StatusOrcamentoEnum,
    ConverterOrcamentoRequest,
)

router = APIRouter()


@router.post(
    "/",
    response_model=OrcamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo orçamento",
    description="Cria um novo orçamento completo com itens",
)
async def create_orcamento(
    orcamento_data: OrcamentoCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo orçamento completo com itens.

    **Regras:**
    - Valida se todos os produtos existem e estão ativos
    - Calcula data_validade automaticamente (data_orcamento + validade_dias)
    - Calcula totais automaticamente
    - NÃO mexe em estoque (orçamento é apenas informacional)
    - Cria o orçamento com status ABERTO

    **Exemplo de requisição:**
    ```json
    {
        "cliente_id": 1,
        "vendedor_id": 1,
        "validade_dias": 15,
        "desconto": 10.00,
        "observacoes": "Orçamento para reforma",
        "itens": [
            {
                "produto_id": 1,
                "quantidade": 5.0,
                "preco_unitario": 32.90,
                "desconto_item": 0.0,
                "observacao_item": "Material de qualidade"
            },
            {
                "produto_id": 2,
                "quantidade": 2.0,
                "preco_unitario": 15.50,
                "desconto_item": 1.00,
                "observacao_item": null
            }
        ]
    }
    ```
    """
    service = OrcamentosService(db)
    return await service.criar_orcamento(orcamento_data)


@router.get(
    "/{orcamento_id}",
    response_model=OrcamentoResponse,
    summary="Buscar orçamento por ID",
    description="Retorna os dados completos de um orçamento com seus itens",
)
async def get_orcamento(orcamento_id: int, db: AsyncSession = Depends(get_db)):
    """Busca um orçamento por ID com todos os seus itens"""
    service = OrcamentosService(db)
    return await service.get_orcamento(orcamento_id)


@router.get(
    "/",
    response_model=OrcamentoList,
    summary="Listar orçamentos",
    description="Lista todos os orçamentos com paginação e filtros",
)
async def list_orcamentos(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    status: Optional[StatusOrcamentoEnum] = Query(None, description="Filtrar por status"),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    vendedor_id: Optional[int] = Query(None, description="Filtrar por vendedor"),
    data_inicio: Optional[datetime] = Query(None, description="Data inicial"),
    data_fim: Optional[datetime] = Query(None, description="Data final"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista orçamentos com paginação e filtros.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **status**: Filtrar por status (ABERTO, APROVADO, PERDIDO, CONVERTIDO)
    - **cliente_id**: Filtrar por cliente
    - **vendedor_id**: Filtrar por vendedor
    - **data_inicio**: Data inicial do filtro
    - **data_fim**: Data final do filtro
    """
    service = OrcamentosService(db)
    return await service.list_orcamentos(
        page=page,
        page_size=page_size,
        status=status,
        cliente_id=cliente_id,
        vendedor_id=vendedor_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@router.put(
    "/{orcamento_id}",
    response_model=OrcamentoResponse,
    summary="Atualizar orçamento",
    description="Atualiza um orçamento (apenas se status = ABERTO)",
)
async def update_orcamento(
    orcamento_id: int,
    orcamento_data: OrcamentoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza um orçamento.

    **Regras:**
    - Orçamento deve estar ABERTO
    - Recalcula data_validade se validade_dias for alterado
    - Recalcula valor_total se desconto for alterado

    **Exemplo de requisição:**
    ```json
    {
        "cliente_id": 2,
        "validade_dias": 30,
        "desconto": 15.00,
        "observacoes": "Orçamento atualizado"
    }
    ```
    """
    service = OrcamentosService(db)
    return await service.atualizar_orcamento(orcamento_id, orcamento_data)


@router.post(
    "/{orcamento_id}/aprovar",
    response_model=OrcamentoResponse,
    summary="Aprovar orçamento",
    description="Aprova um orçamento (altera status para APROVADO)",
)
async def aprovar_orcamento(orcamento_id: int, db: AsyncSession = Depends(get_db)):
    """
    Aprova um orçamento (altera status para APROVADO).

    **Regras:**
    - Orçamento deve estar ABERTO
    - Altera status para APROVADO

    **Exemplo de uso:**
    - POST /orcamentos/1/aprovar
    """
    service = OrcamentosService(db)
    return await service.aprovar_orcamento(orcamento_id)


@router.post(
    "/{orcamento_id}/reprovar",
    response_model=OrcamentoResponse,
    summary="Reprovar orçamento",
    description="Reprova um orçamento (altera status para PERDIDO)",
)
async def reprovar_orcamento(orcamento_id: int, db: AsyncSession = Depends(get_db)):
    """
    Reprova um orçamento (altera status para PERDIDO).

    **Regras:**
    - Orçamento deve estar ABERTO ou APROVADO
    - Altera status para PERDIDO

    **Exemplo de uso:**
    - POST /orcamentos/1/reprovar
    """
    service = OrcamentosService(db)
    return await service.reprovar_orcamento(orcamento_id)


@router.post(
    "/{orcamento_id}/converter-venda",
    summary="Converter orçamento para venda",
    description="Converte um orçamento aprovado para venda",
)
async def converter_para_venda(
    orcamento_id: int,
    converter_data: ConverterOrcamentoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Converte um orçamento para venda.

    **Regras:**
    - Orçamento deve estar APROVADO
    - Valida estoque disponível para todos os itens
    - Cria venda através de VendasService
    - Atualiza status do orçamento para CONVERTIDO
    - Venda criada já registra saída de estoque automaticamente

    **Exemplo de requisição:**
    ```json
    {
        "forma_pagamento": "DINHEIRO"
    }
    ```

    **Retorno:**
    ```json
    {
        "orcamento": { ... },
        "venda": { ... }
    }
    ```

    **Exemplo de uso:**
    - POST /orcamentos/1/converter-venda
    """
    service = OrcamentosService(db)
    return await service.converter_para_venda(orcamento_id, converter_data)


@router.get(
    "/vencidos/lista",
    response_model=OrcamentoList,
    summary="Orçamentos vencidos",
    description="Retorna orçamentos vencidos (data_validade < hoje)",
)
async def get_orcamentos_vencidos(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna orçamentos vencidos.

    **Regras:**
    - Busca orçamentos com data_validade < hoje
    - Apenas orçamentos com status ABERTO ou APROVADO

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)

    **Exemplo de uso:**
    - GET /orcamentos/vencidos/lista?page=1&page_size=50
    """
    service = OrcamentosService(db)
    return await service.get_orcamentos_vencidos(page=page, page_size=page_size)


@router.get(
    "/a-vencer/lista",
    response_model=OrcamentoList,
    summary="Orçamentos a vencer",
    description="Retorna orçamentos a vencer nos próximos N dias",
)
async def get_orcamentos_a_vencer(
    dias: int = Query(7, ge=1, le=90, description="Dias à frente para verificar"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna orçamentos a vencer nos próximos N dias.

    **Regras:**
    - Busca orçamentos com data_validade entre hoje e hoje+N dias
    - Apenas orçamentos com status ABERTO ou APROVADO

    **Parâmetros:**
    - **dias**: Quantidade de dias à frente para verificar (padrão: 7, máximo: 90)
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)

    **Exemplo de uso:**
    - GET /orcamentos/a-vencer/lista?dias=7&page=1&page_size=50
    """
    service = OrcamentosService(db)
    return await service.get_orcamentos_a_vencer(
        dias=dias, page=page, page_size=page_size
    )


@router.delete(
    "/{orcamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancelar orçamento",
    description="Cancela (deleta) um orçamento",
)
async def deletar_orcamento(orcamento_id: int, db: AsyncSession = Depends(get_db)):
    """
    Cancela (deleta) um orçamento.

    **Regras:**
    - Orçamento deve estar ABERTO
    - Deleta o orçamento e seus itens (cascade)
    - NÃO mexe em estoque (orçamento nunca movimentou estoque)

    **Exemplo de uso:**
    - DELETE /orcamentos/1
    """
    service = OrcamentosService(db)
    await service.deletar_orcamento(orcamento_id)
    return None


# ========== ROTAS ALTERNATIVAS PARA COMPATIBILIDADE COM TESTES ==========


@router.post(
    "/{orcamento_id}/perdido",
    response_model=OrcamentoResponse,
    summary="Marcar orçamento como perdido (rota alternativa)",
    description="Marca orçamento como perdido (alias para /reprovar)",
)
async def marcar_como_perdido(orcamento_id: int, db: AsyncSession = Depends(get_db)):
    """
    Marca orçamento como perdido (rota alternativa a /reprovar).

    Esta rota é um alias para /reprovar para compatibilidade com testes.
    """
    service = OrcamentosService(db)
    return await service.reprovar_orcamento(orcamento_id)


@router.post(
    "/{orcamento_id}/converter",
    summary="Converter orçamento para venda (rota alternativa)",
    description="Converte orçamento para venda (alias para /converter-venda)",
)
async def converter_para_venda_alt(
    orcamento_id: int,
    converter_data: ConverterOrcamentoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Converte orçamento para venda (rota alternativa a /converter-venda).

    Esta rota é um alias para /converter-venda para compatibilidade com testes.
    """
    service = OrcamentosService(db)
    return await service.converter_para_venda(orcamento_id, converter_data)
