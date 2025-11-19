"""
Endpoints de Health Check
Implementa verificações de saúde da aplicação e dependências
"""
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, status
from sqlalchemy import text

from app.core.database import get_async_session
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Health check básico - verifica se a aplicação está rodando

    Returns:
        Status de saúde da aplicação
    """
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check - verifica se a aplicação está pronta para receber tráfego
    Inclui verificação de dependências (banco de dados)

    Returns:
        Status detalhado de prontidão

    Raises:
        HTTPException: Se alguma dependência não estiver disponível
    """
    checks = {
        "status": "ready",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "checks": {}
    }

    # Verifica conexão com banco de dados
    db_healthy = await check_database()
    checks["checks"]["database"] = {
        "status": "healthy" if db_healthy else "unhealthy",
        "type": "postgresql"
    }

    # Se alguma verificação falhar, marca como não pronto
    all_healthy = all(
        check.get("status") == "healthy"
        for check in checks["checks"].values()
    )

    if not all_healthy:
        checks["status"] = "not_ready"
        logger.warning("Readiness check failed", extra={"checks": checks["checks"]})

    return checks


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check - verifica se a aplicação está viva (não travada)
    Usado pelo Kubernetes para restart automático

    Returns:
        Status simples de vida
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
    }


async def check_database() -> bool:
    """
    Verifica conectividade com o banco de dados

    Returns:
        True se banco está acessível, False caso contrário
    """
    try:
        async for session in get_async_session():
            # Executa query simples
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def metrics() -> Dict[str, Any]:
    """
    Endpoint de métricas básicas da aplicação
    Pode ser expandido com Prometheus metrics

    Returns:
        Métricas básicas
    """
    import psutil
    import os

    process = psutil.Process(os.getpid())

    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "system": {
            "cpu_percent": process.cpu_percent(),
            "memory_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "threads": process.num_threads(),
        },
        "environment": "development" if settings.DEBUG else "production",
    }
