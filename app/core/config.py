"""
Configuração global da aplicação
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Configurações da aplicação"""

    # Application
    APP_NAME: str = "ERP Materiais de Construção"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "test-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
    DATABASE_TEST_URL: str = "sqlite+aiosqlite:///:memory:"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

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
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging and Monitoring
    SENTRY_DSN: str = ""  # URL do Sentry para monitoramento de erros (opcional)
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    @validator("ALLOWED_ORIGINS")
    def assemble_cors_origins(cls, v: str) -> List[str]:
        """Converte string de origens em lista"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
