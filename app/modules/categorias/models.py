"""
Modelos de Categorias de Produtos
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Categoria(Base):
    """Modelo de Categoria de Produtos"""

    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relacionamentos
    produtos: Mapped[list["Produto"]] = relationship(
        "Produto", back_populates="categoria", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Categoria(id={self.id}, nome='{self.nome}')>"
