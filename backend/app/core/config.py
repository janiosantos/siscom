"""
Configuração global da aplicação
"""
from typing import List

from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações da aplicação"""

    # model_config: set env file and ignore extra env vars
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }

    # Application
    APP_NAME: str = "ERP Materiais de Construção"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "test-secret-key-change-in-production"

    # Database
    # DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    DATABASE_URL = "postgresql+asyncpg://siscom:siscom123@172.21.0.2:5432/siscom_dev"
    DATABASE_TEST_URL: str = "sqlite+aiosqlite:///:memory:"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000, \
                                http://0.0.0.0:3000,http://0.0.0.0:8000"

    # Fiscal
    AMBIENTE_NFE: str = "homologacao"
    CERTIFICADO_NFE_PATH: str = ""
    CERTIFICADO_NFE_PASSWORD: str = ""

    # Email (opcional)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Redis (opcional)
    REDIS_URL: str = "redis://172.21.0.2:6379/0"

    # JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Logging and Monitoring
    # URL do Sentry para monitoramento de erros (opcional)
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Integrations - Mercado Pago
    MERCADOPAGO_ACCESS_TOKEN: str = ""
    MERCADOPAGO_PUBLIC_KEY: str = ""
    MERCADOPAGO_WEBHOOK_SECRET: str = ""

    # Integrations - PagSeguro
    PIX_PAGSEGURO_CLIENT_ID: str = ""
    PIX_PAGSEGURO_CLIENT_SECRET: str = ""
    PAGSEGURO_TOKEN: str = ""
    PAGSEGURO_SANDBOX: bool = True

    # Integrations - Cielo
    CIELO_CLIENT_ID: str = ""
    CIELO_CLIENT_SECRET: str = ""
    CIELO_MERCHANT_ID: str = ""

    # Integrations - Stone
    STONE_CLIENT_ID: str = ""
    STONE_CLIENT_SECRET: str = ""

    # Integrations - Shipping
    CORREIOS_API_KEY: str = ""
    MELHOR_ENVIO_CLIENT_ID: str = ""
    MELHOR_ENVIO_CLIENT_SECRET: str = ""
    FRENET_API_KEY: str = ""

    # Integrations - Communication
    SENDGRID_API_KEY: str = ""
    AWS_SES_ACCESS_KEY: str = ""
    AWS_SES_SECRET_KEY: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    WHATSAPP_API_TOKEN: str = ""

    # Integrations - Marketplaces
    MERCADO_LIVRE_CLIENT_ID: str = ""
    MERCADO_LIVRE_CLIENT_SECRET: str = ""
    AMAZON_CLIENT_ID: str = ""
    AMAZON_CLIENT_SECRET: str = ""

    # BI - Metabase
    METABASE_URL: str = "http://localhost:3000"
    METABASE_USERNAME: str = ""
    METABASE_PASSWORD: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    @validator("ALLOWED_ORIGINS")
    def assemble_cors_origins(cls, v: str) -> List[str]:
        """Converte string de origens em lista"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # model_config replaces the old Config inner class for pydantic v2


settings = Settings()
