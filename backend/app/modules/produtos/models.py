"""
Modelos de Produtos
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Numeric, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Produto(Base):
    """Modelo de Produto"""

    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo_barras: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    descricao: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    categoria_id: Mapped[int] = mapped_column(
        ForeignKey("categorias.id"), nullable=False, index=True
    )
    preco_custo: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    preco_venda: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    estoque_atual: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    estoque_minimo: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, default=0.0
    )
    unidade: Mapped[str] = mapped_column(String(10), nullable=False, default="UN")
    ncm: Mapped[str] = mapped_column(String(10), nullable=True)
    controla_lote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    controla_serie: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    categoria: Mapped["Categoria"] = relationship(
        "Categoria", back_populates="produtos", lazy="selectin"
    )

    # Relacionamento com MovimentacoesEstoque (será criado depois)
    # movimentacoes_estoque: Mapped[list["MovimentacaoEstoque"]] = relationship(
    #     "MovimentacaoEstoque", back_populates="produto", lazy="selectin"
    # )

    # Índices compostos para otimização de consultas
    __table_args__ = (
        Index("idx_produto_categoria_ativo", "categoria_id", "ativo"),
        Index("idx_produto_descricao", "descricao"),
    )

    def __repr__(self) -> str:
        return f"<Produto(id={self.id}, codigo_barras='{self.codigo_barras}', descricao='{self.descricao}')>"
