"""
Testes para router de integrações de comunicação
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from main import app
from app.integrations.email import EmailClient, EmailProvider
from app.integrations.sms import SMSClient


@pytest.fixture
def client():
    """Cliente de teste FastAPI"""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Headers de autenticação mockados"""
    return {"Authorization": "Bearer test_token"}


class TestEmailEndpoints:
    """Testes dos endpoints de email"""

    @patch('app.integrations.comunicacao_router.get_email_client')
    def test_enviar_email_sucesso(self, mock_get_client, client, auth_headers):
        """Testa envio de email com sucesso"""
        # Mock do email client
        mock_email_client = MagicMock()
        mock_email_client.enviar_email = AsyncMock(return_value={
            "sucesso": True,
            "provider": "sendgrid",
            "message_id": "msg_123456",
            "destinatario": "teste@exemplo.com"
        })
        mock_get_client.return_value = mock_email_client

        payload = {
            "destinatario": "teste@exemplo.com",
            "assunto": "Teste de email",
            "corpo_html": "<h1>Olá!</h1><p>Este é um teste.</p>",
            "corpo_texto": "Olá! Este é um teste."
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/email/enviar",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["sucesso"] is True
        assert data["provider"] == "sendgrid"
        assert data["message_id"] == "msg_123456"

    @patch('app.integrations.comunicacao_router.get_email_client')
    def test_enviar_email_com_cc_bcc(self, mock_get_client, client, auth_headers):
        """Testa envio de email com CC e BCC"""
        mock_email_client = MagicMock()
        mock_email_client.enviar_email = AsyncMock(return_value={
            "sucesso": True,
            "provider": "sendgrid",
            "message_id": "msg_789"
        })
        mock_get_client.return_value = mock_email_client

        payload = {
            "destinatario": "principal@exemplo.com",
            "assunto": "Email com cópias",
            "corpo_html": "<p>Teste com CC e BCC</p>",
            "cc": ["copia1@exemplo.com", "copia2@exemplo.com"],
            "bcc": ["oculta@exemplo.com"]
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/email/enviar",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        mock_email_client.enviar_email.assert_called_once()
        call_args = mock_email_client.enviar_email.call_args
        assert call_args.kwargs["cc"] == ["copia1@exemplo.com", "copia2@exemplo.com"]
        assert call_args.kwargs["bcc"] == ["oculta@exemplo.com"]

    @patch('app.integrations.comunicacao_router.get_email_client')
    def test_enviar_email_erro(self, mock_get_client, client, auth_headers):
        """Testa erro ao enviar email"""
        mock_email_client = MagicMock()
        mock_email_client.enviar_email = AsyncMock(return_value={
            "sucesso": False,
            "provider": "sendgrid",
            "erro": "Destinatário inválido"
        })
        mock_get_client.return_value = mock_email_client

        payload = {
            "destinatario": "invalido",
            "assunto": "Teste",
            "corpo_html": "<p>Teste</p>"
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/email/enviar",
                json=payload,
                headers=auth_headers
            )

        # Pode retornar 200 com sucesso=False ou 422 dependendo da validação
        assert response.status_code in [200, 422]

    @patch('app.integrations.comunicacao_router.get_email_client')
    def test_enviar_template_sendgrid(self, mock_get_client, client, auth_headers):
        """Testa envio de email com template SendGrid"""
        mock_email_client = MagicMock()
        mock_email_client.provider = EmailProvider.SENDGRID
        mock_email_client.enviar_template = AsyncMock(return_value={
            "sucesso": True,
            "provider": "sendgrid",
            "message_id": "template_msg_123",
            "template_id": "d-abc123"
        })
        mock_get_client.return_value = mock_email_client

        payload = {
            "destinatario": "cliente@exemplo.com",
            "template_id": "d-abc123",
            "dados_template": {
                "nome": "João",
                "produto": "Cimento",
                "quantidade": 10
            }
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/email/template",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["sucesso"] is True
        assert data["template_id"] == "d-abc123"

    @patch('app.integrations.comunicacao_router.get_email_client')
    def test_enviar_template_aws_ses_erro(self, mock_get_client, client, auth_headers):
        """Testa que template não funciona com AWS SES"""
        mock_email_client = MagicMock()
        mock_email_client.provider = EmailProvider.AWS_SES
        mock_get_client.return_value = mock_email_client

        payload = {
            "destinatario": "cliente@exemplo.com",
            "template_id": "d-abc123",
            "dados_template": {"nome": "João"}
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/email/template",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 400


class TestSMSEndpoints:
    """Testes dos endpoints de SMS"""

    @patch('app.integrations.comunicacao_router.get_sms_client')
    def test_enviar_sms_sucesso(self, mock_get_client, client, auth_headers):
        """Testa envio de SMS com sucesso"""
        mock_sms_client = MagicMock()
        mock_sms_client.enviar_sms = AsyncMock(return_value={
            "sucesso": True,
            "message_sid": "SM123456",
            "status": "sent",
            "destinatario": "+5511999999999",
            "segmentos": 1,
            "preco": "0.05",
            "moeda": "USD"
        })
        mock_get_client.return_value = mock_sms_client

        payload = {
            "destinatario": "+5511999999999",
            "mensagem": "Seu código de verificação é: 123456"
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/sms/enviar",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["sucesso"] is True
        assert data["message_sid"] == "SM123456"
        assert data["destinatario"] == "+5511999999999"

    @patch('app.integrations.comunicacao_router.get_sms_client')
    def test_enviar_sms_erro(self, mock_get_client, client, auth_headers):
        """Testa erro ao enviar SMS"""
        mock_sms_client = MagicMock()
        mock_sms_client.enviar_sms = AsyncMock(return_value={
            "sucesso": False,
            "erro": "Número inválido",
            "codigo_erro": "21211"
        })
        mock_get_client.return_value = mock_sms_client

        payload = {
            "destinatario": "+55119999",  # Número incompleto
            "mensagem": "Teste"
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/sms/enviar",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["sucesso"] is False
        assert "erro" in data

    @patch('app.integrations.comunicacao_router.get_sms_client')
    def test_consultar_sms(self, mock_get_client, client, auth_headers):
        """Testa consulta de status de SMS"""
        mock_sms_client = MagicMock()
        mock_sms_client.consultar_mensagem = AsyncMock(return_value={
            "message_sid": "SM123456",
            "status": "delivered",
            "de": "+5511988888888",
            "para": "+5511999999999",
            "corpo": "Teste de SMS",
            "data_criacao": "2025-11-19T10:00:00Z",
            "data_envio": "2025-11-19T10:00:05Z",
            "segmentos": 1,
            "preco": "0.05"
        })
        mock_get_client.return_value = mock_sms_client

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/comunicacao/sms/consultar/SM123456",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["message_sid"] == "SM123456"
        assert data["status"] == "delivered"


class TestWhatsAppEndpoints:
    """Testes dos endpoints de WhatsApp"""

    @patch('app.integrations.comunicacao_router.get_sms_client')
    def test_enviar_whatsapp_sucesso(self, mock_get_client, client, auth_headers):
        """Testa envio de WhatsApp com sucesso"""
        mock_sms_client = MagicMock()
        mock_sms_client.enviar_whatsapp = AsyncMock(return_value={
            "sucesso": True,
            "message_sid": "SM789012",
            "status": "queued",
            "destinatario": "+5511999999999",
            "canal": "whatsapp"
        })
        mock_get_client.return_value = mock_sms_client

        payload = {
            "destinatario": "+5511999999999",
            "mensagem": "Olá! Seu pedido foi confirmado."
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/whatsapp/enviar",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["sucesso"] is True
        assert data["canal"] == "whatsapp"

    @patch('app.integrations.comunicacao_router.get_sms_client')
    def test_enviar_whatsapp_com_midia(self, mock_get_client, client, auth_headers):
        """Testa envio de WhatsApp com mídia"""
        mock_sms_client = MagicMock()
        mock_sms_client.enviar_whatsapp = AsyncMock(return_value={
            "sucesso": True,
            "message_sid": "SM345678",
            "status": "queued",
            "canal": "whatsapp"
        })
        mock_get_client.return_value = mock_sms_client

        payload = {
            "destinatario": "+5511999999999",
            "mensagem": "Veja o boleto anexo",
            "media_url": "https://exemplo.com/boleto.pdf"
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/whatsapp/enviar",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 200
        mock_sms_client.enviar_whatsapp.assert_called_once()
        call_args = mock_sms_client.enviar_whatsapp.call_args
        assert call_args.kwargs["media_url"] == "https://exemplo.com/boleto.pdf"

    @patch('app.integrations.comunicacao_router.get_sms_client')
    def test_verificar_numero_valido(self, mock_get_client, client, auth_headers):
        """Testa verificação de número válido"""
        mock_sms_client = MagicMock()
        mock_sms_client.verificar_numero = AsyncMock(return_value={
            "valido": True,
            "numero_formatado": "+5511999999999",
            "numero_nacional": "(11) 99999-9999",
            "pais": "BR",
            "operadora": "Vivo",
            "tipo": "mobile"
        })
        mock_get_client.return_value = mock_sms_client

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/comunicacao/numero/verificar/+5511999999999",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["valido"] is True
        assert data["pais"] == "BR"
        assert data["operadora"] == "Vivo"

    @patch('app.integrations.comunicacao_router.get_sms_client')
    def test_verificar_numero_invalido(self, mock_get_client, client, auth_headers):
        """Testa verificação de número inválido"""
        mock_sms_client = MagicMock()
        mock_sms_client.verificar_numero = AsyncMock(return_value={
            "valido": False,
            "erro": "Número não encontrado"
        })
        mock_get_client.return_value = mock_sms_client

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.get(
                "/api/v1/integrations/comunicacao/numero/verificar/+55119999",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["valido"] is False


class TestHealthCheck:
    """Testes do health check"""

    @patch('app.integrations.comunicacao_router.settings')
    def test_health_check_tudo_configurado(self, mock_settings, client):
        """Testa health check com todos os provedores configurados"""
        mock_settings.SENDGRID_API_KEY = "SG.test"
        mock_settings.AWS_SES_ACCESS_KEY = "aws_test"
        mock_settings.TWILIO_ACCOUNT_SID = "AC123"
        mock_settings.TWILIO_AUTH_TOKEN = "token123"

        response = client.get("/api/v1/integrations/comunicacao/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["provedores"]["sendgrid"] is True
        assert data["provedores"]["aws_ses"] is True
        assert data["provedores"]["twilio"] is True
        assert data["email_ativo"] is True
        assert data["sms_ativo"] is True

    @patch('app.integrations.comunicacao_router.settings')
    def test_health_check_apenas_sendgrid(self, mock_settings, client):
        """Testa health check com apenas SendGrid configurado"""
        mock_settings.SENDGRID_API_KEY = "SG.test"
        mock_settings.AWS_SES_ACCESS_KEY = None
        mock_settings.TWILIO_ACCOUNT_SID = None
        mock_settings.TWILIO_AUTH_TOKEN = None

        response = client.get("/api/v1/integrations/comunicacao/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["provedores"]["sendgrid"] is True
        assert data["provedores"]["twilio"] is False
        assert data["email_ativo"] is True
        assert data["sms_ativo"] is False

    def test_health_check_sem_configuracao(self, client):
        """Testa health check sem nenhum provedor configurado"""
        with patch('app.integrations.comunicacao_router.settings.SENDGRID_API_KEY', None):
            with patch('app.integrations.comunicacao_router.settings.AWS_SES_ACCESS_KEY', None):
                with patch('app.integrations.comunicacao_router.settings.TWILIO_ACCOUNT_SID', None):
                    response = client.get("/api/v1/integrations/comunicacao/health")

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "sem_configuracao"
                    assert data["email_ativo"] is False
                    assert data["sms_ativo"] is False


class TestValidacoes:
    """Testes de validação de campos"""

    def test_email_invalido(self, client, auth_headers):
        """Testa envio com email inválido"""
        payload = {
            "destinatario": "email_invalido",
            "assunto": "Teste",
            "corpo_html": "<p>Teste</p>"
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/email/enviar",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 422

    def test_sms_mensagem_muito_longa(self, client, auth_headers):
        """Testa SMS com mensagem muito longa"""
        payload = {
            "destinatario": "+5511999999999",
            "mensagem": "A" * 1601  # Excede limite de 1600
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/sms/enviar",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 422

    def test_campos_obrigatorios_email(self, client, auth_headers):
        """Testa campos obrigatórios do email"""
        payload = {
            "destinatario": "teste@exemplo.com",
            # Falta assunto e corpo_html
        }

        with patch('app.integrations.comunicacao_router.get_current_user', return_value=MagicMock(id=1)):
            response = client.post(
                "/api/v1/integrations/comunicacao/email/enviar",
                json=payload,
                headers=auth_headers
            )

        assert response.status_code == 422
