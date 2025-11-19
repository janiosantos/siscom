"""
Middleware de Multi-tenancy - Tenant Isolation
Extrai empresa_id do token JWT e filtra queries automaticamente
"""
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware para extrair empresa_id do token/header
    e disponibilizar no request.state
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extrair empresa_id do header (priority)
        empresa_id = request.headers.get("X-Tenant-ID")

        if not empresa_id:
            # Extrair do token JWT (implementar quando necessário)
            # Por ora, usar empresa padrão ou null
            empresa_id = request.state.get("empresa_id")

        # Armazenar no request.state para uso posterior
        request.state.empresa_id = int(empresa_id) if empresa_id else None

        logger.debug(f"Tenant ID: {request.state.empresa_id}")

        response = await call_next(request)
        return response


# Dependency para injetar empresa_id
async def get_current_tenant(request: Request) -> int:
    """
    Dependency que retorna empresa_id do request

    Uso:
        @router.get("/produtos")
        async def listar_produtos(empresa_id: int = Depends(get_current_tenant)):
            # Filtra apenas produtos da empresa
    """
    empresa_id = getattr(request.state, "empresa_id", None)
    if not empresa_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Empresa não especificada")
    return empresa_id


# Helper para filtrar queries por tenant
def apply_tenant_filter(query, model, empresa_id: int):
    """
    Aplica filtro de tenant em query SQLAlchemy

    Uso:
        query = db.query(Produto)
        query = apply_tenant_filter(query, Produto, empresa_id)
    """
    if hasattr(model, "empresa_id"):
        return query.filter(model.empresa_id == empresa_id)
    return query
