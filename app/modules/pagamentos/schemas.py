"""
Schemas Pydantic para Pagamentos
"""
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, validator

from app.modules.pagamentos.models import (
    TipoPagamento, StatusPagamento, TipoChavePix,
    StatusBoleto
)


# ==============================================================================
# PIX Schemas
# ==============================================================================

class ChavePixBase(BaseModel):
    """Schema base para ChavePix"""
    tipo: TipoChavePix
    chave: str = Field(..., min_length=1, max_length=255)
    descricao: Optional[str] = None
    banco: str = Field(..., min_length=1, max_length=100)
    agencia: str = Field(..., min_length=1, max_length=10)
    conta: str = Field(..., min_length=1, max_length=20)
    ativa: bool = True


class ChavePixCreate(ChavePixBase):
    """Schema para criação de ChavePix"""
    pass


class ChavePixInResponse(ChavePixBase):
    """Schema de ChavePix em resposta"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class TransacaoPixCreate(BaseModel):
    """Schema para criação de transação PIX"""
    chave_pix_id: int
    valor: Decimal = Field(..., gt=0, decimal_places=2)
    descricao: Optional[str] = None
    pagador_nome: Optional[str] = None
    pagador_documento: Optional[str] = None
    data_expiracao: Optional[datetime] = None
    webhook_url: Optional[str] = None


class TransacaoPixInResponse(BaseModel):
    """Schema de transação PIX em resposta"""
    id: int
    txid: str
    e2e_id: Optional[str]
    valor: Decimal
    descricao: Optional[str]
    pagador_nome: Optional[str]
    pagador_documento: Optional[str]
    status: StatusPagamento
    data_criacao: datetime
    data_pagamento: Optional[datetime]
    data_expiracao: Optional[datetime]
    qr_code_texto: Optional[str]
    qr_code_imagem: Optional[str]

    class Config:
        from_attributes = True


class WebhookPixPayload(BaseModel):
    """Payload de webhook PIX"""
    txid: str
    e2e_id: str
    valor: Decimal
    pagador_nome: str
    pagador_documento: str
    data_pagamento: datetime


# ==============================================================================
# Boleto Schemas
# ==============================================================================

class ConfiguracaoBoletoBase(BaseModel):
    """Schema base para ConfiguracaoBoleto"""
    banco_codigo: str = Field(..., min_length=3, max_length=3)
    banco_nome: str
    agencia: str
    agencia_dv: Optional[str] = None
    conta: str
    conta_dv: str
    cedente_nome: str
    cedente_documento: str = Field(..., min_length=11, max_length=14)
    cedente_endereco: Optional[str] = None
    carteira: str
    convenio: Optional[str] = None
    variacao_carteira: Optional[str] = None
    instrucoes: Optional[str] = None
    local_pagamento: str = "Pagável em qualquer banco até o vencimento"
    percentual_juros: Decimal = Field(default=0, ge=0, le=100, decimal_places=2)
    percentual_multa: Decimal = Field(default=0, ge=0, le=100, decimal_places=2)
    ativa: bool = True


class ConfiguracaoBoletoCreate(ConfiguracaoBoletoBase):
    """Schema para criação de ConfiguracaoBoleto"""
    pass


class ConfiguracaoBoletoInResponse(ConfiguracaoBoletoBase):
    """Schema de ConfiguracaoBoleto em resposta"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BoletoCreate(BaseModel):
    """Schema para criação de Boleto"""
    configuracao_id: int
    valor: Decimal = Field(..., gt=0, decimal_places=2)
    valor_desconto: Decimal = Field(default=0, ge=0, decimal_places=2)
    data_vencimento: date
    sacado_nome: str = Field(..., min_length=1, max_length=255)
    sacado_documento: str = Field(..., min_length=11, max_length=14)
    sacado_endereco: Optional[str] = None
    sacado_cep: Optional[str] = Field(None, min_length=8, max_length=8)
    sacado_cidade: Optional[str] = None
    sacado_uf: Optional[str] = Field(None, min_length=2, max_length=2)
    instrucoes: Optional[str] = None
    demonstrativo: Optional[str] = None

    @validator('data_vencimento')
    def valida_data_vencimento(cls, v):
        if v < date.today():
            raise ValueError('Data de vencimento não pode ser no passado')
        return v


class BoletoInResponse(BaseModel):
    """Schema de Boleto em resposta"""
    id: int
    nosso_numero: str
    numero_documento: str
    codigo_barras: Optional[str]
    linha_digitavel: Optional[str]
    valor: Decimal
    valor_desconto: Decimal
    valor_pago: Optional[Decimal]
    data_emissao: date
    data_vencimento: date
    data_pagamento: Optional[date]
    sacado_nome: str
    sacado_documento: str
    status: StatusBoleto
    registrado: bool
    pdf_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# Conciliação Schemas
# ==============================================================================

class ExtratoBancarioCreate(BaseModel):
    """Schema para criação de ExtratoBancario"""
    banco_codigo: str = Field(..., min_length=3, max_length=3)
    agencia: str
    conta: str
    data: date
    descricao: str
    documento: Optional[str] = None
    valor: Decimal = Field(..., decimal_places=2)
    tipo: str = Field(..., pattern='^[CD]$')  # C ou D
    saldo: Optional[Decimal] = Field(None, decimal_places=2)
    arquivo_origem: Optional[str] = None
    linha_arquivo: Optional[int] = None


class ExtratoBancarioInResponse(BaseModel):
    """Schema de ExtratoBancario em resposta"""
    id: int
    banco_codigo: str
    agencia: str
    conta: str
    data: date
    descricao: str
    documento: Optional[str]
    valor: Decimal
    tipo: str
    saldo: Optional[Decimal]
    conciliado: bool
    data_conciliacao: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ConciliacaoBancariaCreate(BaseModel):
    """Schema para criação de ConciliacaoBancaria"""
    tipo: str
    extrato_bancario_id: int
    transacao_pix_id: Optional[int] = None
    boleto_id: Optional[int] = None
    valor_sistema: Decimal = Field(..., decimal_places=2)
    valor_extrato: Decimal = Field(..., decimal_places=2)
    automatica: bool = False
    observacoes: Optional[str] = None


class ConciliacaoBancariaInResponse(BaseModel):
    """Schema de ConciliacaoBancaria em resposta"""
    id: int
    tipo: str
    valor_sistema: Decimal
    valor_extrato: Decimal
    diferenca: Decimal
    automatica: bool
    observacoes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# Import Schemas
# ==============================================================================

class ImportOFXRequest(BaseModel):
    """Request para importação de arquivo OFX"""
    banco_codigo: str
    agencia: str
    conta: str
    arquivo_base64: str  # Arquivo OFX em base64


class ImportCSVRequest(BaseModel):
    """Request para importação de arquivo CSV"""
    banco_codigo: str
    agencia: str
    conta: str
    arquivo_base64: str  # Arquivo CSV em base64
    separador: str = ","
    encoding: str = "utf-8"


# ==============================================================================
# CNAB Schemas
# ==============================================================================

class CNABRemessaRequest(BaseModel):
    """Request para geração de arquivo CNAB de remessa"""
    configuracao_id: int
    boleto_ids: list[int] = Field(..., min_items=1)
    formato: str = Field(..., pattern="^(240|400)$")  # 240 ou 400
    numero_remessa: int = Field(default=1, ge=1)


class CNABRetornoRequest(BaseModel):
    """Request para processamento de arquivo CNAB de retorno"""
    configuracao_id: int
    formato: str = Field(..., pattern="^(240|400)$")
    conteudo_arquivo: str  # Conteúdo do arquivo CNAB


class CNABRemessaResponse(BaseModel):
    """Response da geração de arquivo CNAB de remessa"""
    sucesso: bool
    formato: str
    total_boletos: int
    arquivo_base64: str  # Arquivo CNAB em base64
    nome_arquivo: str


class CNABRetornoResponse(BaseModel):
    """Response do processamento de arquivo CNAB de retorno"""
    sucesso: bool
    formato: str
    total_registros: int
    boletos_atualizados: int
    boletos_pagos: int
    erros: list[dict] = []
