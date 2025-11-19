"""
Sistema de Logging Estruturado com JSON
Implementa logging com correlation IDs, formatação JSON e integração com Sentry
"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Formatador JSON customizado para logs estruturados
    """

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """
        Adiciona campos customizados aos logs
        """
        super().add_fields(log_record, record, message_dict)

        # Adiciona timestamp ISO 8601
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Adiciona nível do log
        log_record['level'] = record.levelname

        # Adiciona nome do logger
        log_record['logger'] = record.name

        # Adiciona informações do módulo
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno

        # Adiciona ambiente (dev/prod)
        log_record['environment'] = 'development' if settings.DEBUG else 'production'

        # Adiciona nome da aplicação
        log_record['application'] = settings.APP_NAME
        log_record['version'] = settings.APP_VERSION


def setup_logging() -> logging.Logger:
    """
    Configura o sistema de logging estruturado

    Returns:
        Logger configurado
    """
    # Determina o nível de log baseado no ambiente
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Cria o logger raiz
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove handlers existentes
    logger.handlers = []

    # Cria handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Configura o formatador JSON
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(logger)s %(module)s %(function)s %(line)s %(message)s'
    )
    handler.setFormatter(formatter)

    # Adiciona o handler ao logger
    logger.addHandler(handler)

    # Configura loggers específicos

    # Reduz verbosidade do SQLAlchemy em produção
    if not settings.DEBUG:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

    # Reduz verbosidade do uvicorn
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger específico para um módulo

    Args:
        name: Nome do módulo/componente

    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    correlation_id: str = None,
    user_id: str = None,
    client_ip: str = None,
    **extra_fields
) -> None:
    """
    Loga uma requisição HTTP de forma estruturada

    Args:
        method: Método HTTP (GET, POST, etc)
        path: Caminho da requisição
        status_code: Código de status da resposta
        duration_ms: Duração da requisição em milissegundos
        correlation_id: ID de correlação da requisição
        user_id: ID do usuário (se autenticado)
        client_ip: IP do cliente
        **extra_fields: Campos adicionais para logging
    """
    logger = get_logger('api.request')

    log_data = {
        'event': 'http_request',
        'method': method,
        'path': path,
        'status_code': status_code,
        'duration_ms': round(duration_ms, 2),
    }

    if correlation_id:
        log_data['correlation_id'] = correlation_id

    if user_id:
        log_data['user_id'] = user_id

    if client_ip:
        log_data['client_ip'] = client_ip

    # Adiciona campos extras
    log_data.update(extra_fields)

    # Define o nível de log baseado no status code
    if status_code >= 500:
        logger.error('HTTP Request', extra=log_data)
    elif status_code >= 400:
        logger.warning('HTTP Request', extra=log_data)
    else:
        logger.info('HTTP Request', extra=log_data)


def log_business_event(
    event_name: str,
    correlation_id: str = None,
    user_id: str = None,
    **event_data
) -> None:
    """
    Loga um evento de negócio de forma estruturada

    Args:
        event_name: Nome do evento (ex: 'venda_criada', 'estoque_baixo')
        correlation_id: ID de correlação
        user_id: ID do usuário
        **event_data: Dados do evento
    """
    logger = get_logger('business.events')

    log_data = {
        'event': event_name,
        **event_data
    }

    if correlation_id:
        log_data['correlation_id'] = correlation_id

    if user_id:
        log_data['user_id'] = user_id

    logger.info(f'Business Event: {event_name}', extra=log_data)


def log_error(
    error: Exception,
    correlation_id: str = None,
    user_id: str = None,
    **context
) -> None:
    """
    Loga um erro de forma estruturada

    Args:
        error: Exceção ocorrida
        correlation_id: ID de correlação
        user_id: ID do usuário
        **context: Contexto adicional do erro
    """
    logger = get_logger('errors')

    log_data = {
        'event': 'error',
        'error_type': type(error).__name__,
        'error_message': str(error),
        **context
    }

    if correlation_id:
        log_data['correlation_id'] = correlation_id

    if user_id:
        log_data['user_id'] = user_id

    logger.error(f'Error: {type(error).__name__}', extra=log_data, exc_info=True)


def setup_sentry(dsn: str = None) -> None:
    """
    Configura integração com Sentry para monitoramento de erros

    Args:
        dsn: Data Source Name do Sentry (opcional)
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        # Usa DSN das configurações se não fornecido
        sentry_dsn = dsn or getattr(settings, 'SENTRY_DSN', None)

        if not sentry_dsn:
            logger = get_logger('sentry')
            logger.warning('Sentry DSN not configured. Sentry integration disabled.')
            return

        sentry_sdk.init(
            dsn=sentry_dsn,
            environment='development' if settings.DEBUG else 'production',
            release=settings.APP_VERSION,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            # Taxa de amostragem de transações (performance monitoring)
            traces_sample_rate=0.1 if not settings.DEBUG else 1.0,

            # Taxa de amostragem de erros
            sample_rate=1.0,

            # Envia PII (Personally Identifiable Information)
            send_default_pii=False,

            # Anexa stack traces locais
            attach_stacktrace=True,
        )

        logger = get_logger('sentry')
        logger.info('Sentry integration configured successfully')

    except ImportError:
        logger = get_logger('sentry')
        logger.warning('sentry-sdk not installed. Install with: pip install sentry-sdk')
    except Exception as e:
        logger = get_logger('sentry')
        logger.error(f'Failed to configure Sentry: {e}')


# Inicializa o logger na importação do módulo
setup_logging()
