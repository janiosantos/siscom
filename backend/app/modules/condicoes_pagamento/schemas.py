"""
Schemas Pydantic para Condicoes de Pagamento
"""
from datetime import datetime, date
from typing import Optional, List
from enum import Enum as PyEnum
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class TipoCondicaoEnum(str, PyEnum):
    """Enum de tipo de condição de pagamento"""
    AVISTA = "AVISTA"
    PRAZO = "PRAZO"
    PARCELADO = "PARCELADO"


# ==================== Schemas de Parcela Padrão ====================

class ParcelaPadraoBase(BaseModel):
    """Schema base de Parcela Padrão"""
    numero_parcela: int = Field(..., ge=1, description="Número da parcela")
    dias_vencimento: int = Field(..., ge=0, description="Dias até vencimento")
    percentual_valor: float = Field(..., ge=0.0, le=100.0, description="Percentual do valor total")

    @field_validator("percentual_valor")
    @classmethod
    def validar_percentual(cls, v: float) -> float:
        """Valida percentual"""
        if v < 0 or v > 100:
            raise ValueError("Percentual deve estar entre 0 e 100")
        # Arredonda para 2 casas decimais
        return round(v, 2)


class ParcelaPadraoCreate(ParcelaPadraoBase):
    """Schema para criação de Parcela Padrão"""
    pass


class ParcelaPadraoResponse(ParcelaPadraoBase):
    """Schema de resposta de Parcela Padrão"""
    id: int
    condicao_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Schemas de Condição de Pagamento ====================

class CondicaoPagamentoBase(BaseModel):
    """Schema base de Condição de Pagamento"""
    nome: str = Field(..., min_length=1, max_length=100, description="Nome da condição")
    descricao: Optional[str] = Field(None, max_length=500, description="Descrição da condição")
    tipo: TipoCondicaoEnum = Field(..., description="Tipo de condição de pagamento")
    quantidade_parcelas: int = Field(..., ge=1, description="Quantidade de parcelas")
    intervalo_dias: int = Field(..., ge=0, description="Intervalo em dias entre parcelas")
    entrada_percentual: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Percentual de entrada"
    )
    ativa: bool = Field(default=True, description="Condição ativa")

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        """Valida nome da condição"""
        if not v or not v.strip():
            raise ValueError("Nome não pode ser vazio")
        return v.strip()

    @field_validator("entrada_percentual")
    @classmethod
    def validar_entrada_percentual(cls, v: float) -> float:
        """Valida percentual de entrada"""
        if v < 0 or v > 100:
            raise ValueError("Percentual de entrada deve estar entre 0 e 100")
        return round(v, 2)

    @model_validator(mode='after')
    def validar_tipo_condicao(self):
        """Valida regras de negócio por tipo de condição"""
        if self.tipo == TipoCondicaoEnum.AVISTA:
            # À vista: 1 parcela, 0 dias
            if self.quantidade_parcelas != 1:
                raise ValueError("Condição à vista deve ter 1 parcela")
            if self.intervalo_dias != 0:
                raise ValueError("Condição à vista deve ter 0 dias de intervalo")

        elif self.tipo == TipoCondicaoEnum.PRAZO:
            # A prazo: 1+ parcelas
            if self.quantidade_parcelas < 1:
                raise ValueError("Condição a prazo deve ter no mínimo 1 parcela")

        elif self.tipo == TipoCondicaoEnum.PARCELADO:
            # Parcelado: 2+ parcelas
            if self.quantidade_parcelas < 2:
                raise ValueError("Condição parcelada deve ter no mínimo 2 parcelas")

        return self


class CondicaoPagamentoCreate(CondicaoPagamentoBase):
    """Schema para criação de Condição de Pagamento"""
    parcelas: List[ParcelaPadraoCreate] = Field(
        default_factory=list, description="Lista de parcelas padrão"
    )

    @model_validator(mode='after')
    def validar_parcelas(self):
        """Valida parcelas"""
        if not self.parcelas:
            raise ValueError("É necessário informar as parcelas")

        # Valida quantidade de parcelas
        if len(self.parcelas) != self.quantidade_parcelas:
            raise ValueError(
                f"Quantidade de parcelas informada ({len(self.parcelas)}) "
                f"difere da quantidade configurada ({self.quantidade_parcelas})"
            )

        # Valida numeração sequencial
        numeros = [p.numero_parcela for p in self.parcelas]
        if sorted(numeros) != list(range(1, len(self.parcelas) + 1)):
            raise ValueError("Numeração das parcelas deve ser sequencial a partir de 1")

        # Valida soma de percentuais = 100%
        total_percentual = sum(p.percentual_valor for p in self.parcelas)
        if abs(total_percentual - 100.0) > 0.01:  # Tolerância de 0.01%
            raise ValueError(
                f"Soma dos percentuais das parcelas deve ser 100%. "
                f"Soma atual: {total_percentual:.2f}%"
            )

        return self


class CondicaoPagamentoUpdate(BaseModel):
    """Schema para atualização de Condição de Pagamento"""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    descricao: Optional[str] = Field(None, max_length=500)
    tipo: Optional[TipoCondicaoEnum] = None
    quantidade_parcelas: Optional[int] = Field(None, ge=1)
    intervalo_dias: Optional[int] = Field(None, ge=0)
    entrada_percentual: Optional[float] = Field(None, ge=0.0, le=100.0)
    ativa: Optional[bool] = None
    parcelas: Optional[List[ParcelaPadraoCreate]] = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: Optional[str]) -> Optional[str]:
        """Valida nome da condição"""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Nome não pode ser vazio")
        return v.strip()

    @field_validator("entrada_percentual")
    @classmethod
    def validar_entrada_percentual(cls, v: Optional[float]) -> Optional[float]:
        """Valida percentual de entrada"""
        if v is None:
            return None
        if v < 0 or v > 100:
            raise ValueError("Percentual de entrada deve estar entre 0 e 100")
        return round(v, 2)

    @model_validator(mode='after')
    def validar_atualizacao(self):
        """Valida atualização"""
        # Se está atualizando parcelas, valida soma de percentuais
        if self.parcelas is not None:
            if not self.parcelas:
                raise ValueError("Lista de parcelas não pode ser vazia")

            # Valida soma de percentuais = 100%
            total_percentual = sum(p.percentual_valor for p in self.parcelas)
            if abs(total_percentual - 100.0) > 0.01:
                raise ValueError(
                    f"Soma dos percentuais das parcelas deve ser 100%. "
                    f"Soma atual: {total_percentual:.2f}%"
                )

            # Valida quantidade de parcelas se foi informada
            if self.quantidade_parcelas is not None:
                if len(self.parcelas) != self.quantidade_parcelas:
                    raise ValueError(
                        f"Quantidade de parcelas informada ({len(self.parcelas)}) "
                        f"difere da quantidade configurada ({self.quantidade_parcelas})"
                    )

        return self


class CondicaoPagamentoResponse(CondicaoPagamentoBase):
    """Schema de resposta de Condição de Pagamento"""
    id: int
    created_at: datetime
    updated_at: datetime
    parcelas: List[ParcelaPadraoResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CondicaoPagamentoList(BaseModel):
    """Schema para lista paginada de condições de pagamento"""
    items: List[CondicaoPagamentoResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ==================== Schemas para cálculo de parcelas ====================

class ParcelaCalculada(BaseModel):
    """Schema para parcela calculada"""
    numero_parcela: int = Field(..., description="Número da parcela")
    valor: float = Field(..., description="Valor da parcela")
    vencimento: date = Field(..., description="Data de vencimento")
    percentual: float = Field(..., description="Percentual do total")


class CalcularParcelasRequest(BaseModel):
    """Schema para requisição de cálculo de parcelas"""
    condicao_id: int = Field(..., description="ID da condição de pagamento")
    valor_total: float = Field(..., gt=0, description="Valor total a ser parcelado")
    data_base: Optional[date] = Field(
        default=None, description="Data base para cálculo (padrão: hoje)"
    )

    @field_validator("valor_total")
    @classmethod
    def validar_valor(cls, v: float) -> float:
        """Valida valor total"""
        if v <= 0:
            raise ValueError("Valor total deve ser maior que zero")
        return round(v, 2)


class CalcularParcelasResponse(BaseModel):
    """Schema de resposta do cálculo de parcelas"""
    condicao: CondicaoPagamentoResponse
    valor_total: float
    parcelas: List[ParcelaCalculada]
