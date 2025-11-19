"""
Middleware de Rate Limiting
Protege a API contra abuso e ataques DDoS
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_identifier(request: Request) -> str:
    """
    Identifica o cliente para rate limiting

    Usa o user_id se autenticado, caso contrário usa IP

    Args:
        request: Requisição FastAPI

    Returns:
        Identificador único do cliente
    """
    # Se usuário estiver autenticado, usa user_id
    user = getattr(request.state, "user", None)
    if user:
        identifier = f"user:{user.id}"
        logger.debug(f"Rate limit identifier: {identifier}")
        return identifier

    # Caso contrário, usa IP
    identifier = get_remote_address(request)
    logger.debug(f"Rate limit identifier (IP): {identifier}")
    return identifier


# Cria o limiter
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["200 per minute", "5000 per hour"],  # Limites padrão
    storage_uri=settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else "memory://",
    strategy="fixed-window",
    headers_enabled=True,  # Adiciona headers X-RateLimit-* nas respostas
)


# Rate limits específicos para diferentes endpoints

# Login: mais restritivo para evitar brute force
LOGIN_LIMIT = "5 per minute"

# Registro: limitar criação de contas
REGISTER_LIMIT = "3 per hour"

# Endpoints de escrita (POST, PUT, DELETE): moderado
WRITE_LIMIT = "60 per minute"

# Endpoints de leitura (GET): mais permissivo
READ_LIMIT = "200 per minute"

# Endpoints públicos (sem autenticação): mais restritivo
PUBLIC_LIMIT = "30 per minute"

# Endpoints de exportação/relatórios: restrito (operações pesadas)
EXPORT_LIMIT = "10 per hour"


def setup_rate_limiting(app):
    """
    Configura rate limiting na aplicação

    Args:
        app: Instância do FastAPI
    """
    # Registra o limiter no state
    app.state.limiter = limiter

    # Adiciona exception handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Adiciona middleware
    app.add_middleware(SlowAPIMiddleware)

    logger.info("Rate limiting configured", extra={
        "default_limits": limiter._default_limits,
        "storage": "redis" if "redis" in settings.REDIS_URL else "memory"
    })
