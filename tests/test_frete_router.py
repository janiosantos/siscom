"""
Testes para router de integrações de frete
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from decimal import Decimal

from main import app
from app.integrations.correios import CorreiosClient
from app.integrations.melhorenvio import MelhorEnvioClient


@pytest.fixture
def client():
    """Cliente de teste FastAPI"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers de autenticação mockados"""
    # TODO: Implementar autenticação real quando disponível
    return {"Authorization": "Bearer test_token"}


class TestCorreiosEndpoints:
    """Testes dos endpoints Correios"""

    @patch('app.integrations.frete_router.CorreiosClient')
    def test_calcular_frete_correios_sucesso(self, mock_correios, client, auth_headers):
        """Testa cálculo de frete Correios com sucesso"""
        # Mock do client
        mock_instance = MagicMock()
        mock_instance.calcular_frete = AsyncMock(return_value={
            "servicos": [
                {
                    "codigo": "04014",
                    "nome": "SEDEX",
                    "valor": 25.50,
                    "prazo_entrega": 3,
                    "erro": None
                },
                {
                    "codigo": "04510",
                    "nome": "PAC",
                    "valor": 15.80,
                    "prazo_entrega": 8,
                    "erro": None
                }
            ]
        })
        mock_correios.return_value = mock_instance

        # Request
        payload = {
            "cep_origem": "01310100",
            "cep_destino": "04547130",
            "peso": 2.5,
            "altura": 10,
            "largura": 15,
            "comprimento": 20
        }

        with patch('app.integrations.frete_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/frete/correios/calcular",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "servicos" in data
        assert len(data["servicos"]) == 2
        assert data["servicos"][0]["codigo"] == "04014"
        assert data["servicos"][0]["valor"] == 25.50

    @patch('app.integrations.frete_router.CorreiosClient')
    def test_calcular_frete_correios_erro_api(self, mock_correios, client, auth_headers):
        """Testa erro na API dos Correios"""
        mock_instance = MagicMock()
        mock_instance.calcular_frete = AsyncMock(return_value={
            "erro": "CEP de origem inválido"
        })
        mock_correios.return_value = mock_instance

        payload = {
            "cep_origem": "00000000",
            "cep_destino": "04547130",
            "peso": 2.5
        }

        with patch('app.integrations.frete_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/frete/correios/calcular",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "erro" in data

    def test_calcular_frete_correios_validacao(self, client, auth_headers):
        """Testa validação de campos obrigatórios"""
        payload = {
            "cep_origem": "01310100",
            # Falta cep_destino
            "peso": 2.5
        }

        with patch('app.integrations.frete_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/frete/correios/calcular",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 422  # Validation error

    @patch('app.integrations.frete_router.httpx.AsyncClient')
    def test_consultar_cep_sucesso(self, mock_httpx, client, auth_headers):
        """Testa consulta de CEP com sucesso"""
        # Mock da resposta do ViaCEP
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "cep": "01310-100",
            "logradouro": "Avenida Paulista",
            "bairro": "Bela Vista",
            "localidade": "São Paulo",
            "uf": "SP"
        }

        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client_instance

        with patch('app.integrations.frete_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/frete/cep/01310100",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["cep"] == "01310-100"
        assert data["logradouro"] == "Avenida Paulista"
        assert data["uf"] == "SP"

    @patch('app.integrations.frete_router.httpx.AsyncClient')
    def test_consultar_cep_invalido(self, mock_httpx, client, auth_headers):
        """Testa consulta de CEP inválido"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"erro": True}

        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_httpx.return_value = mock_client_instance

        with patch('app.integrations.frete_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/frete/cep/00000000",
                headers=auth_headers
            )

        assert response.status_code == 404


class TestMelhorEnvioEndpoints:
    """Testes dos endpoints Melhor Envio"""

    @patch('app.integrations.frete_router.MelhorEnvioClient')
    def test_calcular_frete_melhor_envio_sucesso(self, mock_me, client, auth_headers):
        """Testa cálculo de frete Melhor Envio com sucesso"""
        mock_instance = MagicMock()
        mock_instance.calcular_frete = AsyncMock(return_value=[
            {
                "id": 1,
                "name": "PAC",
                "company": {"name": "Correios"},
                "price": "15.80",
                "delivery_time": 8,
                "error": None
            },
            {
                "id": 2,
                "name": ".Package",
                "company": {"name": "Jadlog"},
                "price": "18.50",
                "delivery_time": 5,
                "error": None
            }
        ])
        mock_me.return_value = mock_instance

        payload = {
            "cep_origem": "01310100",
            "cep_destino": "04547130",
            "peso": 2.5,
            "altura": 10,
            "largura": 15,
            "comprimento": 20,
            "valor_declarado": 100.00
        }

        with patch('app.integrations.frete_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/frete/melhorenvio/calcular",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "PAC"
        assert data[1]["company"]["name"] == "Jadlog"

    @patch('app.integrations.frete_router.MelhorEnvioClient')
    def test_rastrear_envio_melhor_envio(self, mock_me, client, auth_headers):
        """Testa rastreamento de envio"""
        mock_instance = MagicMock()
        mock_instance.rastrear_envio = AsyncMock(return_value={
            "id": "abc123",
            "status": "delivered",
            "tracking": "BR123456789BR",
            "events": [
                {
                    "date": "2025-11-19",
                    "description": "Objeto entregue ao destinatário"
                }
            ]
        })
        mock_me.return_value = mock_instance

        with patch('app.integrations.frete_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/frete/melhorenvio/rastreamento/abc123",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "abc123"
        assert data["status"] == "delivered"
        assert len(data["events"]) == 1


class TestComparacaoFretes:
    """Testes do endpoint de comparação"""

    @patch('app.integrations.frete_router.MelhorEnvioClient')
    @patch('app.integrations.frete_router.CorreiosClient')
    def test_comparar_fretes_sucesso(self, mock_correios, mock_me, client, auth_headers):
        """Testa comparação de fretes entre provedores"""
        # Mock Correios
        mock_correios_instance = MagicMock()
        mock_correios_instance.calcular_frete = AsyncMock(return_value={
            "servicos": [
                {
                    "codigo": "04014",
                    "nome": "SEDEX",
                    "valor": 25.50,
                    "prazo_entrega": 3
                }
            ]
        })
        mock_correios.return_value = mock_correios_instance

        # Mock Melhor Envio
        mock_me_instance = MagicMock()
        mock_me_instance.calcular_frete = AsyncMock(return_value=[
            {
                "name": "PAC",
                "company": {"name": "Correios"},
                "price": "15.80",
                "delivery_time": 8
            }
        ])
        mock_me.return_value = mock_me_instance

        params = {
            "cep_origem": "01310100",
            "cep_destino": "04547130",
            "peso": 2.5,
            "altura": 10,
            "largura": 15,
            "comprimento": 20
        }

        with patch('app.integrations.frete_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/frete/comparar",
                params=params,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "correios" in data
        assert "melhor_envio" in data
        assert len(data["correios"]["servicos"]) == 1
        assert len(data["melhor_envio"]) == 1

    @patch('app.integrations.frete_router.MelhorEnvioClient')
    @patch('app.integrations.frete_router.CorreiosClient')
    def test_comparar_fretes_com_erro_parcial(self, mock_correios, mock_me, client, auth_headers):
        """Testa comparação quando um serviço falha"""
        # Mock Correios com erro
        mock_correios_instance = MagicMock()
        mock_correios_instance.calcular_frete = AsyncMock(side_effect=Exception("Erro Correios"))
        mock_correios.return_value = mock_correios_instance

        # Mock Melhor Envio com sucesso
        mock_me_instance = MagicMock()
        mock_me_instance.calcular_frete = AsyncMock(return_value=[
            {
                "name": "PAC",
                "price": "15.80",
                "delivery_time": 8
            }
        ])
        mock_me.return_value = mock_me_instance

        params = {
            "cep_origem": "01310100",
            "cep_destino": "04547130",
            "peso": 2.5
        }

        with patch('app.integrations.frete_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/frete/comparar",
                params=params,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        # Deve retornar mesmo com erro em um serviço
        assert "melhor_envio" in data
        assert data["correios"]["erro"] is not None


class TestHealthCheck:
    """Testes do health check"""

    @patch('app.integrations.frete_router.settings')
    def test_health_check_tudo_configurado(self, mock_settings, client):
        """Testa health check com tudo configurado"""
        mock_settings.MELHOR_ENVIO_CLIENT_ID = "test_client_id"
        mock_settings.MELHOR_ENVIO_CLIENT_SECRET = "test_secret"

        response = client.get("/api/v1/integrations/frete/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["correios"]["disponivel"] is True
        assert data["melhor_envio"]["configurado"] is True

    def test_health_check_sem_configuracao(self, client):
        """Testa health check sem configuração"""
        with patch('app.integrations.frete_router.settings.MELHOR_ENVIO_CLIENT_ID', None):
            with patch('app.integrations.frete_router.settings.MELHOR_ENVIO_CLIENT_SECRET', None):
                response = client.get("/api/v1/integrations/frete/health")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "parcial"
                assert data["melhor_envio"]["configurado"] is False
