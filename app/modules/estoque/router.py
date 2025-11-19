"""
Router para endpoints de Estoque
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.modules.estoque.service import EstoqueService
from app.modules.estoque.schemas import (
    EntradaEstoqueCreate,
    SaidaEstoqueCreate,
    AjusteEstoqueCreate,
    MovimentacaoResponse,
    MovimentacaoList,
    EstoqueAtualResponse,
    TipoMovimentacaoEnum,
)

router = APIRouter()


@router.post(
    "/entrada",
    response_model=MovimentacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar entrada de estoque",
    description="Registra uma entrada de estoque (compra, NF, etc) e atualiza o estoque atual do produto",
)
async def entrada_estoque(
    entrada_data: EntradaEstoqueCreate, db: AsyncSession = Depends(get_db)
):
    """
    Registra uma entrada de estoque.

    **Regras:**
    - Produto deve existir e estar ativo
    - Quantidade deve ser maior que zero
    - Atualiza automaticamente o estoque_atual do produto
    - Atualiza o preço de custo do produto com o custo_unitario informado

    **Exemplo de requisição:**
    ```json
    {
        "produto_id": 1,
        "quantidade": 100.0,
        "custo_unitario": 25.50,
        "documento_referencia": "NF-12345",
        "observacao": "Entrada via nota fiscal de compra",
        "usuario_id": 1
    }
    ```
    """
    service = EstoqueService(db)
    return await service.entrada_estoque(entrada_data)


@router.post(
    "/saida",
    response_model=MovimentacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar saída de estoque",
    description="Registra uma saída de estoque (venda, consumo, etc) e atualiza o estoque atual do produto",
)
async def saida_estoque(
    saida_data: SaidaEstoqueCreate, db: AsyncSession = Depends(get_db)
):
    """
    Registra uma saída de estoque.

    **Regras:**
    - Produto deve existir e estar ativo
    - Valida se há estoque suficiente antes de permitir a saída
    - Quantidade deve ser maior que zero
    - Se custo_unitario não informado, usa o preço de custo do produto
    - Atualiza automaticamente o estoque_atual do produto

    **Exemplo de requisição:**
    ```json
    {
        "produto_id": 1,
        "quantidade": 10.0,
        "custo_unitario": 25.50,
        "documento_referencia": "VENDA-789",
        "observacao": "Saída por venda ao cliente",
        "usuario_id": 1
    }
    ```

    **Retorna erro 400 se:**
    - Não houver estoque suficiente
    - Produto estiver inativo
    """
    service = EstoqueService(db)
    return await service.saida_estoque(saida_data)


@router.post(
    "/ajuste",
    response_model=MovimentacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ajustar estoque manualmente",
    description="Registra um ajuste manual de estoque com justificativa obrigatória",
)
async def ajuste_estoque(
    ajuste_data: AjusteEstoqueCreate, db: AsyncSession = Depends(get_db)
):
    """
    Registra um ajuste manual de estoque.

    **Regras:**
    - Produto deve existir e estar ativo
    - Observação é obrigatória (mínimo 10 caracteres) para justificar o ajuste
    - Quantidade pode ser positiva (adiciona) ou negativa (remove)
    - Se quantidade negativa, valida se há estoque suficiente
    - Atualiza automaticamente o estoque_atual do produto

    **Exemplo de requisição (ajuste positivo):**
    ```json
    {
        "produto_id": 1,
        "quantidade": 5.0,
        "custo_unitario": 25.50,
        "observacao": "Ajuste de inventário - produtos encontrados no depósito secundário",
        "usuario_id": 1
    }
    ```

    **Exemplo de requisição (ajuste negativo):**
    ```json
    {
        "produto_id": 1,
        "quantidade": -3.0,
        "observacao": "Ajuste de inventário - produtos danificados e descartados",
        "usuario_id": 1
    }
    ```
    """
    service = EstoqueService(db)
    return await service.ajuste_estoque(ajuste_data)


@router.get(
    "/produto/{produto_id}/saldo",
    response_model=EstoqueAtualResponse,
    summary="Consultar saldo atual do produto",
    description="Retorna informações detalhadas do estoque atual de um produto",
)
async def get_saldo_produto(produto_id: int, db: AsyncSession = Depends(get_db)):
    """
    Consulta o saldo atual de um produto.

    **Retorna:**
    - Estoque atual
    - Estoque mínimo
    - Custo médio ponderado
    - Valor total do estoque
    - Indicador se está abaixo do estoque mínimo

    **Exemplo de resposta:**
    ```json
    {
        "produto_id": 1,
        "produto_descricao": "Cimento Portland CP-II 50kg",
        "produto_codigo_barras": "7891234567890",
        "estoque_atual": 95.0,
        "estoque_minimo": 20.0,
        "unidade": "SC",
        "custo_medio": 25.50,
        "valor_total_estoque": 2422.50,
        "abaixo_minimo": false
    }
    ```
    """
    service = EstoqueService(db)
    return await service.get_saldo_produto(produto_id)


@router.get(
    "/produto/{produto_id}/movimentacoes",
    response_model=MovimentacaoList,
    summary="Listar movimentações de um produto",
    description="Lista o histórico de movimentações de estoque de um produto específico",
)
async def get_movimentacoes_produto(
    produto_id: int,
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    data_inicio: Optional[datetime] = Query(
        None, description="Data inicial do filtro (formato ISO 8601)"
    ),
    data_fim: Optional[datetime] = Query(
        None, description="Data final do filtro (formato ISO 8601)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista todas as movimentações de estoque de um produto.

    **Parâmetros:**
    - **produto_id**: ID do produto
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **data_inicio**: Filtrar movimentações a partir desta data (opcional)
    - **data_fim**: Filtrar movimentações até esta data (opcional)

    **Exemplo:**
    - `/produto/1/movimentacoes` - lista todas as movimentações do produto 1
    - `/produto/1/movimentacoes?data_inicio=2024-01-01T00:00:00` - movimentações a partir de 01/01/2024
    """
    service = EstoqueService(db)
    return await service.get_movimentacoes_produto(
        produto_id, page, page_size, data_inicio, data_fim
    )


@router.get(
    "/movimentacoes",
    response_model=MovimentacaoList,
    summary="Listar todas as movimentações",
    description="Lista todas as movimentações de estoque com filtros opcionais",
)
async def list_movimentacoes(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    produto_id: Optional[int] = Query(None, description="Filtrar por produto"),
    tipo: Optional[TipoMovimentacaoEnum] = Query(
        None, description="Filtrar por tipo de movimentação"
    ),
    data_inicio: Optional[datetime] = Query(
        None, description="Data inicial do filtro (formato ISO 8601)"
    ),
    data_fim: Optional[datetime] = Query(
        None, description="Data final do filtro (formato ISO 8601)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista todas as movimentações de estoque com filtros.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **produto_id**: Filtrar por produto específico (opcional)
    - **tipo**: Filtrar por tipo de movimentação (ENTRADA, SAIDA, AJUSTE, etc) (opcional)
    - **data_inicio**: Filtrar movimentações a partir desta data (opcional)
    - **data_fim**: Filtrar movimentações até esta data (opcional)

    **Tipos de movimentação disponíveis:**
    - ENTRADA: Entrada de estoque (compras, NF)
    - SAIDA: Saída de estoque (vendas, consumo)
    - AJUSTE: Ajuste manual de estoque
    - TRANSFERENCIA: Transferência entre locais
    - DEVOLUCAO: Devolução de clientes

    **Exemplos:**
    - `/movimentacoes` - lista todas as movimentações
    - `/movimentacoes?tipo=ENTRADA` - lista apenas entradas
    - `/movimentacoes?produto_id=1&tipo=SAIDA` - saídas do produto 1
    """
    service = EstoqueService(db)
    return await service.list_movimentacoes(
        page, page_size, produto_id, tipo, data_inicio, data_fim
    )


@router.get(
    "/relatorio/periodo",
    response_model=MovimentacaoList,
    summary="Relatório de movimentações por período",
    description="Gera relatório de todas as movimentações em um período específico",
)
async def relatorio_periodo(
    data_inicio: datetime = Query(
        ..., description="Data inicial do período (formato ISO 8601)"
    ),
    data_fim: datetime = Query(
        ..., description="Data final do período (formato ISO 8601)"
    ),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Gera relatório de movimentações em um período.

    **Parâmetros obrigatórios:**
    - **data_inicio**: Data inicial do período
    - **data_fim**: Data final do período

    **Parâmetros opcionais:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)

    **Exemplo:**
    ```
    /relatorio/periodo?data_inicio=2024-01-01T00:00:00&data_fim=2024-01-31T23:59:59
    ```

    **Útil para:**
    - Análise de movimentações em um mês específico
    - Relatórios de auditoria
    - Conferência de inventário
    - Análise de entrada e saída em períodos
    """
    service = EstoqueService(db)
    return await service.get_relatorio_periodo(data_inicio, data_fim, page, page_size)
