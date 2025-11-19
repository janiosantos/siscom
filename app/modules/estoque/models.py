"""
Modelos de Estoque
"""
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Date, Numeric, Integer, ForeignKey, Index, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class TipoMovimentacao(str, PyEnum):
    """Enum para tipos de movimentação de estoque"""

    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    AJUSTE = "AJUSTE"
    TRANSFERENCIA = "TRANSFERENCIA"
    DEVOLUCAO = "DEVOLUCAO"


class MovimentacaoEstoque(Base):
    """Modelo de Movimentação de Estoque"""

    __tablename__ = "movimentacoes_estoque"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    tipo: Mapped[TipoMovimentacao] = mapped_column(
        Enum(TipoMovimentacao), nullable=False, index=True
    )
    quantidade: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    custo_unitario: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    valor_total: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    documento_referencia: Mapped[str] = mapped_column(
        String(100), nullable=True, index=True
    )
    observacao: Mapped[str] = mapped_column(String(500), nullable=True)
    usuario_id: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relacionamentos
    produto: Mapped["Produto"] = relationship("Produto", lazy="selectin")

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_movimentacao_produto_tipo", "produto_id", "tipo"),
        Index("idx_movimentacao_produto_data", "produto_id", "created_at"),
        Index("idx_movimentacao_data_tipo", "created_at", "tipo"),
    )

    def __repr__(self) -> str:
        return f"<MovimentacaoEstoque(id={self.id}, produto_id={self.produto_id}, tipo='{self.tipo}', quantidade={self.quantidade})>"


class LoteEstoque(Base):
    """Modelo de Lote de Estoque para controle FIFO"""

    __tablename__ = "lotes_estoque"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    numero_lote: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    data_fabricacao: Mapped[date] = mapped_column(Date, nullable=True)
    data_validade: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantidade_inicial: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    quantidade_atual: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, index=True
    )
    custo_unitario: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    documento_referencia: Mapped[str] = mapped_column(
        String(100), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Relacionamentos
    produto: Mapped["Produto"] = relationship("Produto", lazy="selectin")

    # Índices compostos para otimização de consultas FIFO
    __table_args__ = (
        Index("idx_lote_produto_validade", "produto_id", "data_validade"),
        Index("idx_lote_produto_disponivel", "produto_id", "quantidade_atual"),
        Index("idx_lote_numero", "numero_lote"),
    )

    def __repr__(self) -> str:
        return f"<LoteEstoque(id={self.id}, numero_lote='{self.numero_lote}', produto_id={self.produto_id}, quantidade_atual={self.quantidade_atual})>"


# ==================== MODELOS WMS ====================


class TipoLocalizacao(str, PyEnum):
    """Enum para tipos de localização de estoque"""

    CORREDOR = "CORREDOR"
    PRATELEIRA = "PRATELEIRA"
    PALLET = "PALLET"
    DEPOSITO = "DEPOSITO"


class LocalizacaoEstoque(Base):
    """Modelo de Localização Física de Estoque (WMS)"""

    __tablename__ = "localizacoes_estoque"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    descricao: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[TipoLocalizacao] = mapped_column(
        Enum(TipoLocalizacao), nullable=False, index=True
    )
    corredor: Mapped[str] = mapped_column(String(20), nullable=True)
    prateleira: Mapped[str] = mapped_column(String(20), nullable=True)
    nivel: Mapped[str] = mapped_column(String(20), nullable=True)
    observacoes: Mapped[str] = mapped_column(String(500), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    produtos_localizacoes: Mapped[list["ProdutoLocalizacao"]] = relationship(
        "ProdutoLocalizacao", back_populates="localizacao", lazy="selectin"
    )

    # Índices compostos
    __table_args__ = (
        Index("idx_localizacao_codigo", "codigo"),
        Index("idx_localizacao_tipo_ativo", "tipo", "ativo"),
        Index("idx_localizacao_corredor_prateleira", "corredor", "prateleira", "nivel"),
    )

    def __repr__(self) -> str:
        return f"<LocalizacaoEstoque(id={self.id}, codigo='{self.codigo}', tipo='{self.tipo}')>"


class ProdutoLocalizacao(Base):
    """Modelo de vínculo entre Produto e Localização (onde o produto está armazenado)"""

    __tablename__ = "produtos_localizacoes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    localizacao_id: Mapped[int] = mapped_column(
        ForeignKey("localizacoes_estoque.id"), nullable=False, index=True
    )
    quantidade: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    quantidade_minima: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    quantidade_maxima: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    produto: Mapped["Produto"] = relationship("Produto", lazy="selectin")
    localizacao: Mapped["LocalizacaoEstoque"] = relationship(
        "LocalizacaoEstoque", back_populates="produtos_localizacoes", lazy="selectin"
    )

    # Índices compostos
    __table_args__ = (
        Index("idx_produto_localizacao", "produto_id", "localizacao_id", unique=True),
        Index("idx_localizacao_quantidade", "localizacao_id", "quantidade"),
    )

    def __repr__(self) -> str:
        return f"<ProdutoLocalizacao(id={self.id}, produto_id={self.produto_id}, localizacao_id={self.localizacao_id}, quantidade={self.quantidade})>"


# ==================== MODELOS INVENTÁRIO ====================


class TipoInventario(str, PyEnum):
    """Enum para tipos de inventário"""

    GERAL = "GERAL"
    PARCIAL = "PARCIAL"
    ROTATIVO = "ROTATIVO"


class StatusInventario(str, PyEnum):
    """Enum para status de inventário"""

    ABERTA = "ABERTA"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


class FichaInventario(Base):
    """Modelo de Ficha de Inventário"""

    __tablename__ = "fichas_inventario"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    data_geracao: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    data_inicio: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    data_conclusao: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    tipo: Mapped[TipoInventario] = mapped_column(
        Enum(TipoInventario), nullable=False, index=True
    )
    status: Mapped[StatusInventario] = mapped_column(
        Enum(StatusInventario), nullable=False, default=StatusInventario.ABERTA, index=True
    )
    usuario_responsavel_id: Mapped[int] = mapped_column(Integer, nullable=True)
    observacoes: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    itens: Mapped[list["ItemInventario"]] = relationship(
        "ItemInventario", back_populates="ficha", lazy="selectin"
    )

    # Índices compostos
    __table_args__ = (
        Index("idx_inventario_tipo_status", "tipo", "status"),
        Index("idx_inventario_data_geracao", "data_geracao"),
    )

    def __repr__(self) -> str:
        return f"<FichaInventario(id={self.id}, tipo='{self.tipo}', status='{self.status}')>"


class ItemInventario(Base):
    """Modelo de Item de Inventário"""

    __tablename__ = "itens_inventario"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ficha_id: Mapped[int] = mapped_column(
        ForeignKey("fichas_inventario.id"), nullable=False, index=True
    )
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id"), nullable=False, index=True
    )
    localizacao_id: Mapped[int] = mapped_column(
        ForeignKey("localizacoes_estoque.id"), nullable=True, index=True
    )
    quantidade_sistema: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    quantidade_contada: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    divergencia: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    justificativa: Mapped[str] = mapped_column(String(500), nullable=True)
    conferido_por_id: Mapped[int] = mapped_column(Integer, nullable=True)
    data_contagem: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    ficha: Mapped["FichaInventario"] = relationship(
        "FichaInventario", back_populates="itens", lazy="selectin"
    )
    produto: Mapped["Produto"] = relationship("Produto", lazy="selectin")
    localizacao: Mapped["LocalizacaoEstoque"] = relationship(
        "LocalizacaoEstoque", lazy="selectin"
    )

    # Índices compostos
    __table_args__ = (
        Index("idx_item_ficha_produto", "ficha_id", "produto_id"),
        Index("idx_item_localizacao", "localizacao_id"),
    )

    def __repr__(self) -> str:
        return f"<ItemInventario(id={self.id}, ficha_id={self.ficha_id}, produto_id={self.produto_id}, divergencia={self.divergencia})>"
