"""
Schemas Pydantic para Fornecedores
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.utils.validators import DocumentValidator


class FornecedorBase(BaseModel):
    """Schema base de Fornecedor"""

    razao_social: str = Field(
        ..., min_length=1, max_length=200, description="Razão social da empresa"
    )
    nome_fantasia: Optional[str] = Field(
        None, max_length=200, description="Nome fantasia"
    )
    cnpj: str = Field(..., min_length=14, max_length=18, description="CNPJ do fornecedor")
    ie: Optional[str] = Field(None, max_length=20, description="Inscrição Estadual")
    email: Optional[str] = Field(None, max_length=100, description="E-mail do fornecedor")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone fixo")
    celular: Optional[str] = Field(None, max_length=20, description="Celular")
    contato_nome: Optional[str] = Field(
        None, max_length=100, description="Nome do contato principal"
    )

    # Endereço
    endereco: Optional[str] = Field(None, max_length=200, description="Logradouro")
    numero: Optional[str] = Field(None, max_length=20, description="Número")
    complemento: Optional[str] = Field(None, max_length=100, description="Complemento")
    bairro: Optional[str] = Field(None, max_length=100, description="Bairro")
    cidade: Optional[str] = Field(None, max_length=100, description="Cidade")
    estado: Optional[str] = Field(None, max_length=2, description="UF do estado")
    cep: Optional[str] = Field(None, max_length=10, description="CEP")

    # Dados bancários
    banco: Optional[str] = Field(None, max_length=100, description="Nome do banco")
    agencia: Optional[str] = Field(None, max_length=20, description="Agência")
    conta: Optional[str] = Field(None, max_length=30, description="Conta bancária")

    # Observações
    observacoes: Optional[str] = Field(None, description="Observações gerais")

    ativo: bool = Field(default=True, description="Fornecedor ativo")

    @field_validator("razao_social")
    @classmethod
    def validar_razao_social(cls, v: str) -> str:
        """Valida razão social"""
        if not v or not v.strip():
            raise ValueError("Razão social não pode ser vazia")
        return v.strip()

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: str) -> str:
        """Valida CNPJ"""
        if not v:
            raise ValueError("CNPJ é obrigatório")

        # Remove caracteres especiais
        v = v.replace(".", "").replace("-", "").replace("/", "").strip()

        # Valida CNPJ (14 dígitos)
        if len(v) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos")

        if not DocumentValidator.validate_cnpj(v):
            raise ValueError("CNPJ inválido")

        return v

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        """Valida e-mail"""
        if v is None or v == "":
            return None

        v = v.strip().lower()

        # Validação básica de e-mail
        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError("E-mail inválido")

        return v

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: Optional[str]) -> Optional[str]:
        """Valida UF do estado"""
        if v is None or v == "":
            return None

        v = v.strip().upper()

        estados_validos = [
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
            "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
            "RS", "RO", "RR", "SC", "SP", "SE", "TO"
        ]

        if v not in estados_validos:
            raise ValueError(f"Estado inválido. Deve ser uma UF válida: {', '.join(estados_validos)}")

        return v

    @field_validator("cep")
    @classmethod
    def validar_cep(cls, v: Optional[str]) -> Optional[str]:
        """Valida CEP"""
        if v is None or v == "":
            return None

        # Remove caracteres especiais
        v = v.replace("-", "").replace(".", "").strip()

        if not v.isdigit():
            raise ValueError("CEP deve conter apenas números")

        if len(v) != 8:
            raise ValueError("CEP deve ter 8 dígitos")

        return v


class FornecedorCreate(FornecedorBase):
    """Schema para criação de Fornecedor"""
    pass


class FornecedorUpdate(BaseModel):
    """Schema para atualização de Fornecedor"""

    razao_social: Optional[str] = Field(None, min_length=1, max_length=200)
    nome_fantasia: Optional[str] = Field(None, max_length=200)
    cnpj: Optional[str] = Field(None, min_length=14, max_length=18)
    ie: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    telefone: Optional[str] = Field(None, max_length=20)
    celular: Optional[str] = Field(None, max_length=20)
    contato_nome: Optional[str] = Field(None, max_length=100)
    endereco: Optional[str] = Field(None, max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = Field(None, max_length=10)
    banco: Optional[str] = Field(None, max_length=100)
    agencia: Optional[str] = Field(None, max_length=20)
    conta: Optional[str] = Field(None, max_length=30)
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None

    @field_validator("razao_social")
    @classmethod
    def validar_razao_social(cls, v: Optional[str]) -> Optional[str]:
        """Valida razão social"""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Razão social não pode ser vazia")
        return v.strip()

    @field_validator("cnpj")
    @classmethod
    def validar_cnpj(cls, v: Optional[str]) -> Optional[str]:
        """Valida CNPJ"""
        if v is None:
            return None

        v = v.replace(".", "").replace("-", "").replace("/", "").strip()

        if len(v) != 14:
            raise ValueError("CNPJ deve ter 14 dígitos")

        if not DocumentValidator.validate_cnpj(v):
            raise ValueError("CNPJ inválido")

        return v

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        """Valida e-mail"""
        if v is None or v == "":
            return None

        v = v.strip().lower()

        if "@" not in v or "." not in v.split("@")[1]:
            raise ValueError("E-mail inválido")

        return v

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: Optional[str]) -> Optional[str]:
        """Valida UF do estado"""
        if v is None or v == "":
            return None

        v = v.strip().upper()

        estados_validos = [
            "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
            "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
            "RS", "RO", "RR", "SC", "SP", "SE", "TO"
        ]

        if v not in estados_validos:
            raise ValueError("Estado inválido. Deve ser uma UF válida")

        return v

    @field_validator("cep")
    @classmethod
    def validar_cep(cls, v: Optional[str]) -> Optional[str]:
        """Valida CEP"""
        if v is None or v == "":
            return None

        v = v.replace("-", "").replace(".", "").strip()

        if not v.isdigit():
            raise ValueError("CEP deve conter apenas números")

        if len(v) != 8:
            raise ValueError("CEP deve ter 8 dígitos")

        return v


class FornecedorResponse(FornecedorBase):
    """Schema de resposta de Fornecedor"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FornecedorList(BaseModel):
    """Schema para lista paginada de fornecedores"""

    items: list[FornecedorResponse]
    total: int
    page: int
    page_size: int
    pages: int
