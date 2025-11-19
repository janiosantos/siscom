"""
Schemas para CRM e Análise RFM
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ClienteRFM(BaseModel):
    """Cliente com análise RFM"""

    cliente_id: int
    cliente_nome: str
    recencia_dias: int = Field(..., description="Dias desde última compra")
    frequencia: int = Field(..., description="Total de compras")
    monetario: float = Field(..., description="Valor total gasto")
    ticket_medio: float
    score_r: int = Field(..., ge=1, le=5, description="Score de Recência (1-5)")
    score_f: int = Field(..., ge=1, le=5, description="Score de Frequência (1-5)")
    score_m: int = Field(..., ge=1, le=5, description="Score de Monetário (1-5)")
    segmento_rfm: str = Field(..., description="Segmento baseado em RFM")
    ultima_compra: Optional[datetime] = None


class AnaliseRFMResponse(BaseModel):
    """Resposta de análise RFM"""

    data_analise: datetime
    total_clientes: int
    clientes: list[ClienteRFM]


class SegmentoClientes(BaseModel):
    """Segmento de clientes"""

    segmento: str
    descricao: str
    total_clientes: int
    valor_total: float
    percentual_clientes: float
    percentual_valor: float


class RelatorioSegmentosResponse(BaseModel):
    """Relatório de segmentos de clientes"""

    data_analise: datetime
    total_clientes: int
    valor_total: float
    segmentos: list[SegmentoClientes]


class ClienteDetalhado(BaseModel):
    """Cliente com informações detalhadas"""

    cliente_id: int
    nome: str
    email: Optional[str]
    telefone: Optional[str]
    cpf_cnpj: Optional[str]
    total_compras: int
    valor_total_comprado: float
    ticket_medio: float
    ultima_compra: Optional[datetime]
    dias_desde_ultima_compra: Optional[int]
    pontos_fidelidade: int = 0


class TopClientesResponse(BaseModel):
    """Top clientes por valor"""

    periodo_inicio: date
    periodo_fim: date
    clientes: list[ClienteDetalhado]
    total_clientes: int
