"""
Testes para funcionalidade de retry automático em pagamentos

Valida que operações de pagamento retentam automaticamente em caso de falhas temporárias
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from app.services.payment_gateway_service import (
    PaymentGatewayService,
    PaymentGateway,
    PaymentMethod,
    PaymentStatus
)
from app.utils.retry import (
    RetryConfig,
    with_retry,
    retry_with_config,
    NetworkError,
    TimeoutError as RetryTimeoutError,
    RateLimitError,
    TemporaryError
)


@pytest.fixture
def payment_service():
    """Fixture de serviço de pagamento"""
    return PaymentGatewayService()


# ============================================
# TESTES DO MÓDULO RETRY
# ============================================

class TestRetryConfig:
    """Testes da classe RetryConfig"""

    def test_calculate_delay_exponential(self):
        """Teste de cálculo de delay com backoff exponencial"""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=False
        )

        # Primeira tentativa (attempt 0)
        assert config.calculate_delay(0) == 1.0

        # Segunda tentativa (attempt 1)
        assert config.calculate_delay(1) == 2.0

        # Terceira tentativa (attempt 2)
        assert config.calculate_delay(2) == 4.0

        # Quarta tentativa (attempt 3)
        assert config.calculate_delay(3) == 8.0

    def test_calculate_delay_respects_max_delay(self):
        """Teste que delay não excede max_delay"""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=5.0,
            jitter=False
        )

        # Attempt 10 normalmente seria 2^10 = 1024s, mas deve ser limitado a 5s
        delay = config.calculate_delay(10)
        assert delay == 5.0

    def test_calculate_delay_with_jitter(self):
        """Teste que jitter adiciona randomização"""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            jitter=True
        )

        # Com jitter, o delay deve ser >= initial_delay
        delay = config.calculate_delay(0)
        assert delay >= 1.0

        # Executar múltiplas vezes para garantir que há variação
        delays = [config.calculate_delay(0) for _ in range(10)]
        # Deve haver pelo menos alguma variação
        assert len(set(delays)) > 1

    def test_is_retryable(self):
        """Teste de identificação de exceções retentáveis"""
        config = RetryConfig(
            retryable_exceptions=(NetworkError, RetryTimeoutError)
        )

        assert config.is_retryable(NetworkError("test"))
        assert config.is_retryable(RetryTimeoutError("test"))
        assert not config.is_retryable(ValueError("test"))
        assert not config.is_retryable(KeyError("test"))


class TestRetryDecorator:
    """Testes do decorator @with_retry"""

    @pytest.mark.asyncio
    async def test_retry_succeeds_first_attempt(self):
        """Teste que função bem-sucedida não retenta"""
        call_count = 0

        @with_retry(max_attempts=3)
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()

        assert result == "success"
        assert call_count == 1  # Chamada apenas uma vez

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failures(self):
        """Teste que função retenta até sucesso"""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.1)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary network error")
            return "success"

        result = await flaky_function()

        assert result == "success"
        assert call_count == 3  # Tentou 3 vezes

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self):
        """Teste que exceção é lançada após max_attempts"""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Persistent error")

        with pytest.raises(NetworkError) as exc_info:
            await always_fails()

        assert "Persistent error" in str(exc_info.value)
        assert call_count == 3  # Tentou 3 vezes

    @pytest.mark.asyncio
    async def test_retry_non_retryable_exception(self):
        """Teste que exceções não-retentáveis não são retentadas"""
        call_count = 0

        @with_retry(
            max_attempts=3,
            initial_delay=0.1,
            retryable_exceptions=(NetworkError,)
        )
        async def raises_non_retryable():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retryable error")

        with pytest.raises(ValueError) as exc_info:
            await raises_non_retryable()

        assert "Non-retryable error" in str(exc_info.value)
        assert call_count == 1  # Não retentou

    @pytest.mark.asyncio
    async def test_retry_callback_is_called(self):
        """Teste que callback on_retry é chamado"""
        callback_calls = []

        def on_retry_callback(exception, attempt, delay):
            callback_calls.append({
                "exception": exception,
                "attempt": attempt,
                "delay": delay
            })

        call_count = 0

        @with_retry(
            max_attempts=3,
            initial_delay=0.1,
            on_retry=on_retry_callback
        )
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError(f"Error {call_count}")
            return "success"

        result = await flaky_function()

        assert result == "success"
        assert len(callback_calls) == 2  # Callback chamado 2 vezes (antes da 2ª e 3ª tentativas)
        assert callback_calls[0]["attempt"] == 1
        assert callback_calls[1]["attempt"] == 2


# ============================================
# TESTES DE RETRY NO PAYMENT GATEWAY SERVICE
# ============================================

class TestPaymentGatewayRetry:
    """Testes de retry em operações de pagamento"""

    @pytest.mark.asyncio
    async def test_create_payment_retries_on_network_error(self, payment_service):
        """Teste que create_payment retenta em caso de erro de rede"""
        call_count = 0

        async def mock_create_payment(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise asyncio.TimeoutError("Network timeout")
            # Terceira tentativa: sucesso
            return {
                "PaymentId": "test-payment-id",
                "Status": "2",
                "Amount": 15000,
                "Captured": True
            }

        with patch.object(
            payment_service.cielo,
            'create_credit_card_payment',
            side_effect=mock_create_payment
        ):
            result = await payment_service.create_payment(
                gateway=PaymentGateway.CIELO,
                payment_method=PaymentMethod.CREDIT_CARD,
                amount=Decimal("150.00"),
                order_id="ORDER-001",
                customer_data={"name": "Cliente"},
                card_data={
                    "number": "4532000000000000",
                    "holder": "TESTE",
                    "expiration": "12/2028",
                    "cvv": "123",
                    "brand": "Visa"
                }
            )

        assert result["payment_id"] == "test-payment-id"
        assert call_count == 3  # Retentou 3 vezes

    @pytest.mark.asyncio
    async def test_create_payment_fails_after_max_retries(self, payment_service):
        """Teste que create_payment falha após max_attempts"""
        call_count = 0

        async def mock_create_payment(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise asyncio.TimeoutError("Persistent network error")

        with patch.object(
            payment_service.cielo,
            'create_credit_card_payment',
            side_effect=mock_create_payment
        ):
            with pytest.raises(asyncio.TimeoutError):
                await payment_service.create_payment(
                    gateway=PaymentGateway.CIELO,
                    payment_method=PaymentMethod.CREDIT_CARD,
                    amount=Decimal("150.00"),
                    order_id="ORDER-001",
                    customer_data={"name": "Cliente"},
                    card_data={
                        "number": "4532000000000000",
                        "holder": "TESTE",
                        "expiration": "12/2028",
                        "cvv": "123",
                        "brand": "Visa"
                    }
                )

        assert call_count == 5  # Max attempts = 5 para create_payment

    @pytest.mark.asyncio
    async def test_capture_payment_retries(self, payment_service):
        """Teste que capture_payment retenta em caso de erro"""
        call_count = 0

        async def mock_capture_payment(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return {
                "Status": 2,
                "ReasonCode": 0,
                "ReasonMessage": "Successful"
            }

        with patch.object(
            payment_service.cielo,
            'capture_payment',
            side_effect=mock_capture_payment
        ):
            result = await payment_service.capture_payment(
                gateway=PaymentGateway.CIELO,
                payment_id="test-payment-id",
                amount=Decimal("150.00")
            )

        assert result["status"] == PaymentStatus.CAPTURED
        assert call_count == 2  # Retentou uma vez

    @pytest.mark.asyncio
    async def test_cancel_payment_retries(self, payment_service):
        """Teste que cancel_payment retenta em caso de erro"""
        call_count = 0

        async def mock_cancel_payment(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncio.TimeoutError("Timeout")
            return {
                "Status": 10,
                "ReasonCode": 0,
                "ReasonMessage": "Successful"
            }

        with patch.object(
            payment_service.cielo,
            'cancel_payment',
            side_effect=mock_cancel_payment
        ):
            result = await payment_service.cancel_payment(
                gateway=PaymentGateway.CIELO,
                payment_id="test-payment-id"
            )

        assert result["status"] == PaymentStatus.CANCELLED
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_query_payment_retries(self, payment_service):
        """Teste que query_payment retenta em caso de erro"""
        call_count = 0

        async def mock_query_payment(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return {
                "PaymentId": "test-payment-id",
                "Tid": "TID123456",
                "Status": "2",  # String, not int
                "Amount": 15000,
                "Captured": True,
                "Installments": 1
            }

        with patch.object(
            payment_service.cielo,
            'query_payment',
            side_effect=mock_query_payment
        ):
            result = await payment_service.query_payment(
                gateway=PaymentGateway.CIELO,
                payment_id="test-payment-id"
            )

        assert result["gateway"] == "cielo"
        assert result["status"] == PaymentStatus.CAPTURED
        assert call_count == 2


# ============================================
# TESTES DE EDGE CASES
# ============================================

class TestRetryEdgeCases:
    """Testes de casos extremos"""

    @pytest.mark.asyncio
    async def test_retry_with_zero_delay(self):
        """Teste de retry com delay zero (execução imediata)"""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.0)
        async def fast_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Error")
            return "success"

        import time
        start = time.time()
        result = await fast_retry()
        elapsed = time.time() - start

        assert result == "success"
        assert call_count == 3
        assert elapsed < 0.5  # Deve ser muito rápido

    @pytest.mark.asyncio
    async def test_retry_with_long_delay(self):
        """Teste que delay longo é respeitado"""
        call_count = 0

        @with_retry(max_attempts=2, initial_delay=0.2, jitter=False)
        async def slow_retry():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise NetworkError("Error")
            return "success"

        import time
        start = time.time()
        result = await slow_retry()
        elapsed = time.time() - start

        assert result == "success"
        assert elapsed >= 0.2  # Pelo menos o delay configurado

    @pytest.mark.asyncio
    async def test_retry_mixed_exceptions(self):
        """Teste com mix de exceções retentáveis e não-retentáveis"""
        call_count = 0

        @with_retry(
            max_attempts=5,
            initial_delay=0.1,
            retryable_exceptions=(NetworkError, RetryTimeoutError)
        )
        async def mixed_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NetworkError("Retryable")
            elif call_count == 2:
                raise ValueError("Non-retryable")
            return "should not reach"

        with pytest.raises(ValueError):
            await mixed_exceptions()

        assert call_count == 2  # Parou na exceção não-retentável


# ============================================
# TESTES DE PERFORMANCE
# ============================================

class TestRetryPerformance:
    """Testes de performance e comportamento do retry"""

    @pytest.mark.asyncio
    async def test_retry_delay_increases_exponentially(self):
        """Teste que delay aumenta exponencialmente entre tentativas"""
        delays = []

        def capture_delay(exc, attempt, delay):
            delays.append(delay)

        call_count = 0

        @with_retry(
            max_attempts=5,
            initial_delay=0.1,
            exponential_base=2.0,
            jitter=False,
            on_retry=capture_delay
        )
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise NetworkError("Error")

        with pytest.raises(NetworkError):
            await always_fails()

        # Verificar que delays aumentam: 0.1, 0.2, 0.4, 0.8
        assert len(delays) == 4
        assert delays[0] == 0.1
        assert delays[1] == 0.2
        assert delays[2] == 0.4
        assert delays[3] == 0.8
