"""
Schemas Pydantic para Clientes
"""
from datetime import datetime, date
from typing import Optional
from enum import Enum as PyEnum
from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr
from app.utils.validators import DocumentValidator


class TipoPessoaEnum(str, PyEnum):
    """Enum de tipo de pessoa"""
    PF = "PF"
    PJ = "PJ"


class ClienteBase(BaseModel):
    """Schema base de Cliente"""

    nome: str = Field(
        ..., min_length=1, max_length=200, description="Nome completo ou razão social"
    )
    tipo_pessoa: TipoPessoaEnum = Field(
        default=TipoPessoaEnum.PF, description="Tipo de pessoa (PF ou PJ)"
    )
    cpf_cnpj: str = Field(..., min_length=11, max_length=18, description="CPF ou CNPJ")
    email: Optional[str] = Field(None, max_length=100, description="E-mail do cliente")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone fixo")
    celular: Optional[str] = Field(None, max_length=20, description="Celular")
    data_nascimento: Optional[date] = Field(None, description="Data de nascimento")

    # Endereço
    endereco: Optional[str] = Field(None, max_length=200, description="Logradouro")
    numero: Optional[str] = Field(None, max_length=20, description="Número")
    complemento: Optional[str] = Field(None, max_length=100, description="Complemento")
    bairro: Optional[str] = Field(None, max_length=100, description="Bairro")
    cidade: Optional[str] = Field(None, max_length=100, description="Cidade")
    estado: Optional[str] = Field(None, max_length=2, description="UF do estado")
    cep: Optional[str] = Field(None, max_length=10, description="CEP")

    ativo: bool = Field(default=True, description="Cliente ativo")

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        """Valida nome do cliente"""
        if not v or not v.strip():
            raise ValueError("Nome não pode ser vazio")
        return v.strip()

    @field_validator("cpf_cnpj")
    @classmethod
    def validar_cpf_cnpj(cls, v: str) -> str:
        """Valida CPF ou CNPJ"""
        if not v:
            raise ValueError("CPF/CNPJ é obrigatório")

        # Remove caracteres especiais
        v = v.replace(".", "").replace("-", "").replace("/", "").strip()

        # Valida CPF (11 dígitos) ou CNPJ (14 dígitos)
        if len(v) == 11:
            if not DocumentValidator.validate_cpf(v):
                raise ValueError("CPF inválido")
        elif len(v) == 14:
            if not DocumentValidator.validate_cnpj(v):
                raise ValueError("CNPJ inválido")
        else:
            raise ValueError("CPF/CNPJ deve ter 11 ou 14 dígitos")

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

    @field_validator("data_nascimento")
    @classmethod
    def validar_data_nascimento(cls, v: Optional[date]) -> Optional[date]:
        """Valida data de nascimento"""
        if v is None:
            return None

        # Não pode ser data futura
        if v > date.today():
            raise ValueError("Data de nascimento não pode ser no futuro")

        # Idade mínima de 0 anos e máxima de 150 anos
        idade = (date.today() - v).days // 365
        if idade > 150:
            raise ValueError("Data de nascimento inválida (idade maior que 150 anos)")

        return v


class ClienteCreate(ClienteBase):
    """Schema para criação de Cliente"""
    pass


class ClienteUpdate(BaseModel):
    """Schema para atualização de Cliente"""

    nome: Optional[str] = Field(None, min_length=1, max_length=200)
    tipo_pessoa: Optional[TipoPessoaEnum] = None
    cpf_cnpj: Optional[str] = Field(None, min_length=11, max_length=18)
    email: Optional[str] = Field(None, max_length=100)
    telefone: Optional[str] = Field(None, max_length=20)
    celular: Optional[str] = Field(None, max_length=20)
    data_nascimento: Optional[date] = None
    endereco: Optional[str] = Field(None, max_length=200)
    numero: Optional[str] = Field(None, max_length=20)
    complemento: Optional[str] = Field(None, max_length=100)
    bairro: Optional[str] = Field(None, max_length=100)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = Field(None, max_length=10)
    ativo: Optional[bool] = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: Optional[str]) -> Optional[str]:
        """Valida nome do cliente"""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Nome não pode ser vazio")
        return v.strip()

    @field_validator("cpf_cnpj")
    @classmethod
    def validar_cpf_cnpj(cls, v: Optional[str]) -> Optional[str]:
        """Valida CPF ou CNPJ"""
        if v is None:
            return None

        v = v.replace(".", "").replace("-", "").replace("/", "").strip()

        if len(v) == 11:
            if not DocumentValidator.validate_cpf(v):
                raise ValueError("CPF inválido")
        elif len(v) == 14:
            if not DocumentValidator.validate_cnpj(v):
                raise ValueError("CNPJ inválido")
        else:
            raise ValueError("CPF/CNPJ deve ter 11 ou 14 dígitos")

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
            raise ValueError(f"Estado inválido. Deve ser uma UF válida")

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

    @field_validator("data_nascimento")
    @classmethod
    def validar_data_nascimento(cls, v: Optional[date]) -> Optional[date]:
        """Valida data de nascimento"""
        if v is None:
            return None

        if v > date.today():
            raise ValueError("Data de nascimento não pode ser no futuro")

        idade = (date.today() - v).days // 365
        if idade > 150:
            raise ValueError("Data de nascimento inválida")

        return v


class ClienteResponse(ClienteBase):
    """Schema de resposta de Cliente"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClienteList(BaseModel):
    """Schema para lista paginada de clientes"""

    items: list[ClienteResponse]
    total: int
    page: int
    page_size: int
    pages: int
