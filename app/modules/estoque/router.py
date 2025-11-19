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
from app.modules.estoque.wms_service import WMSService
from app.modules.estoque.inventario_service import InventarioService
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
    LocalizacaoEstoqueCreate,
    LocalizacaoEstoqueUpdate,
    LocalizacaoEstoqueResponse,
    LocalizacaoEstoqueList,
    VincularProdutoLocalizacaoRequest,
    ProdutoLocalizacaoResponse,
    PickingListItem,
    FichaInventarioCreate,
    FichaInventarioResponse,
    FichaInventarioList,
    ItemInventarioResponse,
    RegistrarContagemRequest,
    IniciarContagemRequest,
    FinalizarContagemRequest,
    AcuracidadeResponse,
    DivergenciaItem,
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


# ==================== ENDPOINTS WMS (WAREHOUSE MANAGEMENT SYSTEM) ====================


@router.post(
    "/wms/localizacoes",
    response_model=LocalizacaoEstoqueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar localização de estoque",
    description="Cria uma nova localização física no estoque (corredor, prateleira, pallet, depósito)",
)
async def criar_localizacao(
    data: LocalizacaoEstoqueCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria uma nova localização de estoque.

    **Tipos de localização:**
    - CORREDOR: Corredor do armazém
    - PRATELEIRA: Prateleira específica
    - PALLET: Localização de pallet
    - DEPOSITO: Depósito ou área de armazenagem

    **Exemplo:**
    ```json
    {
        "codigo": "A-01-P3-N2",
        "descricao": "Corredor A, Prateleira 1, Nível 2",
        "tipo": "PRATELEIRA",
        "corredor": "A",
        "prateleira": "01-P3",
        "nivel": "N2",
        "ativo": true
    }
    ```
    """
    service = WMSService(db)
    return await service.criar_localizacao(data)


@router.get(
    "/wms/localizacoes/{localizacao_id}",
    response_model=LocalizacaoEstoqueResponse,
    summary="Buscar localização por ID",
    description="Retorna informações de uma localização específica",
)
async def get_localizacao(localizacao_id: int, db: AsyncSession = Depends(get_db)):
    """Busca localização de estoque por ID"""
    service = WMSService(db)
    return await service.get_localizacao(localizacao_id)


@router.get(
    "/wms/localizacoes",
    response_model=LocalizacaoEstoqueList,
    summary="Listar localizações",
    description="Lista todas as localizações de estoque com paginação",
)
async def listar_localizacoes(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    apenas_ativas: bool = Query(True, description="Listar apenas localizações ativas"),
    db: AsyncSession = Depends(get_db),
):
    """Lista localizações de estoque com paginação"""
    service = WMSService(db)
    return await service.list_localizacoes(page, page_size, apenas_ativas)


@router.put(
    "/wms/localizacoes/{localizacao_id}",
    response_model=LocalizacaoEstoqueResponse,
    summary="Atualizar localização",
    description="Atualiza informações de uma localização",
)
async def atualizar_localizacao(
    localizacao_id: int,
    data: LocalizacaoEstoqueUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza uma localização de estoque"""
    service = WMSService(db)
    return await service.atualizar_localizacao(localizacao_id, data)


@router.delete(
    "/wms/localizacoes/{localizacao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Inativar localização",
    description="Inativa uma localização (soft delete)",
)
async def inativar_localizacao(localizacao_id: int, db: AsyncSession = Depends(get_db)):
    """Inativa uma localização de estoque (soft delete)"""
    service = WMSService(db)
    await service.inativar_localizacao(localizacao_id)
    return None


@router.post(
    "/wms/produtos/{produto_id}/localizacoes",
    response_model=ProdutoLocalizacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Vincular produto a localização",
    description="Vincula um produto a uma localização de estoque",
)
async def vincular_produto_localizacao(
    produto_id: int,
    data: VincularProdutoLocalizacaoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Vincula um produto a uma localização de estoque.

    **Permite:**
    - Definir quantidade inicial na localização
    - Definir quantidade mínima e máxima

    **Útil para:**
    - Organização física do estoque
    - Picking (separação) otimizado
    - Controle de capacidade por localização
    """
    service = WMSService(db)
    return await service.vincular_produto_localizacao(produto_id, data)


@router.get(
    "/wms/produtos/{produto_id}/localizacoes",
    response_model=list[ProdutoLocalizacaoResponse],
    summary="Listar localizações de um produto",
    description="Lista todas as localizações onde um produto está armazenado",
)
async def get_localizacoes_produto(produto_id: int, db: AsyncSession = Depends(get_db)):
    """
    Lista todas as localizações onde um produto está armazenado.

    **Retorna:**
    - Código e descrição da localização
    - Quantidade disponível em cada localização
    - Ordenado por quantidade (maior primeiro)
    """
    service = WMSService(db)
    return await service.get_localizacoes_produto(produto_id)


@router.post(
    "/wms/picking",
    response_model=list[PickingListItem],
    summary="Gerar lista de separação (picking)",
    description="Gera lista de picking com sugestão de localizações (FIFO)",
)
async def gerar_lista_picking(
    itens_pedido: list[dict], db: AsyncSession = Depends(get_db)
):
    """
    Gera lista de separação (picking) para um pedido.

    **Exemplo de entrada:**
    ```json
    [
        {"produto_id": 1, "quantidade": 10},
        {"produto_id": 2, "quantidade": 5}
    ]
    ```

    **Retorna:**
    - Lista de itens para separar
    - Localização sugerida por produto (FIFO - mais antiga primeiro)
    - Quantidade disponível em cada localização

    **Regras:**
    - Sugere localizações por ordem FIFO
    - Pode sugerir múltiplas localizações se necessário
    - Otimiza o caminho de separação
    """
    service = WMSService(db)
    return await service.gerar_lista_picking(itens_pedido)


# ==================== ENDPOINTS INVENTÁRIO ====================


@router.post(
    "/inventario/fichas",
    response_model=FichaInventarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar ficha de inventário",
    description="Cria nova ficha de inventário (GERAL, PARCIAL ou ROTATIVO)",
)
async def criar_ficha_inventario(
    data: FichaInventarioCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria nova ficha de inventário.

    **Tipos de inventário:**
    - **GERAL**: Inclui todos os produtos ativos
    - **PARCIAL**: Apenas produtos/localizações/categorias especificadas
    - **ROTATIVO**: Produtos com maior rotatividade (curva A/B)

    **Exemplo GERAL:**
    ```json
    {
        "tipo": "GERAL",
        "observacoes": "Inventário mensal de junho"
    }
    ```

    **Exemplo PARCIAL:**
    ```json
    {
        "tipo": "PARCIAL",
        "produto_ids": [1, 2, 3],
        "categoria_ids": [1],
        "observacoes": "Inventário de cimentos e argamassas"
    }
    ```

    **Ações automáticas:**
    - Gera itens de inventário automaticamente
    - Captura estoque atual do sistema para cada produto
    - Inicia com status ABERTA
    """
    service = InventarioService(db)
    return await service.criar_ficha_inventario(data)


@router.get(
    "/inventario/fichas/{ficha_id}",
    response_model=FichaInventarioResponse,
    summary="Buscar ficha de inventário",
    description="Retorna informações de uma ficha de inventário",
)
async def get_ficha_inventario(ficha_id: int, db: AsyncSession = Depends(get_db)):
    """Busca ficha de inventário por ID"""
    service = InventarioService(db)
    return await service.get_ficha(ficha_id)


@router.get(
    "/inventario/fichas",
    response_model=FichaInventarioList,
    summary="Listar fichas de inventário",
    description="Lista fichas de inventário com filtros",
)
async def listar_fichas_inventario(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    db: AsyncSession = Depends(get_db),
):
    """Lista fichas de inventário com paginação e filtros"""
    service = InventarioService(db)
    return await service.list_fichas(page, page_size, status, tipo)


@router.post(
    "/inventario/fichas/{ficha_id}/iniciar",
    response_model=FichaInventarioResponse,
    summary="Iniciar contagem de inventário",
    description="Inicia a contagem de uma ficha de inventário",
)
async def iniciar_contagem(
    ficha_id: int,
    data: IniciarContagemRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Inicia contagem de inventário.

    **Regras:**
    - Apenas fichas com status ABERTA podem iniciar contagem
    - Muda status para EM_ANDAMENTO
    - Registra data de início
    """
    service = InventarioService(db)
    return await service.iniciar_contagem(ficha_id, data)


@router.get(
    "/inventario/fichas/{ficha_id}/itens",
    response_model=list[ItemInventarioResponse],
    summary="Listar itens de inventário",
    description="Lista todos os itens de uma ficha de inventário",
)
async def listar_itens_inventario(ficha_id: int, db: AsyncSession = Depends(get_db)):
    """Lista todos os itens de uma ficha de inventário"""
    service = InventarioService(db)
    return await service.get_itens_ficha(ficha_id)


@router.post(
    "/inventario/registrar-contagem",
    response_model=ItemInventarioResponse,
    summary="Registrar contagem de item",
    description="Registra a contagem física de um item de inventário",
)
async def registrar_contagem(
    data: RegistrarContagemRequest, db: AsyncSession = Depends(get_db)
):
    """
    Registra contagem física de um item.

    **Exemplo:**
    ```json
    {
        "item_id": 1,
        "quantidade_contada": 45.0,
        "justificativa": "Diferença de 5 unidades - produto avariado",
        "conferido_por_id": 1
    }
    ```

    **Ações automáticas:**
    - Calcula divergência automaticamente
    - Registra data e responsável pela contagem
    """
    service = InventarioService(db)
    return await service.registrar_contagem(data)


@router.post(
    "/inventario/fichas/{ficha_id}/finalizar",
    response_model=FichaInventarioResponse,
    summary="Finalizar inventário",
    description="Finaliza inventário e opcionalmente ajusta estoque",
)
async def finalizar_inventario(
    ficha_id: int,
    data: FinalizarContagemRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Finaliza inventário.

    **Regras:**
    - Apenas fichas EM_ANDAMENTO podem ser finalizadas
    - Todos os itens devem estar contados
    - Se ajustar_estoque=True, atualiza estoque dos produtos

    **Exemplo:**
    ```json
    {
        "ajustar_estoque": true,
        "observacoes": "Inventário concluído com divergências ajustadas"
    }
    ```

    **Ações automáticas:**
    - Muda status para CONCLUIDA
    - Registra data de conclusão
    - Se ajustar_estoque=True, atualiza estoque_atual dos produtos
    """
    service = InventarioService(db)
    return await service.finalizar_inventario(ficha_id, data)


@router.post(
    "/inventario/fichas/{ficha_id}/cancelar",
    response_model=FichaInventarioResponse,
    summary="Cancelar inventário",
    description="Cancela um inventário (apenas se não estiver concluído)",
)
async def cancelar_inventario(ficha_id: int, db: AsyncSession = Depends(get_db)):
    """
    Cancela inventário.

    **Regras:**
    - Não é possível cancelar inventário concluído
    - Muda status para CANCELADA
    """
    service = InventarioService(db)
    return await service.cancelar_inventario(ficha_id)


@router.get(
    "/inventario/fichas/{ficha_id}/acuracidade",
    response_model=AcuracidadeResponse,
    summary="Calcular acuracidade do inventário",
    description="Calcula a acuracidade (precisão) do inventário",
)
async def calcular_acuracidade(ficha_id: int, db: AsyncSession = Depends(get_db)):
    """
    Calcula acuracidade do inventário.

    **Métrica:**
    - Acuracidade = (itens sem divergência / total de itens) * 100

    **Retorna:**
    - Total de itens inventariados
    - Itens sem divergência
    - Itens com divergência
    - Percentual de acuracidade
    - Total de divergências positivas (sobras)
    - Total de divergências negativas (faltas)

    **Útil para:**
    - Avaliar qualidade do processo de inventário
    - Identificar problemas no controle de estoque
    - KPI de gestão de estoque
    """
    service = InventarioService(db)
    return await service.calcular_acuracidade(ficha_id)


@router.get(
    "/inventario/fichas/{ficha_id}/divergencias",
    response_model=list[DivergenciaItem],
    summary="Listar divergências do inventário",
    description="Lista todos os itens com divergência entre sistema e contagem física",
)
async def listar_divergencias(ficha_id: int, db: AsyncSession = Depends(get_db)):
    """
    Lista itens com divergência no inventário.

    **Retorna:**
    - Produto e código de barras
    - Quantidade no sistema vs. quantidade contada
    - Divergência absoluta e percentual
    - Localização (se houver)

    **Útil para:**
    - Análise de perdas
    - Identificação de problemas operacionais
    - Auditoria de estoque
    """
    service = InventarioService(db)
    return await service.get_divergencias(ficha_id)
