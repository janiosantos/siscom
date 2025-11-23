"""
Schemas Pydantic para Produtos
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.modules.categorias.schemas import CategoriaResponse


class ProdutoBase(BaseModel):
    """Schema base de Produto"""

    codigo_barras: str = Field(
        ..., min_length=1, max_length=50, description="Código de barras do produto"
    )
    descricao: str = Field(
        ..., min_length=1, max_length=200, description="Descrição do produto"
    )
    categoria_id: int = Field(..., gt=0, description="ID da categoria do produto")
    preco_custo: float = Field(..., ge=0, description="Preço de custo do produto")
    preco_venda: float = Field(..., ge=0, description="Preço de venda do produto")
    estoque_atual: float = Field(
        default=0.0, ge=0, description="Estoque atual do produto"
    )
    estoque_minimo: float = Field(
        default=0.0, ge=0, description="Estoque mínimo do produto"
    )
    unidade: str = Field(
        default="UN", min_length=1, max_length=10, description="Unidade de medida"
    )
    ncm: Optional[str] = Field(None, max_length=10, description="NCM do produto")
    ativo: bool = Field(default=True, description="Produto ativo")

    @field_validator("codigo_barras")
    @classmethod
    def validar_codigo_barras(cls, v: str) -> str:
        """Valida formato do código de barras"""
        if not v or not v.strip():
            raise ValueError("Código de barras não pode ser vazio")

        # Remove espaços em branco
        v = v.strip()

        # Valida se contém apenas números e letras (alfanumérico)
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Código de barras deve conter apenas letras, números, hífens e underscores"
            )

        return v

    @field_validator("preco_venda")
    @classmethod
    def validar_preco_venda(cls, v: float, info) -> float:
        """Valida que preço de venda seja maior ou igual ao preço de custo"""
        # Nota: validação completa será feita no service, pois precisamos de ambos os valores
        if v < 0:
            raise ValueError("Preço de venda não pode ser negativo")
        return v

    @field_validator("ncm")
    @classmethod
    def validar_ncm(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato do NCM"""
        if v is None or v == "":
            return None

        v = v.strip()
        # Remove pontos e espaços
        v = v.replace(".", "").replace(" ", "")

        # NCM deve ter 8 dígitos
        if not v.isdigit():
            raise ValueError("NCM deve conter apenas números")

        if len(v) != 8:
            raise ValueError("NCM deve ter 8 dígitos")

        return v


class ProdutoCreate(ProdutoBase):
    """Schema para criação de Produto"""

    pass


class ProdutoUpdate(BaseModel):
    """Schema para atualização de Produto"""

    codigo_barras: Optional[str] = Field(None, min_length=1, max_length=50)
    descricao: Optional[str] = Field(None, min_length=1, max_length=200)
    categoria_id: Optional[int] = Field(None, gt=0)
    preco_custo: Optional[float] = Field(None, ge=0)
    preco_venda: Optional[float] = Field(None, ge=0)
    estoque_atual: Optional[float] = Field(None, ge=0)
    estoque_minimo: Optional[float] = Field(None, ge=0)
    unidade: Optional[str] = Field(None, min_length=1, max_length=10)
    ncm: Optional[str] = Field(None, max_length=10)
    ativo: Optional[bool] = None

    @field_validator("codigo_barras")
    @classmethod
    def validar_codigo_barras(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato do código de barras"""
        if v is None:
            return None

        if not v.strip():
            raise ValueError("Código de barras não pode ser vazio")

        v = v.strip()

        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Código de barras deve conter apenas letras, números, hífens e underscores"
            )

        return v

    @field_validator("ncm")
    @classmethod
    def validar_ncm(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato do NCM"""
        if v is None or v == "":
            return None

        v = v.strip()
        v = v.replace(".", "").replace(" ", "")

        if not v.isdigit():
            raise ValueError("NCM deve conter apenas números")

        if len(v) != 8:
            raise ValueError("NCM deve ter 8 dígitos")

        return v


class ProdutoResponse(ProdutoBase):
    """Schema de resposta de Produto"""

    id: int
    categoria: CategoriaResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProdutoList(BaseModel):
    """Schema para lista paginada de produtos"""

    items: list[ProdutoResponse]
    total: int
    page: int
    page_size: int
    pages: int
