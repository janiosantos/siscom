"""
Módulo de Clientes
"""
from app.modules.clientes.models import Cliente, TipoPessoa
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ClienteList,
    TipoPessoaEnum,
)
from app.modules.clientes.router import router

__all__ = [
    "Cliente",
    "TipoPessoa",
    "ClienteCreate",
    "ClienteUpdate",
    "ClienteResponse",
    "ClienteList",
    "TipoPessoaEnum",
    "router",
]
