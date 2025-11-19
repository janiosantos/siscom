"""
Modelos para Integração E-commerce
"""
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Boolean, Integer, Numeric, Text, Enum, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StatusPedidoEcommerce(str, PyEnum):
    """Enum para status de pedido do e-commerce"""

    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    FATURADO = "FATURADO"
    ENVIADO = "ENVIADO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"
    ERRO = "ERRO"


class PlataformaEcommerce(str, PyEnum):
    """Enum para plataformas de e-commerce suportadas"""

    WOOCOMMERCE = "WOOCOMMERCE"
    MAGENTO = "MAGENTO"
    TRAY = "TRAY"
    SHOPIFY = "SHOPIFY"
    VTEX = "VTEX"
    OUTRO = "OUTRO"


class ConfiguracaoEcommerce(Base):
    """Modelo de Configuração de Integração E-commerce"""

    __tablename__ = "configuracoes_ecommerce"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plataforma: Mapped[PlataformaEcommerce] = mapped_column(
        Enum(PlataformaEcommerce), nullable=False
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    url_loja: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key: Mapped[str] = mapped_column(String(500), nullable=False)
    api_secret: Mapped[str] = mapped_column(String(500), nullable=True)
    sincronizar_produtos: Mapped[bool] = mapped_column(Boolean, default=True)
    sincronizar_estoque: Mapped[bool] = mapped_column(Boolean, default=True)
    sincronizar_precos: Mapped[bool] = mapped_column(Boolean, default=True)
    receber_pedidos: Mapped[bool] = mapped_column(Boolean, default=True)
    intervalo_sincronizacao_minutos: Mapped[int] = mapped_column(Integer, default=15)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ultima_sincronizacao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<ConfiguracaoEcommerce(id={self.id}, plataforma='{self.plataforma}', nome='{self.nome}')>"


class PedidoEcommerce(Base):
    """Modelo de Pedido recebido do E-commerce"""

    __tablename__ = "pedidos_ecommerce"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    configuracao_id: Mapped[int] = mapped_column(
        ForeignKey("configuracoes_ecommerce.id"), nullable=False, index=True
    )
    pedido_externo_id: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True,
        comment="ID do pedido na plataforma de e-commerce"
    )
    numero_pedido: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="Número do pedido para exibição"
    )
    status: Mapped[StatusPedidoEcommerce] = mapped_column(
        Enum(StatusPedidoEcommerce), nullable=False, default=StatusPedidoEcommerce.PENDENTE, index=True
    )

    # Dados do cliente
    cliente_nome: Mapped[str] = mapped_column(String(200), nullable=False)
    cliente_email: Mapped[str] = mapped_column(String(200), nullable=True)
    cliente_telefone: Mapped[str] = mapped_column(String(20), nullable=True)
    cliente_cpf_cnpj: Mapped[str] = mapped_column(String(20), nullable=True)

    # Endereço de entrega
    endereco_cep: Mapped[str] = mapped_column(String(10), nullable=True)
    endereco_logradouro: Mapped[str] = mapped_column(String(200), nullable=True)
    endereco_numero: Mapped[str] = mapped_column(String(20), nullable=True)
    endereco_complemento: Mapped[str] = mapped_column(String(100), nullable=True)
    endereco_bairro: Mapped[str] = mapped_column(String(100), nullable=True)
    endereco_cidade: Mapped[str] = mapped_column(String(100), nullable=True)
    endereco_uf: Mapped[str] = mapped_column(String(2), nullable=True)

    # Valores
    valor_produtos: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    valor_frete: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    valor_desconto: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    valor_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Forma de pagamento
    forma_pagamento: Mapped[str] = mapped_column(String(100), nullable=True)

    # Integração com o ERP
    venda_id: Mapped[int | None] = mapped_column(
        ForeignKey("vendas.id"), nullable=True, index=True,
        comment="ID da venda criada no ERP"
    )

    # Dados JSON completos do pedido (para referência)
    dados_completos: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Erros
    erro_integracao: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Datas
    data_pedido: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    data_recebimento: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    data_processamento: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    configuracao: Mapped["ConfiguracaoEcommerce"] = relationship(
        "ConfiguracaoEcommerce", lazy="selectin"
    )
    itens: Mapped[list["ItemPedidoEcommerce"]] = relationship(
        "ItemPedidoEcommerce", back_populates="pedido", lazy="selectin"
    )

    # Índices compostos
    __table_args__ = (
        Index("idx_pedido_ecommerce_externo", "configuracao_id", "pedido_externo_id", unique=True),
        Index("idx_pedido_ecommerce_status_data", "status", "data_pedido"),
    )

    def __repr__(self) -> str:
        return f"<PedidoEcommerce(id={self.id}, numero='{self.numero_pedido}', status='{self.status}')>"


class ItemPedidoEcommerce(Base):
    """Modelo de Item de Pedido do E-commerce"""

    __tablename__ = "itens_pedido_ecommerce"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos_ecommerce.id"), nullable=False, index=True
    )
    produto_id: Mapped[int | None] = mapped_column(
        ForeignKey("produtos.id"), nullable=True, index=True,
        comment="ID do produto no ERP (mapeado)"
    )

    # Dados do produto no e-commerce
    produto_externo_id: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="ID do produto na plataforma de e-commerce"
    )
    produto_sku: Mapped[str] = mapped_column(String(100), nullable=True)
    produto_nome: Mapped[str] = mapped_column(String(200), nullable=False)

    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    preco_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    pedido: Mapped["PedidoEcommerce"] = relationship(
        "PedidoEcommerce", back_populates="itens", lazy="selectin"
    )

    # Índices
    __table_args__ = (
        Index("idx_item_pedido_ecommerce", "pedido_id", "produto_id"),
    )

    def __repr__(self) -> str:
        return f"<ItemPedidoEcommerce(id={self.id}, produto='{self.produto_nome}', quantidade={self.quantidade})>"


class LogSincronizacao(Base):
    """Modelo de Log de Sincronização com E-commerce"""

    __tablename__ = "logs_sincronizacao"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    configuracao_id: Mapped[int] = mapped_column(
        ForeignKey("configuracoes_ecommerce.id"), nullable=False, index=True
    )
    tipo_sincronizacao: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="PRODUTO, ESTOQUE, PRECO, PEDIDO"
    )
    produto_id: Mapped[int | None] = mapped_column(
        ForeignKey("produtos.id"), nullable=True, index=True
    )
    sucesso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)
    detalhes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tempo_execucao_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relacionamentos
    configuracao: Mapped["ConfiguracaoEcommerce"] = relationship(
        "ConfiguracaoEcommerce", lazy="selectin"
    )

    # Índices
    __table_args__ = (
        Index("idx_log_sync_config_tipo", "configuracao_id", "tipo_sincronizacao"),
        Index("idx_log_sync_data", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<LogSincronizacao(id={self.id}, tipo='{self.tipo_sincronizacao}', sucesso={self.sucesso})>"
