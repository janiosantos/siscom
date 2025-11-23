"""
Schemas Pydantic para Notas Fiscais
"""
from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TipoNotaEnum(str, Enum):
    """Enum para tipos de nota"""

    NFE = "NFE"
    NFCE = "NFCE"
    NFSE = "NFSE"


class StatusNotaEnum(str, Enum):
    """Enum para status de nota"""

    PENDENTE = "PENDENTE"
    AUTORIZADA = "AUTORIZADA"
    CANCELADA = "CANCELADA"
    REJEITADA = "REJEITADA"


class NotaFiscalBase(BaseModel):
    """Schema base de Nota Fiscal"""

    tipo: TipoNotaEnum = Field(default=TipoNotaEnum.NFE, description="Tipo da nota")
    numero: str = Field(..., min_length=1, max_length=20, description="Número da nota")
    serie: str = Field(default="1", max_length=10, description="Série da nota")
    chave_acesso: str = Field(..., min_length=44, max_length=44, description="Chave de acesso de 44 dígitos")
    data_emissao: datetime = Field(..., description="Data de emissão da nota")

    fornecedor_id: Optional[int] = Field(None, description="ID do fornecedor")
    cliente_id: Optional[int] = Field(None, description="ID do cliente")
    venda_id: Optional[int] = Field(None, description="ID da venda (FK opcional)")

    valor_produtos: float = Field(default=0.0, ge=0, description="Valor dos produtos")
    valor_total: float = Field(default=0.0, ge=0, description="Valor total da nota")
    valor_icms: float = Field(default=0.0, ge=0, description="Valor do ICMS")
    valor_ipi: float = Field(default=0.0, ge=0, description="Valor do IPI")

    observacoes: Optional[str] = Field(None, description="Observações da nota")

    @field_validator("chave_acesso")
    @classmethod
    def validar_chave_acesso(cls, v: str) -> str:
        """Valida chave de acesso com 44 dígitos"""
        if not v:
            raise ValueError("Chave de acesso é obrigatória")

        v = v.strip().replace(" ", "")

        if not v.isdigit():
            raise ValueError("Chave de acesso deve conter apenas números")

        if len(v) != 44:
            raise ValueError("Chave de acesso deve ter exatamente 44 dígitos")

        return v


class NotaFiscalCreate(NotaFiscalBase):
    """Schema para criação de Nota Fiscal"""

    xml_nfe: Optional[str] = Field(None, description="XML da NF-e")
    status: StatusNotaEnum = Field(
        default=StatusNotaEnum.PENDENTE, description="Status da nota"
    )


class NotaFiscalResponse(NotaFiscalBase):
    """Schema de resposta de Nota Fiscal"""

    id: int
    status: StatusNotaEnum
    protocolo_autorizacao: Optional[str] = None
    data_autorizacao: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotaFiscalList(BaseModel):
    """Schema para lista paginada de notas fiscais"""

    items: list[NotaFiscalResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ImportarXMLCreate(BaseModel):
    """Schema para importação de XML de NF-e"""

    xml_content: str = Field(..., description="Conteúdo do XML da NF-e")
    registrar_entrada_estoque: bool = Field(
        default=True, description="Se deve registrar entrada de estoque"
    )
    criar_conta_pagar: bool = Field(
        default=True, description="Se deve criar conta a pagar"
    )


class EmitirNFCeCreate(BaseModel):
    """Schema para emissão de NFC-e"""

    venda_id: int = Field(..., gt=0, description="ID da venda")
    serie: str = Field(default="1", max_length=10, description="Série da NFC-e")
    observacoes: Optional[str] = Field(None, description="Observações da NFC-e")


class CancelarNotaRequest(BaseModel):
    """Schema para cancelamento de nota"""

    motivo: str = Field(
        ..., min_length=15, max_length=255, description="Motivo do cancelamento"
    )


class ConsultarNotaResponse(NotaFiscalResponse):
    """Schema estendido para consulta de nota com XML"""

    xml_nfe: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
