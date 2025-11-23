"""
Router para endpoints Mobile - API otimizada para dispositivos móveis
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.mobile.service import MobileService
from app.modules.mobile.schemas import (
    ProdutoMobileResponse,
    ClienteMobileResponse,
    VendaMobileCreate,
    OrcamentoMobileCreate,
    EstoqueConsultaResponse,
)
from app.modules.vendas.schemas import VendaResponse
from app.modules.orcamentos.schemas import OrcamentoResponse

router = APIRouter()


# ========== ENDPOINTS DE PRODUTOS ==========

@router.get(
    "/produtos/buscar",
    response_model=List[ProdutoMobileResponse],
    summary="Buscar produtos",
    description="Busca produtos por código de barras ou descrição (versão mobile otimizada)",
)
async def buscar_produtos(
    termo: str = Query(..., min_length=1, description="Termo de busca"),
    limit: int = Query(20, ge=1, le=50, description="Limite de resultados"),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca produtos por código de barras ou descrição.

    **Otimizações Mobile:**
    - Retorna apenas campos essenciais
    - Limite máximo de 50 resultados
    - Busca rápida com índices

    **Exemplo:**
    ```
    GET /mobile/produtos/buscar?termo=coca&limit=10
    ```
    """
    service = MobileService(db)
    return await service.buscar_produto(termo, limit)


@router.get(
    "/produtos/codigo-barras/{codigo}",
    response_model=Optional[ProdutoMobileResponse],
    summary="Buscar produto por código de barras",
    description="Busca produto por código de barras exato",
)
async def buscar_produto_por_codigo_barras(
    codigo: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Busca produto por código de barras exato.

    **Uso típico:**
    - Leitor de código de barras mobile
    - Consulta rápida no PDV mobile

    **Exemplo:**
    ```
    GET /mobile/produtos/codigo-barras/7891234567890
    ```
    """
    service = MobileService(db)
    return await service.buscar_produto_por_codigo_barras(codigo)


@router.get(
    "/produtos/populares",
    response_model=List[ProdutoMobileResponse],
    summary="Produtos mais vendidos",
    description="Retorna os produtos mais vendidos dos últimos 30 dias",
)
async def get_produtos_populares(
    limit: int = Query(20, ge=1, le=50, description="Quantidade de produtos"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna os produtos mais vendidos dos últimos 30 dias.

    **Otimizações:**
    - Cache de resultados (implementar futuramente)
    - Atualização diária
    - Útil para sugestões no mobile

    **Exemplo:**
    ```
    GET /mobile/produtos/populares?limit=10
    ```
    """
    service = MobileService(db)
    return await service.get_produtos_populares(limit)


# ========== ENDPOINTS DE ESTOQUE ==========

@router.get(
    "/estoque/consultar/{produto_id}",
    response_model=EstoqueConsultaResponse,
    summary="Consultar estoque",
    description="Consulta rápida de estoque de um produto",
)
async def consultar_estoque(
    produto_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Consulta rápida de estoque de um produto.

    **Informações retornadas:**
    - Estoque atual
    - Estoque mínimo
    - Alerta de estoque baixo
    - Preço de venda

    **Exemplo:**
    ```
    GET /mobile/estoque/consultar/1
    ```
    """
    service = MobileService(db)
    return await service.consultar_estoque(produto_id)


# ========== ENDPOINTS DE CLIENTES ==========

@router.get(
    "/clientes/buscar",
    response_model=List[ClienteMobileResponse],
    summary="Buscar clientes",
    description="Busca clientes por nome, CPF/CNPJ ou telefone",
)
async def buscar_clientes(
    termo: str = Query(..., min_length=1, description="Termo de busca"),
    limit: int = Query(20, ge=1, le=50, description="Limite de resultados"),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca clientes por nome, CPF/CNPJ ou telefone.

    **Otimizações Mobile:**
    - Retorna apenas campos essenciais (id, nome, telefone, celular)
    - Limite máximo de 50 resultados
    - Busca rápida

    **Exemplo:**
    ```
    GET /mobile/clientes/buscar?termo=joão&limit=10
    ```
    """
    service = MobileService(db)
    return await service.buscar_cliente(termo, limit)


@router.get(
    "/clientes/recentes",
    response_model=List[ClienteMobileResponse],
    summary="Clientes recentes",
    description="Retorna os últimos clientes cadastrados",
)
async def get_clientes_recentes(
    limit: int = Query(20, ge=1, le=50, description="Quantidade de clientes"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna os últimos clientes cadastrados.

    **Uso típico:**
    - Sugestões de clientes no mobile
    - Acesso rápido a cadastros recentes

    **Exemplo:**
    ```
    GET /mobile/clientes/recentes?limit=10
    ```
    """
    service = MobileService(db)
    return await service.get_clientes_recentes(limit)


# ========== ENDPOINTS DE VENDAS ==========

@router.post(
    "/vendas",
    response_model=VendaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar venda via mobile",
    description="Cria uma nova venda através do aplicativo mobile",
)
async def criar_venda_mobile(
    venda_data: VendaMobileCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova venda através do aplicativo mobile.

    **Validações:**
    - Produtos devem existir e estar ativos
    - Estoque suficiente para todos os itens
    - Cálculos automáticos de totais

    **Integração:**
    - Usa VendasService (mesmas regras de negócio)
    - Registra saída de estoque automaticamente
    - Venda criada com status PENDENTE

    **Exemplo de requisição:**
    ```json
    {
        "cliente_id": 1,
        "vendedor_id": 1,
        "forma_pagamento": "DINHEIRO",
        "desconto": 5.00,
        "observacoes": "Venda mobile",
        "itens": [
            {
                "produto_id": 1,
                "quantidade": 2.0,
                "preco_unitario": 32.90,
                "desconto_item": 0.0
            }
        ]
    }
    ```
    """
    service = MobileService(db)
    return await service.criar_venda_mobile(venda_data)


# ========== ENDPOINTS DE ORÇAMENTOS ==========

@router.post(
    "/orcamentos",
    response_model=OrcamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar orçamento via mobile",
    description="Cria um novo orçamento através do aplicativo mobile",
)
async def criar_orcamento_mobile(
    orcamento_data: OrcamentoMobileCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo orçamento através do aplicativo mobile.

    **Validações:**
    - Produtos devem existir e estar ativos
    - Cálculos automáticos de totais
    - Validade em dias (padrão 7 dias)

    **Integração:**
    - Usa OrcamentosService (mesmas regras de negócio)
    - NÃO movimenta estoque (apenas informacional)
    - Orçamento criado com status ABERTO

    **Exemplo de requisição:**
    ```json
    {
        "cliente_id": 1,
        "vendedor_id": 1,
        "validade_dias": 7,
        "desconto": 10.00,
        "observacoes": "Orçamento mobile",
        "itens": [
            {
                "produto_id": 1,
                "quantidade": 2.0,
                "preco_unitario": 32.90,
                "desconto_item": 0.0
            }
        ]
    }
    ```
    """
    service = MobileService(db)
    return await service.criar_orcamento_mobile(orcamento_data)
