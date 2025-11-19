"""
Schemas para Integração E-commerce
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class PlataformaEcommerceEnum(str, Enum):
    """Enum para plataformas de e-commerce"""

    WOOCOMMERCE = "WOOCOMMERCE"
    MAGENTO = "MAGENTO"
    TRAY = "TRAY"
    SHOPIFY = "SHOPIFY"
    VTEX = "VTEX"
    OUTRO = "OUTRO"


class StatusPedidoEcommerceEnum(str, Enum):
    """Enum para status de pedido"""

    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    FATURADO = "FATURADO"
    ENVIADO = "ENVIADO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"
    ERRO = "ERRO"


# ==================== CONFIGURAÇÃO ====================


class ConfiguracaoEcommerceBase(BaseModel):
    """Schema base de Configuração E-commerce"""

    plataforma: PlataformaEcommerceEnum
    nome: str = Field(..., min_length=1, max_length=100)
    url_loja: str = Field(..., min_length=1, max_length=500)
    api_key: str = Field(..., min_length=1, max_length=500)
    api_secret: Optional[str] = Field(None, max_length=500)
    sincronizar_produtos: bool = True
    sincronizar_estoque: bool = True
    sincronizar_precos: bool = True
    receber_pedidos: bool = True
    intervalo_sincronizacao_minutos: int = Field(15, ge=1, le=1440)
    ativo: bool = True


class ConfiguracaoEcommerceCreate(ConfiguracaoEcommerceBase):
    """Schema para criação de configuração"""

    pass


class ConfiguracaoEcommerceUpdate(BaseModel):
    """Schema para atualização de configuração"""

    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    url_loja: Optional[str] = Field(None, min_length=1, max_length=500)
    api_key: Optional[str] = Field(None, min_length=1, max_length=500)
    api_secret: Optional[str] = Field(None, max_length=500)
    sincronizar_produtos: Optional[bool] = None
    sincronizar_estoque: Optional[bool] = None
    sincronizar_precos: Optional[bool] = None
    receber_pedidos: Optional[bool] = None
    intervalo_sincronizacao_minutos: Optional[int] = Field(None, ge=1, le=1440)
    ativo: Optional[bool] = None


class ConfiguracaoEcommerceResponse(ConfiguracaoEcommerceBase):
    """Schema de resposta de configuração"""

    id: int
    ultima_sincronizacao: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== PEDIDOS ====================


class ItemPedidoEcommerceBase(BaseModel):
    """Schema base de item de pedido"""

    produto_externo_id: str
    produto_sku: Optional[str] = None
    produto_nome: str
    quantidade: float
    preco_unitario: float
    preco_total: float


class ItemPedidoEcommerceResponse(ItemPedidoEcommerceBase):
    """Schema de resposta de item de pedido"""

    id: int
    pedido_id: int
    produto_id: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PedidoEcommerceBase(BaseModel):
    """Schema base de pedido e-commerce"""

    pedido_externo_id: str
    numero_pedido: str
    cliente_nome: str
    cliente_email: Optional[str] = None
    cliente_telefone: Optional[str] = None
    cliente_cpf_cnpj: Optional[str] = None
    valor_produtos: float
    valor_frete: float = 0
    valor_desconto: float = 0
    valor_total: float
    forma_pagamento: Optional[str] = None
    data_pedido: datetime


class PedidoEcommerceCreate(PedidoEcommerceBase):
    """Schema para criação de pedido e-commerce"""

    configuracao_id: int
    itens: list[ItemPedidoEcommerceBase]
    endereco_cep: Optional[str] = None
    endereco_logradouro: Optional[str] = None
    endereco_numero: Optional[str] = None
    endereco_complemento: Optional[str] = None
    endereco_bairro: Optional[str] = None
    endereco_cidade: Optional[str] = None
    endereco_uf: Optional[str] = None


class PedidoEcommerceResponse(PedidoEcommerceBase):
    """Schema de resposta de pedido"""

    id: int
    configuracao_id: int
    status: StatusPedidoEcommerceEnum
    venda_id: Optional[int]
    erro_integracao: Optional[str]
    data_recebimento: datetime
    data_processamento: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    itens: list[ItemPedidoEcommerceResponse]

    model_config = ConfigDict(from_attributes=True)


class PedidoEcommerceList(BaseModel):
    """Schema para lista paginada de pedidos"""

    items: list[PedidoEcommerceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ProcessarPedidoRequest(BaseModel):
    """Schema para processar pedido e-commerce (criar venda no ERP)"""

    criar_cliente: bool = Field(True, description="Se deve criar cliente caso não exista")


# ==================== SINCRONIZAÇÃO ====================


class SincronizarProdutoRequest(BaseModel):
    """Schema para sincronizar produto"""

    produto_ids: Optional[list[int]] = Field(None, description="IDs específicos (ou todos se None)")


class SincronizarEstoqueRequest(BaseModel):
    """Schema para sincronizar estoque"""

    produto_ids: Optional[list[int]] = Field(None, description="IDs específicos (ou todos se None)")


class ResultadoSincronizacao(BaseModel):
    """Schema de resultado de sincronização"""

    tipo: str
    total_processados: int
    total_sucesso: int
    total_erro: int
    tempo_execucao_segundos: float
    mensagens: list[str] = []


class LogSincronizacaoResponse(BaseModel):
    """Schema de resposta de log"""

    id: int
    configuracao_id: int
    tipo_sincronizacao: str
    produto_id: Optional[int]
    sucesso: bool
    mensagem: Optional[str]
    tempo_execucao_ms: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
