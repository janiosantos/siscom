"""
Schemas Pydantic para Estoque
"""
from datetime import datetime, date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.modules.produtos.schemas import ProdutoResponse


class TipoMovimentacaoEnum(str, Enum):
    """Enum para tipos de movimentação de estoque"""

    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    AJUSTE = "AJUSTE"
    TRANSFERENCIA = "TRANSFERENCIA"
    DEVOLUCAO = "DEVOLUCAO"


class MovimentacaoBase(BaseModel):
    """Schema base de Movimentação de Estoque"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    tipo: TipoMovimentacaoEnum = Field(..., description="Tipo de movimentação")
    quantidade: float = Field(..., gt=0, description="Quantidade movimentada")
    custo_unitario: float = Field(..., ge=0, description="Custo unitário do produto")
    documento_referencia: Optional[str] = Field(
        None, max_length=100, description="Documento de referência (NF, pedido, etc)"
    )
    observacao: Optional[str] = Field(None, max_length=500, description="Observação")
    usuario_id: Optional[int] = Field(None, description="ID do usuário responsável")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que a quantidade seja positiva"""
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v

    @field_validator("custo_unitario")
    @classmethod
    def validar_custo_unitario(cls, v: float) -> float:
        """Valida que o custo unitário não seja negativo"""
        if v < 0:
            raise ValueError("Custo unitário não pode ser negativo")
        return v


class MovimentacaoCreate(MovimentacaoBase):
    """Schema para criação de Movimentação de Estoque"""

    pass


class EntradaEstoqueCreate(BaseModel):
    """Schema para entrada de estoque via NF ou compra"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: float = Field(..., gt=0, description="Quantidade de entrada")
    custo_unitario: float = Field(..., ge=0, description="Custo unitário do produto")
    documento_referencia: Optional[str] = Field(
        None, max_length=100, description="Número da NF ou documento"
    )
    observacao: Optional[str] = Field(None, max_length=500, description="Observação")
    usuario_id: Optional[int] = Field(None, description="ID do usuário responsável")
    # Campos de lote (obrigatórios se produto controla_lote=True)
    numero_lote: Optional[str] = Field(None, max_length=50, description="Número do lote")
    data_fabricacao: Optional[date] = Field(None, description="Data de fabricação")
    data_validade: Optional[date] = Field(None, description="Data de validade")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que a quantidade seja positiva"""
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v


class SaidaEstoqueCreate(BaseModel):
    """Schema para saída de estoque por venda ou consumo"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: float = Field(..., gt=0, description="Quantidade de saída")
    custo_unitario: Optional[float] = Field(
        None, ge=0, description="Custo unitário (opcional, usa preço de custo do produto se não informado)"
    )
    documento_referencia: Optional[str] = Field(
        None, max_length=100, description="Número da venda ou documento"
    )
    observacao: Optional[str] = Field(None, max_length=500, description="Observação")
    usuario_id: Optional[int] = Field(None, description="ID do usuário responsável")
    # Campo de lote (obrigatório se produto controla_lote=True)
    lote_id: Optional[int] = Field(None, description="ID do lote para saída (FIFO se não informado)")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que a quantidade seja positiva"""
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v


class AjusteEstoqueCreate(BaseModel):
    """Schema para ajuste manual de estoque"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    quantidade: float = Field(
        ..., description="Quantidade do ajuste (positivo para adicionar, negativo para remover)"
    )
    custo_unitario: Optional[float] = Field(
        None, ge=0, description="Custo unitário (opcional, usa preço de custo do produto se não informado)"
    )
    observacao: str = Field(
        ..., min_length=10, max_length=500, description="Justificativa obrigatória para o ajuste"
    )
    usuario_id: Optional[int] = Field(None, description="ID do usuário responsável")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que a quantidade não seja zero"""
        if v == 0:
            raise ValueError("Quantidade do ajuste não pode ser zero")
        return v

    @field_validator("observacao")
    @classmethod
    def validar_observacao(cls, v: str) -> str:
        """Valida que a observação não esteja vazia"""
        if not v or not v.strip():
            raise ValueError("Observação é obrigatória para ajustes de estoque")
        if len(v.strip()) < 10:
            raise ValueError(
                "Observação deve ter no mínimo 10 caracteres para justificar o ajuste"
            )
        return v.strip()


class MovimentacaoResponse(MovimentacaoBase):
    """Schema de resposta de Movimentação de Estoque"""

    id: int
    valor_total: float = Field(..., description="Valor total da movimentação")
    produto: ProdutoResponse
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MovimentacaoList(BaseModel):
    """Schema para lista paginada de movimentações"""

    items: list[MovimentacaoResponse]
    total: int
    page: int
    page_size: int
    pages: int


class EstoqueAtualResponse(BaseModel):
    """Schema de resposta para saldo atual de estoque"""

    produto_id: int
    produto_descricao: str
    produto_codigo_barras: str
    estoque_atual: float
    estoque_minimo: float
    unidade: str
    custo_medio: float = Field(..., description="Custo médio ponderado")
    valor_total_estoque: float = Field(
        ..., description="Valor total do estoque (quantidade * custo médio)"
    )
    abaixo_minimo: bool = Field(..., description="Indica se está abaixo do estoque mínimo")

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS DE LOTE ====================


class LoteEstoqueBase(BaseModel):
    """Schema base de Lote de Estoque"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    numero_lote: str = Field(..., min_length=1, max_length=50, description="Número do lote")
    data_fabricacao: Optional[date] = Field(None, description="Data de fabricação")
    data_validade: date = Field(..., description="Data de validade")
    quantidade_inicial: float = Field(..., gt=0, description="Quantidade inicial do lote")
    custo_unitario: float = Field(..., ge=0, description="Custo unitário do lote")
    documento_referencia: Optional[str] = Field(
        None, max_length=100, description="Documento de referência (NF, etc)"
    )

    @field_validator("data_validade")
    @classmethod
    def validar_data_validade(cls, v: date, info) -> date:
        """Valida que a data de validade seja futura"""
        if v < date.today():
            raise ValueError("Data de validade não pode ser anterior à data atual")
        return v

    @field_validator("data_fabricacao")
    @classmethod
    def validar_data_fabricacao(cls, v: Optional[date], info) -> Optional[date]:
        """Valida que a data de fabricação não seja futura"""
        if v and v > date.today():
            raise ValueError("Data de fabricação não pode ser futura")
        return v


class LoteEstoqueCreate(LoteEstoqueBase):
    """Schema para criação de Lote de Estoque"""

    pass


class LoteEstoqueResponse(LoteEstoqueBase):
    """Schema de resposta de Lote de Estoque"""

    id: int
    quantidade_atual: float = Field(..., description="Quantidade atual disponível no lote")
    produto: ProdutoResponse
    created_at: datetime
    esta_vencido: bool = Field(
        default=False, description="Indica se o lote está vencido"
    )

    model_config = ConfigDict(from_attributes=True)

    @property
    def esta_vencido(self) -> bool:
        """Calcula se o lote está vencido"""
        return self.data_validade < date.today()


class LoteEstoqueList(BaseModel):
    """Schema para lista paginada de lotes"""

    items: list[LoteEstoqueResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ProdutoLoteFIFO(BaseModel):
    """Schema para sugestão de lote FIFO para saída"""

    lote_id: int
    numero_lote: str
    data_validade: date
    quantidade_disponivel: float
    custo_unitario: float
    esta_vencido: bool = Field(..., description="Indica se o lote está vencido")
    dias_para_vencer: int = Field(..., description="Dias restantes até a validade")

    model_config = ConfigDict(from_attributes=True)


class DarBaixaLoteRequest(BaseModel):
    """Schema para dar baixa em um lote"""

    lote_id: int = Field(..., gt=0, description="ID do lote")
    quantidade: float = Field(..., gt=0, description="Quantidade a dar baixa")

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, v: float) -> float:
        """Valida que a quantidade seja positiva"""
        if v <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return v


# ==================== SCHEMAS DE CURVA ABC ====================


class ClassificacaoABC(str, Enum):
    """Enum para classificação ABC"""

    A = "A"
    B = "B"
    C = "C"


class CurvaABCItem(BaseModel):
    """Item individual da Curva ABC"""

    produto_id: int
    produto_descricao: str
    codigo_barras: str
    quantidade_vendida: float = Field(..., description="Quantidade total vendida no período")
    valor_total_vendido: float = Field(..., description="Valor total de vendas no período")
    percentual_faturamento: float = Field(
        ..., description="Percentual em relação ao faturamento total"
    )
    percentual_acumulado: float = Field(
        ..., description="Percentual acumulado de faturamento"
    )
    classificacao: ClassificacaoABC = Field(..., description="Classificação ABC do produto")
    posicao_ranking: int = Field(..., description="Posição no ranking de faturamento")

    model_config = ConfigDict(from_attributes=True)


class CurvaABCResponse(BaseModel):
    """Schema de resposta para análise de Curva ABC"""

    periodo_meses: int = Field(..., description="Período analisado em meses")
    data_inicio: date = Field(..., description="Data inicial da análise")
    data_fim: date = Field(..., description="Data final da análise")
    faturamento_total: float = Field(..., description="Faturamento total do período")
    total_produtos: int = Field(..., description="Total de produtos analisados")
    produtos_classe_a: int = Field(..., description="Quantidade de produtos classe A")
    produtos_classe_b: int = Field(..., description="Quantidade de produtos classe B")
    produtos_classe_c: int = Field(..., description="Quantidade de produtos classe C")
    items: list[CurvaABCItem] = Field(..., description="Lista de produtos classificados")

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS WMS ====================


class TipoLocalizacaoEnum(str, Enum):
    """Enum para tipos de localização de estoque"""

    CORREDOR = "CORREDOR"
    PRATELEIRA = "PRATELEIRA"
    PALLET = "PALLET"
    DEPOSITO = "DEPOSITO"


class LocalizacaoEstoqueBase(BaseModel):
    """Schema base de Localização de Estoque"""

    codigo: str = Field(..., min_length=1, max_length=50, description="Código da localização")
    descricao: str = Field(..., min_length=1, max_length=200, description="Descrição da localização")
    tipo: TipoLocalizacaoEnum = Field(..., description="Tipo de localização")
    corredor: Optional[str] = Field(None, max_length=20, description="Código do corredor")
    prateleira: Optional[str] = Field(None, max_length=20, description="Código da prateleira")
    nivel: Optional[str] = Field(None, max_length=20, description="Nível/altura")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações")
    ativo: bool = Field(True, description="Localização ativa")


class LocalizacaoEstoqueCreate(LocalizacaoEstoqueBase):
    """Schema para criação de Localização de Estoque"""

    pass


class LocalizacaoEstoqueUpdate(BaseModel):
    """Schema para atualização de Localização de Estoque"""

    descricao: Optional[str] = Field(None, min_length=1, max_length=200, description="Descrição da localização")
    tipo: Optional[TipoLocalizacaoEnum] = Field(None, description="Tipo de localização")
    corredor: Optional[str] = Field(None, max_length=20, description="Código do corredor")
    prateleira: Optional[str] = Field(None, max_length=20, description="Código da prateleira")
    nivel: Optional[str] = Field(None, max_length=20, description="Nível/altura")
    observacoes: Optional[str] = Field(None, max_length=500, description="Observações")
    ativo: Optional[bool] = Field(None, description="Localização ativa")


class LocalizacaoEstoqueResponse(LocalizacaoEstoqueBase):
    """Schema de resposta de Localização de Estoque"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocalizacaoEstoqueList(BaseModel):
    """Schema para lista paginada de localizações"""

    items: list[LocalizacaoEstoqueResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ProdutoLocalizacaoBase(BaseModel):
    """Schema base de Produto-Localização"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    localizacao_id: int = Field(..., gt=0, description="ID da localização")
    quantidade: float = Field(0.0, ge=0, description="Quantidade na localização")
    quantidade_minima: Optional[float] = Field(None, ge=0, description="Quantidade mínima nesta localização")
    quantidade_maxima: Optional[float] = Field(None, ge=0, description="Quantidade máxima nesta localização")


class ProdutoLocalizacaoCreate(ProdutoLocalizacaoBase):
    """Schema para criação de Produto-Localização"""

    pass


class ProdutoLocalizacaoResponse(ProdutoLocalizacaoBase):
    """Schema de resposta de Produto-Localização"""

    id: int
    created_at: datetime
    updated_at: datetime
    localizacao: LocalizacaoEstoqueResponse

    model_config = ConfigDict(from_attributes=True)


class VincularProdutoLocalizacaoRequest(BaseModel):
    """Schema para vincular produto a localização"""

    localizacao_id: int = Field(..., gt=0, description="ID da localização")
    quantidade: float = Field(0.0, ge=0, description="Quantidade inicial na localização")
    quantidade_minima: Optional[float] = Field(None, ge=0, description="Quantidade mínima")
    quantidade_maxima: Optional[float] = Field(None, ge=0, description="Quantidade máxima")


class PickingListItem(BaseModel):
    """Item da lista de separação (picking)"""

    produto_id: int
    produto_descricao: str
    codigo_barras: str
    quantidade_necessaria: float
    localizacao_codigo: str
    localizacao_descricao: str
    localizacao_tipo: TipoLocalizacaoEnum
    quantidade_disponivel: float

    model_config = ConfigDict(from_attributes=True)


# ==================== SCHEMAS INVENTÁRIO ====================


class TipoInventarioEnum(str, Enum):
    """Enum para tipos de inventário"""

    GERAL = "GERAL"
    PARCIAL = "PARCIAL"
    ROTATIVO = "ROTATIVO"


class StatusInventarioEnum(str, Enum):
    """Enum para status de inventário"""

    ABERTA = "ABERTA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class FichaInventarioBase(BaseModel):
    """Schema base de Ficha de Inventário"""

    tipo: TipoInventarioEnum = Field(..., description="Tipo de inventário")
    observacoes: Optional[str] = Field(None, max_length=1000, description="Observações")
    usuario_responsavel_id: Optional[int] = Field(None, description="ID do usuário responsável")


class FichaInventarioCreate(FichaInventarioBase):
    """Schema para criação de Ficha de Inventário"""

    # Filtros opcionais para inventário PARCIAL ou ROTATIVO
    produto_ids: Optional[list[int]] = Field(None, description="IDs dos produtos para inventário parcial")
    localizacao_ids: Optional[list[int]] = Field(None, description="IDs das localizações para inventário parcial")
    categoria_ids: Optional[list[int]] = Field(None, description="IDs das categorias para inventário parcial")


class FichaInventarioResponse(FichaInventarioBase):
    """Schema de resposta de Ficha de Inventário"""

    id: int
    data_geracao: datetime
    data_inicio: Optional[datetime]
    data_conclusao: Optional[datetime]
    status: StatusInventarioEnum
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FichaInventarioList(BaseModel):
    """Schema para lista paginada de fichas de inventário"""

    items: list[FichaInventarioResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ItemInventarioBase(BaseModel):
    """Schema base de Item de Inventário"""

    produto_id: int = Field(..., gt=0, description="ID do produto")
    localizacao_id: Optional[int] = Field(None, description="ID da localização (opcional)")
    quantidade_sistema: float = Field(..., ge=0, description="Quantidade registrada no sistema")


class ItemInventarioCreate(ItemInventarioBase):
    """Schema para criação de Item de Inventário"""

    ficha_id: int = Field(..., gt=0, description="ID da ficha de inventário")


class ItemInventarioUpdate(BaseModel):
    """Schema para atualização de Item de Inventário (registro de contagem)"""

    quantidade_contada: float = Field(..., ge=0, description="Quantidade contada fisicamente")
    justificativa: Optional[str] = Field(None, max_length=500, description="Justificativa da divergência")
    conferido_por_id: Optional[int] = Field(None, description="ID do usuário que conferiu")


class ItemInventarioResponse(ItemInventarioBase):
    """Schema de resposta de Item de Inventário"""

    id: int
    ficha_id: int
    quantidade_contada: Optional[float]
    divergencia: Optional[float]
    justificativa: Optional[str]
    conferido_por_id: Optional[int]
    data_contagem: Optional[datetime]
    created_at: datetime
    produto: ProdutoResponse
    localizacao: Optional[LocalizacaoEstoqueResponse]

    model_config = ConfigDict(from_attributes=True)


class RegistrarContagemRequest(BaseModel):
    """Schema para registrar contagem de um item"""

    item_id: int = Field(..., gt=0, description="ID do item de inventário")
    quantidade_contada: float = Field(..., ge=0, description="Quantidade contada")
    justificativa: Optional[str] = Field(None, max_length=500, description="Justificativa se houver divergência")
    conferido_por_id: Optional[int] = Field(None, description="ID do usuário que conferiu")


class IniciarContagemRequest(BaseModel):
    """Schema para iniciar contagem de inventário"""

    observacoes: Optional[str] = Field(None, max_length=1000, description="Observações sobre o início")


class FinalizarContagemRequest(BaseModel):
    """Schema para finalizar inventário"""

    ajustar_estoque: bool = Field(True, description="Se deve ajustar o estoque automaticamente")
    observacoes: Optional[str] = Field(None, max_length=1000, description="Observações finais")


class AcuracidadeResponse(BaseModel):
    """Schema de resposta de acuracidade de estoque"""

    total_itens: int = Field(..., description="Total de itens inventariados")
    itens_sem_divergencia: int = Field(..., description="Itens sem divergência")
    itens_com_divergencia: int = Field(..., description="Itens com divergência")
    percentual_acuracidade: float = Field(..., description="Percentual de acuracidade (0-100)")
    divergencia_total_positiva: float = Field(..., description="Total de divergências positivas (sobras)")
    divergencia_total_negativa: float = Field(..., description="Total de divergências negativas (faltas)")

    model_config = ConfigDict(from_attributes=True)


class DivergenciaItem(BaseModel):
    """Item com divergência no inventário"""

    produto_id: int
    produto_descricao: str
    codigo_barras: str
    quantidade_sistema: float
    quantidade_contada: float
    divergencia: float
    percentual_divergencia: float
    localizacao_codigo: Optional[str]

    model_config = ConfigDict(from_attributes=True)
