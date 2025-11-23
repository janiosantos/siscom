"""
Middleware de Correlation ID
Adiciona um ID único a cada requisição para rastreamento distribuído
"""
import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar

from app.core.logging import log_request, get_logger

# ContextVar para armazenar o correlation ID da requisição atual
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default=None)

logger = get_logger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware que adiciona um Correlation ID único a cada requisição
    e loga automaticamente todas as requisições
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa cada requisição adicionando correlation ID e logging

        Args:
            request: Requisição HTTP
            call_next: Próximo middleware/handler

        Returns:
            Response HTTP
        """
        # Gera ou obtém correlation ID do header
        correlation_id = request.headers.get('X-Correlation-ID')
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Armazena no contexto
        correlation_id_var.set(correlation_id)

        # Marca início da requisição
        start_time = time.time()

        try:
            # Processa a requisição
            response = await call_next(request)

            # Calcula duração
            duration_ms = (time.time() - start_time) * 1000

            # Adiciona correlation ID no header da resposta
            response.headers['X-Correlation-ID'] = correlation_id

            # Loga a requisição
            log_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                client_ip=request.client.host if request.client else None,
                query_params=dict(request.query_params) if request.query_params else None,
                user_agent=request.headers.get('user-agent'),
            )

            return response

        except Exception as e:
            # Calcula duração até o erro
            duration_ms = (time.time() - start_time) * 1000

            # Loga erro da requisição
            log_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
                correlation_id=correlation_id,
                client_ip=request.client.host if request.client else None,
                error=str(e),
                error_type=type(e).__name__,
            )

            # Re-raise para FastAPI tratar
            raise


def get_correlation_id() -> str:
    """
    Obtém o correlation ID da requisição atual

    Returns:
        Correlation ID ou None se não estiver em contexto de requisição
    """
    return correlation_id_var.get()
