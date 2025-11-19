"""
Schemas Pydantic para Ordens de Serviço
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


# Enums
class StatusOSEnum(str, Enum):
    """Enum para status da OS"""

    ABERTA = "ABERTA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"
    FATURADA = "FATURADA"


# ====================================
# TIPO SERVIÇO SCHEMAS
# ====================================


class TipoServicoBase(BaseModel):
    """Schema base para Tipo de Serviço"""

    nome: str = Field(..., min_length=1, max_length=100)
    descricao: Optional[str] = None
    preco_padrao: float = Field(default=0.0, ge=0)
    ativo: bool = True


class TipoServicoCreate(TipoServicoBase):
    """Schema para criar Tipo de Serviço"""

    pass


class TipoServicoUpdate(BaseModel):
    """Schema para atualizar Tipo de Serviço"""

    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = None
    preco_padrao: Optional[float] = Field(None, ge=0)
    ativo: Optional[bool] = None


class TipoServicoResponse(TipoServicoBase):
    """Schema de resposta para Tipo de Serviço"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TipoServicoList(BaseModel):
    """Schema para lista paginada de Tipos de Serviço"""

    items: List[TipoServicoResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ====================================
# TÉCNICO SCHEMAS
# ====================================


class TecnicoBase(BaseModel):
    """Schema base para Técnico"""

    usuario_id: Optional[int] = None
    nome: str = Field(..., min_length=1, max_length=200)
    cpf: str = Field(..., min_length=11, max_length=14)
    telefone: Optional[str] = Field(None, max_length=20)
    especialidades: Optional[str] = None
    ativo: bool = True


class TecnicoCreate(TecnicoBase):
    """Schema para criar Técnico"""

    pass


class TecnicoUpdate(BaseModel):
    """Schema para atualizar Técnico"""

    usuario_id: Optional[int] = None
    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    cpf: Optional[str] = Field(None, min_length=11, max_length=14)
    telefone: Optional[str] = Field(None, max_length=20)
    especialidades: Optional[str] = None
    ativo: Optional[bool] = None


class TecnicoResponse(TecnicoBase):
    """Schema de resposta para Técnico"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TecnicoList(BaseModel):
    """Schema para lista paginada de Técnicos"""

    items: List[TecnicoResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ====================================
# ITEM OS SCHEMAS
# ====================================


class ItemOSBase(BaseModel):
    """Schema base para Item de OS"""

    produto_id: int
    quantidade: float = Field(..., gt=0)
    preco_unitario: float = Field(..., ge=0)


class ItemOSCreate(ItemOSBase):
    """Schema para criar Item de OS"""

    pass


class ItemOSResponse(ItemOSBase):
    """Schema de resposta para Item de OS"""

    id: int
    os_id: int
    total_item: float
    created_at: datetime

    # Incluir dados do produto (lazy loaded)
    produto: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


# ====================================
# APONTAMENTO HORAS SCHEMAS
# ====================================


class ApontamentoHorasBase(BaseModel):
    """Schema base para Apontamento de Horas"""

    tecnico_id: int
    data: datetime
    horas_trabalhadas: float = Field(..., gt=0)
    descricao: Optional[str] = None


class ApontamentoHorasCreate(ApontamentoHorasBase):
    """Schema para criar Apontamento de Horas"""

    pass


class ApontamentoHorasResponse(ApontamentoHorasBase):
    """Schema de resposta para Apontamento de Horas"""

    id: int
    os_id: int
    created_at: datetime

    # Incluir dados do técnico (lazy loaded)
    tecnico: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


# ====================================
# ORDEM SERVIÇO SCHEMAS
# ====================================


class OrdemServicoBase(BaseModel):
    """Schema base para Ordem de Serviço"""

    cliente_id: int
    tecnico_id: int
    tipo_servico_id: int
    produto_id: Optional[int] = None
    numero_serie: Optional[str] = Field(None, max_length=100)
    data_prevista: Optional[datetime] = None
    descricao_problema: Optional[str] = None
    valor_mao_obra: float = Field(default=0.0, ge=0)
    observacoes: Optional[str] = None


class OrdemServicoCreate(OrdemServicoBase):
    """Schema para criar Ordem de Serviço"""

    pass


class OrdemServicoUpdate(BaseModel):
    """Schema para atualizar Ordem de Serviço"""

    tecnico_id: Optional[int] = None
    tipo_servico_id: Optional[int] = None
    produto_id: Optional[int] = None
    numero_serie: Optional[str] = Field(None, max_length=100)
    data_prevista: Optional[datetime] = None
    descricao_problema: Optional[str] = None
    valor_mao_obra: Optional[float] = Field(None, ge=0)
    observacoes: Optional[str] = None


class OrdemServicoResponse(OrdemServicoBase):
    """Schema de resposta para Ordem de Serviço"""

    id: int
    data_abertura: datetime
    data_conclusao: Optional[datetime] = None
    status: StatusOSEnum
    descricao_solucao: Optional[str] = None
    valor_total: float
    created_at: datetime
    updated_at: datetime

    # Relacionamentos
    cliente: Optional[dict] = None
    tecnico: Optional[dict] = None
    tipo_servico: Optional[dict] = None
    produto: Optional[dict] = None
    itens: List[ItemOSResponse] = []
    apontamentos: List[ApontamentoHorasResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrdemServicoList(BaseModel):
    """Schema para lista paginada de Ordens de Serviço"""

    items: List[OrdemServicoResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ====================================
# SCHEMAS DE AÇÕES ESPECÍFICAS
# ====================================


class AtribuirTecnicoRequest(BaseModel):
    """Schema para atribuir/reatribuir técnico"""

    tecnico_id: int


class IniciarOSRequest(BaseModel):
    """Schema para iniciar OS (opcional)"""

    observacoes: Optional[str] = None


class AdicionarMaterialRequest(BaseModel):
    """Schema para adicionar material à OS"""

    produto_id: int
    quantidade: float = Field(..., gt=0)
    preco_unitario: float = Field(..., ge=0)


class ApontarHorasRequest(BaseModel):
    """Schema para apontar horas trabalhadas"""

    tecnico_id: int
    data: datetime
    horas_trabalhadas: float = Field(..., gt=0)
    descricao: Optional[str] = None


class FinalizarOSRequest(BaseModel):
    """Schema para finalizar OS"""

    data_conclusao: datetime
    descricao_solucao: str = Field(..., min_length=1)


class FaturarOSRequest(BaseModel):
    """Schema para faturar OS"""

    vendedor_id: int
    condicao_pagamento_id: int
    forma_pagamento: str = Field(..., min_length=1)
    desconto: float = Field(default=0.0, ge=0)
    observacoes: Optional[str] = None


class CancelarOSRequest(BaseModel):
    """Schema para cancelar OS"""

    motivo: str = Field(..., min_length=1)
