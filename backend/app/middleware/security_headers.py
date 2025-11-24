"""
Middleware de Security Headers
Implementa headers de segurança para proteger a aplicação
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que adiciona headers de segurança em todas as respostas

    Headers implementados:
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security (HSTS)
    - Content-Security-Policy (CSP)
    - Referrer-Policy
    - Permissions-Policy
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa requisição e adiciona headers de segurança

        Args:
            request: Requisição HTTP
            call_next: Próximo middleware/handler

        Returns:
            Response com headers de segurança
        """
        response = await call_next(request)

        # Previne MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Previne clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Proteção XSS (legacy, mantido para compatibilidade)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # HSTS - Force HTTPS (apenas em produção)
        if not settings.DEBUG:
            # max-age=31536000 = 1 ano
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        # Ajuste conforme necessário para seu frontend
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Ajustar em produção
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (Feature Policy)
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "speaker=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # Remove headers que expõem informações do servidor
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

        return response


def setup_security_headers(app):
    """
    Configura security headers na aplicação

    Args:
        app: Instância do FastAPI
    """
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware configured")
