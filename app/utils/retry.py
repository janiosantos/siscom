"""
Utilitário de retry com backoff exponencial

Implementa retry automático para operações que podem falhar temporariamente,
como chamadas a APIs externas.
"""
import asyncio
import logging
from typing import Callable, TypeVar, Any, Type, Tuple, Optional
from functools import wraps
from datetime import datetime
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuração de retry"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Args:
            max_attempts: Número máximo de tentativas (incluindo a primeira)
            initial_delay: Delay inicial em segundos
            max_delay: Delay máximo em segundos
            exponential_base: Base para cálculo exponencial (2 = dobra a cada vez)
            jitter: Adicionar jitter aleatório (evita thundering herd)
            retryable_exceptions: Tupla de exceções que devem ser retentadas
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def calculate_delay(self, attempt: int) -> float:
        """
        Calcula o delay para uma tentativa específica usando backoff exponencial

        Args:
            attempt: Número da tentativa (0-indexed)

        Returns:
            Delay em segundos
        """
        # Backoff exponencial: initial_delay * (base ^ attempt)
        delay = self.initial_delay * (self.exponential_base ** attempt)

        # Limitar ao max_delay
        delay = min(delay, self.max_delay)

        # Adicionar jitter (randomização) se configurado
        if self.jitter:
            # Jitter entre 0% e 100% do delay
            jitter_amount = delay * random.random()
            delay = delay + jitter_amount

        return delay

    def is_retryable(self, exception: Exception) -> bool:
        """
        Verifica se uma exceção deve ser retentada

        Args:
            exception: Exceção a ser verificada

        Returns:
            True se deve retentar, False caso contrário
        """
        return isinstance(exception, self.retryable_exceptions)


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
):
    """
    Decorator para adicionar retry automático a funções assíncronas

    Args:
        max_attempts: Número máximo de tentativas
        initial_delay: Delay inicial em segundos
        max_delay: Delay máximo em segundos
        exponential_base: Base para cálculo exponencial
        jitter: Adicionar jitter aleatório
        retryable_exceptions: Tupla de exceções que devem ser retentadas
        on_retry: Callback opcional chamado antes de cada retry

    Example:
        >>> @with_retry(max_attempts=3, initial_delay=1.0)
        ... async def call_external_api():
        ...     response = await client.get("https://api.example.com")
        ...     return response

        >>> @with_retry(
        ...     max_attempts=5,
        ...     retryable_exceptions=(TimeoutError, ConnectionError)
        ... )
        ... async def risky_operation():
        ...     return await do_something_risky()
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    # Tentar executar a função
                    result = await func(*args, **kwargs)

                    # Sucesso! Logar se não foi a primeira tentativa
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded on attempt {attempt + 1}/{config.max_attempts}"
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Verificar se deve retentar
                    if not config.is_retryable(e):
                        logger.warning(
                            f"{func.__name__} failed with non-retryable exception: {type(e).__name__}: {e}"
                        )
                        raise

                    # Se foi a última tentativa, não retentar
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {config.max_attempts} attempts. "
                            f"Last error: {type(e).__name__}: {e}"
                        )
                        raise

                    # Calcular delay para próxima tentativa
                    delay = config.calculate_delay(attempt)

                    # Logar retry
                    logger.warning(
                        f"{func.__name__} failed on attempt {attempt + 1}/{config.max_attempts}. "
                        f"Error: {type(e).__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    # Chamar callback se fornecido
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1, delay)
                        except Exception as callback_error:
                            logger.error(f"Error in retry callback: {callback_error}")

                    # Aguardar antes de retentar
                    await asyncio.sleep(delay)

            # Nunca deve chegar aqui, mas por segurança
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


class RetryableError(Exception):
    """Exceção base para erros que devem ser retentados"""
    pass


class TemporaryError(RetryableError):
    """Erro temporário que deve ser retentado"""
    pass


class NetworkError(TemporaryError):
    """Erro de rede temporário"""
    pass


class TimeoutError(TemporaryError):
    """Timeout que pode ser retentado"""
    pass


class RateLimitError(TemporaryError):
    """Rate limit excedido, deve retentar"""
    pass


# Exceções comuns de rede/HTTP que devem ser retentadas
RETRYABLE_HTTP_EXCEPTIONS = (
    NetworkError,
    TimeoutError,
    RateLimitError,
    ConnectionError,
    asyncio.TimeoutError,
)


def create_payment_retry_config() -> RetryConfig:
    """
    Cria configuração de retry otimizada para pagamentos

    Pagamentos são operações críticas, então usamos:
    - Mais tentativas (5)
    - Delays maiores para não sobrecarregar gateways
    - Apenas erros de rede/timeout são retentados
    """
    return RetryConfig(
        max_attempts=5,
        initial_delay=2.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True,
        retryable_exceptions=RETRYABLE_HTTP_EXCEPTIONS
    )


async def retry_with_config(
    func: Callable[..., T],
    config: RetryConfig,
    *args: Any,
    **kwargs: Any
) -> T:
    """
    Executa uma função com retry usando configuração específica

    Args:
        func: Função async a ser executada
        config: Configuração de retry
        *args: Argumentos posicionais para func
        **kwargs: Argumentos nomeados para func

    Returns:
        Resultado da função

    Example:
        >>> config = RetryConfig(max_attempts=3, initial_delay=1.0)
        >>> result = await retry_with_config(
        ...     my_async_function,
        ...     config,
        ...     arg1, arg2,
        ...     kwarg1=value1
        ... )
    """
    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            result = await func(*args, **kwargs)

            if attempt > 0:
                logger.info(
                    f"Function succeeded on attempt {attempt + 1}/{config.max_attempts}"
                )

            return result

        except Exception as e:
            last_exception = e

            if not config.is_retryable(e):
                logger.warning(f"Non-retryable exception: {type(e).__name__}: {e}")
                raise

            if attempt == config.max_attempts - 1:
                logger.error(
                    f"Failed after {config.max_attempts} attempts. "
                    f"Last error: {type(e).__name__}: {e}"
                )
                raise

            delay = config.calculate_delay(attempt)
            logger.warning(
                f"Attempt {attempt + 1}/{config.max_attempts} failed. "
                f"Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)

    if last_exception:
        raise last_exception
