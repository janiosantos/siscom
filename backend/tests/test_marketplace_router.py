"""
Testes para router de integrações de marketplaces
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from decimal import Decimal

from main import app
from app.integrations.mercadolivre import MercadoLivreClient


@pytest.fixture
def client():
    """Cliente de teste FastAPI"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers de autenticação mockados"""
    return {"Authorization": "Bearer test_token"}


class TestOAuthEndpoints:
    """Testes dos endpoints OAuth do Mercado Livre"""

    @patch('app.integrations.marketplace_router.settings')
    def test_obter_url_autorizacao(self, mock_settings, client, auth_headers):
        """Testa geração da URL de autorização OAuth"""
        mock_settings.MERCADO_LIVRE_CLIENT_ID = "client_123"

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/marketplace/mercadolivre/auth/url",
                params={"redirect_uri": "https://exemplo.com/callback"},
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "client_123" in data["authorization_url"]
        assert "redirect_uri=https://exemplo.com/callback" in data["authorization_url"]

    @patch('app.integrations.marketplace_router.settings')
    def test_obter_url_autorizacao_sem_client_id(self, mock_settings, client, auth_headers):
        """Testa erro quando CLIENT_ID não configurado"""
        mock_settings.MERCADO_LIVRE_CLIENT_ID = None

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/marketplace/mercadolivre/auth/url",
                params={"redirect_uri": "https://exemplo.com/callback"},
                headers=auth_headers
            )

        assert response.status_code == 500

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_obter_access_token_sucesso(self, mock_get_client, client, auth_headers):
        """Testa obtenção de access token com código"""
        mock_ml_client = MagicMock()
        mock_ml_client.obter_access_token = AsyncMock(return_value={
            "access_token": "APP_USR-123456",
            "token_type": "bearer",
            "expires_in": 21600,
            "refresh_token": "TG-abc123",
            "user_id": "789012"
        })
        mock_get_client.return_value = mock_ml_client

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/auth/token",
                params={
                    "code": "TG-xyz789",
                    "redirect_uri": "https://exemplo.com/callback"
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "APP_USR-123456"
        assert data["refresh_token"] == "TG-abc123"

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_atualizar_access_token(self, mock_get_client, client, auth_headers):
        """Testa renovação do access token"""
        mock_ml_client = MagicMock()
        mock_ml_client.atualizar_access_token = AsyncMock(return_value={
            "access_token": "APP_USR-new123",
            "token_type": "bearer",
            "expires_in": 21600,
            "refresh_token": "TG-new456"
        })
        mock_get_client.return_value = mock_ml_client

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/auth/refresh",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "APP_USR-new123"


class TestAnunciosEndpoints:
    """Testes dos endpoints de anúncios"""

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_criar_anuncio_sucesso(self, mock_get_client, client, auth_headers):
        """Testa criação de anúncio com sucesso"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = "APP_USR-123456"
        mock_ml_client.criar_anuncio = AsyncMock(return_value={
            "id": "MLB123456789",
            "title": "Cimento 50kg",
            "price": 25.90,
            "available_quantity": 100,
            "status": "active",
            "permalink": "https://produto.mercadolivre.com.br/MLB-123456789"
        })
        mock_get_client.return_value = mock_ml_client

        payload = {
            "titulo": "Cimento 50kg",
            "categoria_id": "MLB1234",
            "preco": 25.90,
            "quantidade": 100,
            "condicao": "new",
            "descricao": "Cimento de alta qualidade",
            "imagens": [
                "https://exemplo.com/img1.jpg",
                "https://exemplo.com/img2.jpg"
            ]
        }

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/anuncios",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "MLB123456789"
        assert data["title"] == "Cimento 50kg"
        assert data["status"] == "active"

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_criar_anuncio_sem_token(self, mock_get_client, client, auth_headers):
        """Testa erro ao criar anúncio sem OAuth"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = None
        mock_get_client.return_value = mock_ml_client

        payload = {
            "titulo": "Produto Teste",
            "categoria_id": "MLB1234",
            "preco": 10.00,
            "quantidade": 1,
            "condicao": "new",
            "descricao": "Teste",
            "imagens": ["http://img.jpg"]
        }

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/anuncios",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 401

    def test_criar_anuncio_validacao_titulo(self, client, auth_headers):
        """Testa validação do título (max 60 caracteres)"""
        payload = {
            "titulo": "A" * 61,  # Excede limite
            "categoria_id": "MLB1234",
            "preco": 10.00,
            "quantidade": 1,
            "condicao": "new",
            "descricao": "Teste",
            "imagens": ["http://img.jpg"]
        }

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/anuncios",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 422

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_atualizar_estoque_sucesso(self, mock_get_client, client, auth_headers):
        """Testa atualização de estoque"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = "APP_USR-123456"
        mock_ml_client.atualizar_estoque = AsyncMock(return_value={
            "id": "MLB123456789",
            "available_quantity": 50,
            "status": "active"
        })
        mock_get_client.return_value = mock_ml_client

        payload = {
            "quantidade": 50
        }

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.put(
                "/api/v1/integrations/marketplace/mercadolivre/anuncios/MLB123456789/estoque",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["available_quantity"] == 50

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_pausar_anuncio_sucesso(self, mock_get_client, client, auth_headers):
        """Testa pausar anúncio"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = "APP_USR-123456"
        mock_ml_client.pausar_anuncio = AsyncMock(return_value={
            "id": "MLB123456789",
            "status": "paused"
        })
        mock_get_client.return_value = mock_ml_client

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.put(
                "/api/v1/integrations/marketplace/mercadolivre/anuncios/MLB123456789/pausar",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"


class TestVendasEndpoints:
    """Testes dos endpoints de vendas"""

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_listar_vendas_sucesso(self, mock_get_client, client, auth_headers):
        """Testa listagem de vendas"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = "APP_USR-123456"
        mock_ml_client.listar_vendas = AsyncMock(return_value={
            "results": [
                {
                    "id": 123456789,
                    "status": "paid",
                    "date_created": "2025-11-19T10:00:00.000Z",
                    "total_amount": 100.00,
                    "buyer": {"id": 987654321}
                },
                {
                    "id": 123456790,
                    "status": "confirmed",
                    "date_created": "2025-11-18T15:30:00.000Z",
                    "total_amount": 250.50,
                    "buyer": {"id": 987654322}
                }
            ],
            "paging": {
                "total": 2,
                "offset": 0,
                "limit": 50
            }
        })
        mock_get_client.return_value = mock_ml_client

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/marketplace/mercadolivre/vendas",
                params={"seller_id": "789012"},
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["results"][0]["status"] == "paid"
        assert data["paging"]["total"] == 2

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_listar_vendas_com_filtro_status(self, mock_get_client, client, auth_headers):
        """Testa listagem com filtro de status"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = "APP_USR-123456"
        mock_ml_client.listar_vendas = AsyncMock(return_value={
            "results": [
                {
                    "id": 123456789,
                    "status": "paid",
                    "total_amount": 100.00
                }
            ],
            "paging": {"total": 1}
        })
        mock_get_client.return_value = mock_ml_client

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/marketplace/mercadolivre/vendas",
                params={
                    "seller_id": "789012",
                    "status_venda": "paid"
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        mock_ml_client.listar_vendas.assert_called_once()
        call_kwargs = mock_ml_client.listar_vendas.call_args.kwargs
        assert call_kwargs["status"] == "paid"

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_listar_vendas_paginacao(self, mock_get_client, client, auth_headers):
        """Testa paginação de vendas"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = "APP_USR-123456"
        mock_ml_client.listar_vendas = AsyncMock(return_value={
            "results": [],
            "paging": {"total": 150, "offset": 50, "limit": 50}
        })
        mock_get_client.return_value = mock_ml_client

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/marketplace/mercadolivre/vendas",
                params={
                    "seller_id": "789012",
                    "offset": 50,
                    "limit": 50
                },
                headers=auth_headers
            )

        assert response.status_code == 200
        mock_ml_client.listar_vendas.assert_called_once()
        call_kwargs = mock_ml_client.listar_vendas.call_args.kwargs
        assert call_kwargs["offset"] == 50
        assert call_kwargs["limit"] == 50

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_obter_detalhes_venda(self, mock_get_client, client, auth_headers):
        """Testa obter detalhes de uma venda"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = "APP_USR-123456"
        mock_ml_client.obter_detalhes_venda = AsyncMock(return_value={
            "id": 123456789,
            "status": "paid",
            "date_created": "2025-11-19T10:00:00.000Z",
            "total_amount": 100.00,
            "currency_id": "BRL",
            "buyer": {
                "id": 987654321,
                "nickname": "COMPRADOR123"
            },
            "order_items": [
                {
                    "item": {
                        "id": "MLB123",
                        "title": "Cimento 50kg"
                    },
                    "quantity": 2,
                    "unit_price": 50.00
                }
            ],
            "payments": [
                {
                    "status": "approved",
                    "transaction_amount": 100.00,
                    "payment_type": "credit_card"
                }
            ],
            "shipping": {
                "status": "pending",
                "receiver_address": {
                    "city": {"name": "São Paulo"},
                    "state": {"name": "SP"}
                }
            }
        })
        mock_get_client.return_value = mock_ml_client

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/marketplace/mercadolivre/vendas/123456789",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 123456789
        assert data["status"] == "paid"
        assert len(data["order_items"]) == 1
        assert data["payments"][0]["status"] == "approved"


class TestMensagensEndpoints:
    """Testes dos endpoints de mensagens"""

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_enviar_mensagem_sucesso(self, mock_get_client, client, auth_headers):
        """Testa envio de mensagem para comprador"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = "APP_USR-123456"
        mock_ml_client.enviar_mensagem = AsyncMock(return_value={
            "id": "msg_123",
            "status": "sent",
            "message": "Seu pedido está sendo preparado",
            "date_created": "2025-11-19T10:00:00.000Z"
        })
        mock_get_client.return_value = mock_ml_client

        payload = {
            "mensagem": "Seu pedido está sendo preparado"
        }

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/mensagens/123456789/987654321",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["message"] == "Seu pedido está sendo preparado"

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_enviar_mensagem_sem_token(self, mock_get_client, client, auth_headers):
        """Testa erro ao enviar mensagem sem OAuth"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = None
        mock_get_client.return_value = mock_ml_client

        payload = {
            "mensagem": "Teste"
        }

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/mensagens/123456789/987654321",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 401


class TestHealthCheck:
    """Testes do health check"""

    @patch('app.integrations.marketplace_router.settings')
    def test_health_check_configurado(self, mock_settings, client):
        """Testa health check com ML configurado"""
        mock_settings.MERCADO_LIVRE_CLIENT_ID = "client_123"
        mock_settings.MERCADO_LIVRE_CLIENT_SECRET = "secret_456"

        response = client.get("/api/v1/integrations/marketplace/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["mercado_livre"]["configurado"] is True
        assert data["mercado_livre"]["oauth_required"] is True

    def test_health_check_sem_configuracao(self, client):
        """Testa health check sem configuração"""
        with patch('app.integrations.marketplace_router.settings.MERCADO_LIVRE_CLIENT_ID', None):
            response = client.get("/api/v1/integrations/marketplace/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "sem_configuracao"
            assert data["mercado_livre"]["configurado"] is False


class TestValidacoes:
    """Testes de validação de campos"""

    def test_criar_anuncio_preco_invalido(self, client, auth_headers):
        """Testa criação com preço inválido (zero ou negativo)"""
        payload = {
            "titulo": "Produto",
            "categoria_id": "MLB1234",
            "preco": 0,  # Inválido
            "quantidade": 1,
            "condicao": "new",
            "descricao": "Teste",
            "imagens": ["http://img.jpg"]
        }

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/anuncios",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 422

    def test_criar_anuncio_sem_imagens(self, client, auth_headers):
        """Testa criação sem imagens"""
        payload = {
            "titulo": "Produto",
            "categoria_id": "MLB1234",
            "preco": 10.00,
            "quantidade": 1,
            "condicao": "new",
            "descricao": "Teste",
            "imagens": []  # Vazio
        }

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/anuncios",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 422

    def test_atualizar_estoque_quantidade_negativa(self, client, auth_headers):
        """Testa atualização com quantidade negativa"""
        payload = {
            "quantidade": -5
        }

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.put(
                "/api/v1/integrations/marketplace/mercadolivre/anuncios/MLB123/estoque",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 422

    def test_listar_vendas_limite_invalido(self, client, auth_headers):
        """Testa listagem com limite inválido (>100)"""
        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/marketplace/mercadolivre/vendas",
                params={
                    "seller_id": "789012",
                    "limit": 150  # Excede máximo de 100
                },
                headers=auth_headers
            )

        assert response.status_code == 422


class TestIntegracaoCompleta:
    """Testes de fluxo completo"""

    @patch('app.integrations.marketplace_router.get_ml_client')
    def test_fluxo_completo_anuncio(self, mock_get_client, client, auth_headers):
        """Testa fluxo completo: criar → atualizar estoque → pausar"""
        mock_ml_client = MagicMock()
        mock_ml_client.access_token = "APP_USR-123456"

        # Mock criar anúncio
        mock_ml_client.criar_anuncio = AsyncMock(return_value={
            "id": "MLB999",
            "status": "active"
        })

        # Mock atualizar estoque
        mock_ml_client.atualizar_estoque = AsyncMock(return_value={
            "id": "MLB999",
            "available_quantity": 20
        })

        # Mock pausar
        mock_ml_client.pausar_anuncio = AsyncMock(return_value={
            "id": "MLB999",
            "status": "paused"
        })

        mock_get_client.return_value = mock_ml_client

        with patch('app.integrations.marketplace_router.get_current_user', return_value=MagicMock(id=1)):
            # 1. Criar anúncio
            create_payload = {
                "titulo": "Produto Teste",
                "categoria_id": "MLB1234",
                "preco": 50.00,
                "quantidade": 10,
                "condicao": "new",
                "descricao": "Teste",
                "imagens": ["http://img.jpg"]
            }
            create_response = client.post(
                "/api/v1/integrations/marketplace/mercadolivre/anuncios",
                json=create_payload,
                headers=auth_headers
            )
            assert create_response.status_code == 200
            item_id = create_response.json()["id"]

            # 2. Atualizar estoque
            update_payload = {"quantidade": 20}
            update_response = client.put(
                f"/api/v1/integrations/marketplace/mercadolivre/anuncios/{item_id}/estoque",
                json=update_payload,
                headers=auth_headers
            )
            assert update_response.status_code == 200
            assert update_response.json()["available_quantity"] == 20

            # 3. Pausar anúncio
            pause_response = client.put(
                f"/api/v1/integrations/marketplace/mercadolivre/anuncios/{item_id}/pausar",
                headers=auth_headers
            )
            assert pause_response.status_code == 200
            assert pause_response.json()["status"] == "paused"
