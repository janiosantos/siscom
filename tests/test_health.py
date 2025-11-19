"""
Testes para Health Checks
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestHealthChecks:
    """Testes de health checks"""

    async def test_root_endpoint(self, client: AsyncClient):
        """Teste do endpoint raiz"""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    async def test_health_check(self, client: AsyncClient):
        """Teste de health check básico"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "application" in data
        assert "version" in data
        assert "timestamp" in data

    async def test_readiness_check(self, client: AsyncClient):
        """Teste de readiness check"""
        response = await client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ready", "not_ready"]
        assert "checks" in data
        assert "database" in data["checks"]

    async def test_liveness_check(self, client: AsyncClient):
        """Teste de liveness check"""
        response = await client.get("/live")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    async def test_metrics_endpoint(self, client: AsyncClient):
        """Teste do endpoint de métricas"""
        response = await client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "system" in data
        assert "cpu_percent" in data["system"]
        assert "memory_mb" in data["system"]
