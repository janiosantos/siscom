"""
Testes para Sistema de Logging
"""
import pytest
import logging
from app.core.logging import (
    get_logger,
    log_request,
    log_business_event,
    log_error
)


@pytest.mark.unit
class TestLogging:
    """Testes de logging"""

    def test_get_logger(self):
        """Teste de obtenção de logger"""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_log_request(self):
        """Teste de log de requisição HTTP"""
        # Não deve lançar exceção
        log_request(
            method="GET",
            path="/api/v1/produtos",
            status_code=200,
            duration_ms=45.23,
            correlation_id="test-123",
            user_id="user_456"
        )

    def test_log_business_event(self):
        """Teste de log de evento de negócio"""
        # Não deve lançar exceção
        log_business_event(
            event_name="venda_criada",
            correlation_id="test-123",
            user_id="user_456",
            venda_id=1,
            valor_total=150.00
        )

    def test_log_error(self):
        """Teste de log de erro"""
        try:
            raise ValueError("Erro de teste")
        except ValueError as e:
            # Não deve lançar exceção
            log_error(
                error=e,
                correlation_id="test-123",
                user_id="user_456",
                context={"module": "test"}
            )
