"""
Router para endpoints de Estoque
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.modules.estoque.service import EstoqueService
from app.modules.estoque.lote_service import LoteEstoqueService
from app.modules.estoque.curva_abc_service import CurvaABCService
from app.modules.estoque.schemas import (
    EntradaEstoqueCreate,
    SaidaEstoqueCreate,
    AjusteEstoqueCreate,
    MovimentacaoResponse,
    MovimentacaoList,
    EstoqueAtualResponse,
    TipoMovimentacaoEnum,
    LoteEstoqueCreate,
    LoteEstoqueResponse,
    LoteEstoqueList,
    ProdutoLoteFIFO,
    CurvaABCResponse,
    CurvaABCItem,
    ClassificacaoABC,
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


# ==================== ENDPOINTS DE LOTE ====================


@router.post(
    "/lotes",
    response_model=LoteEstoqueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar lote de estoque",
    description="Cria um novo lote de estoque para produto com controle de lote habilitado",
)
async def criar_lote(
    lote_data: LoteEstoqueCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo lote de estoque.

    **Regras:**
    - Produto deve ter controla_lote=True
    - Data de validade deve ser futura
    - Número do lote é obrigatório

    **Exemplo de requisição:**
    ```json
    {
        "produto_id": 1,
        "numero_lote": "LOTE-2024-001",
        "data_fabricacao": "2024-01-15",
        "data_validade": "2025-01-15",
        "quantidade_inicial": 100.0,
        "custo_unitario": 25.50,
        "documento_referencia": "NF-12345"
    }
    ```
    """
    service = LoteEstoqueService(db)
    return await service.criar_lote(lote_data)


@router.get(
    "/lotes/produto/{produto_id}",
    response_model=LoteEstoqueList,
    summary="Listar lotes de um produto",
    description="Lista todos os lotes de um produto específico",
)
async def listar_lotes_produto(
    produto_id: int,
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista todos os lotes de um produto.

    **Parâmetros:**
    - **produto_id**: ID do produto
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)

    **Retorna:**
    - Lista de lotes ordenados por data de validade (FIFO)
    """
    service = LoteEstoqueService(db)
    return await service.listar_lotes_produto(produto_id, page, page_size)


@router.get(
    "/lotes/{lote_id}",
    response_model=LoteEstoqueResponse,
    summary="Buscar lote por ID",
    description="Busca informações detalhadas de um lote específico",
)
async def get_lote(lote_id: int, db: AsyncSession = Depends(get_db)):
    """
    Busca um lote específico por ID.

    **Retorna:**
    - Informações completas do lote
    - Quantidade atual disponível
    - Status de vencimento
    """
    service = LoteEstoqueService(db)
    return await service.get_lote(lote_id)


@router.get(
    "/lotes/fifo/{produto_id}",
    response_model=ProdutoLoteFIFO,
    summary="Sugerir lote FIFO para saída",
    description="Retorna o lote mais antigo disponível para saída (FIFO)",
)
async def sugerir_lote_fifo(
    produto_id: int, db: AsyncSession = Depends(get_db)
):
    """
    Sugere o lote mais antigo disponível para saída seguindo método FIFO.

    **Regras FIFO:**
    - Prioriza lote com data de validade mais próxima
    - Apenas lotes com quantidade_atual > 0
    - Alerta se lote está vencido

    **Exemplo de resposta:**
    ```json
    {
        "lote_id": 1,
        "numero_lote": "LOTE-2024-001",
        "data_validade": "2025-01-15",
        "quantidade_disponivel": 50.0,
        "custo_unitario": 25.50,
        "esta_vencido": false,
        "dias_para_vencer": 180
    }
    ```
    """
    service = LoteEstoqueService(db)
    return await service.sugerir_lote_fifo(produto_id)


@router.get(
    "/lotes/vencidos",
    response_model=LoteEstoqueList,
    summary="Listar lotes vencidos",
    description="Lista todos os lotes com data de validade vencida",
)
async def listar_lotes_vencidos(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista lotes vencidos.

    **Útil para:**
    - Identificar produtos vencidos no estoque
    - Planejamento de descartes
    - Auditoria de validade
    """
    service = LoteEstoqueService(db)
    return await service.get_lotes_vencidos(page, page_size)


@router.get(
    "/lotes/a-vencer",
    response_model=LoteEstoqueList,
    summary="Listar lotes a vencer",
    description="Lista lotes que vencem nos próximos N dias",
)
async def listar_lotes_a_vencer(
    dias: int = Query(30, ge=1, le=365, description="Dias para vencer"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista lotes que vencem nos próximos N dias.

    **Parâmetros:**
    - **dias**: Número de dias para verificar (padrão: 30)

    **Útil para:**
    - Planejamento de vendas prioritárias
    - Evitar perdas por vencimento
    - Gestão proativa de estoque
    """
    service = LoteEstoqueService(db)
    return await service.get_lotes_a_vencer(dias, page, page_size)


# ==================== ENDPOINTS DE CURVA ABC ====================


@router.get(
    "/curva-abc",
    response_model=CurvaABCResponse,
    summary="Calcular Curva ABC",
    description="Analisa e classifica produtos pela Curva ABC baseada nas vendas",
)
async def calcular_curva_abc(
    periodo_meses: int = Query(
        6, ge=1, le=24, description="Período de análise em meses (padrão: 6)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Calcula a Curva ABC de produtos baseada nas vendas.

    **Classificação:**
    - **Classe A**: Produtos que representam 80% do faturamento (~20% dos produtos)
    - **Classe B**: Produtos que representam 15% do faturamento (~30% dos produtos)
    - **Classe C**: Produtos que representam 5% do faturamento (~50% dos produtos)

    **Parâmetros:**
    - **periodo_meses**: Número de meses para análise (padrão: 6, máximo: 24)

    **Retorna:**
    - Lista de produtos classificados por faturamento
    - Percentuais individuais e acumulados
    - Estatísticas por classe

    **Útil para:**
    - Gestão estratégica de estoque
    - Priorização de compras
    - Análise de rentabilidade
    - Decisões de mix de produtos
    """
    service = CurvaABCService(db)
    return await service.calcular_curva_abc(periodo_meses)


@router.get(
    "/curva-abc/classe/{classe}",
    response_model=list[CurvaABCItem],
    summary="Listar produtos por classe ABC",
    description="Lista apenas produtos de uma classe específica (A, B ou C)",
)
async def listar_produtos_por_classe(
    classe: ClassificacaoABC,
    periodo_meses: int = Query(
        6, ge=1, le=24, description="Período de análise em meses (padrão: 6)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista produtos de uma classe ABC específica.

    **Parâmetros:**
    - **classe**: Classe ABC (A, B ou C)
    - **periodo_meses**: Número de meses para análise (padrão: 6)

    **Exemplos:**
    - `/curva-abc/classe/A` - Lista produtos classe A (top sellers)
    - `/curva-abc/classe/B` - Lista produtos classe B (médio desempenho)
    - `/curva-abc/classe/C` - Lista produtos classe C (baixo desempenho)

    **Útil para:**
    - Foco em produtos estratégicos (classe A)
    - Análise de produtos intermediários (classe B)
    - Identificação de produtos de baixo giro (classe C)
    """
    service = CurvaABCService(db)

    if classe == ClassificacaoABC.A:
        return await service.get_produtos_curva_a(periodo_meses)
    elif classe == ClassificacaoABC.B:
        return await service.get_produtos_curva_b(periodo_meses)
    else:  # ClassificacaoABC.C
        return await service.get_produtos_curva_c(periodo_meses)
