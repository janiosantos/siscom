"""
Configurações do mock service
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configurações da aplicação"""

    # Service
    SERVICE_NAME: str = "payment-gateway-mock"
    VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Mock behavior
    APPROVAL_RATE: float = 0.90  # 90% de aprovações
    DELAY_MS: int = 0  # Delay nas respostas (ms)

    # Logging
    LOG_LEVEL: str = "INFO"

    # Webhooks (opcional)
    ENABLE_WEBHOOKS: bool = False
    WEBHOOK_RETRY_ATTEMPTS: int = 3

    class Config:
        env_prefix = "MOCK_"
        case_sensitive = True


settings = Settings()
