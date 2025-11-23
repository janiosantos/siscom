"""
Testes para integração Mercado Pago
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from app.integrations.mercadopago import MercadoPagoClient, converter_status_mp
from app.modules.pagamentos.models import StatusPagamento


@pytest.fixture
def mp_client():
    """Fixture para MercadoPago client com credenciais de teste"""
    access_token = "TEST-127924860584293-111909-8eb99a40f34eb5ba5c03fa2979196258-184641661"
    public_key = "TEST-040da26c-318d-46ff-b42e-4ef22fbf755f"
    return MercadoPagoClient(access_token=access_token, public_key=public_key)


class TestMercadoPagoClient:
    """Testes para MercadoPagoClient"""

    @pytest.mark.asyncio
    async def test_criar_pagamento_pix_sucesso(self, mp_client):
        """Testa criação de pagamento PIX com sucesso"""
        # Mock da resposta da API do Mercado Pago
        mock_response = {
            "id": 123456789,
            "status": "pending",
            "status_detail": "pending_waiting_payment",
            "transaction_amount": 150.00,
            "date_created": "2025-11-19T10:30:00.000-04:00",
            "date_approved": None,
            "payment_method_id": "pix",
            "point_of_interaction": {
                "type": "PIX",
                "transaction_data": {
                    "qr_code": "00020126580014br.gov.bcb.pix...",
                    "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
                    "ticket_url": "https://www.mercadopago.com.br/payments/123456789/ticket"
                }
            },
            "transaction_details": {
                "transaction_id": "123456789"
            },
            "external_reference": "VENDA-1234"
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            resultado = await mp_client.criar_pagamento_pix(
                valor=Decimal("150.00"),
                descricao="Venda #1234",
                email_pagador="cliente@test.com",
                external_reference="VENDA-1234"
            )

            assert resultado["id"] == 123456789
            assert resultado["status"] == "pending"
            assert resultado["qr_code"] == "00020126580014br.gov.bcb.pix..."
            assert resultado["qr_code_base64"] == "iVBORw0KGgoAAAANSUhEUgAA..."
            assert resultado["valor"] == 150.00
            assert resultado["external_reference"] == "VENDA-1234"

    @pytest.mark.asyncio
    async def test_criar_pagamento_pix_valor_minimo(self, mp_client):
        """Testa criação de pagamento PIX com valor mínimo"""
        mock_response = {
            "id": 987654321,
            "status": "pending",
            "transaction_amount": 1.00,
            "point_of_interaction": {
                "transaction_data": {
                    "qr_code": "00020126580014br.gov.bcb.pix...",
                    "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
                    "ticket_url": "https://www.mercadopago.com.br/payments/987654321/ticket"
                }
            },
            "transaction_details": {"transaction_id": "987654321"}
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            resultado = await mp_client.criar_pagamento_pix(
                valor=Decimal("1.00"),
                descricao="Teste valor mínimo"
            )

            assert resultado["id"] == 987654321
            assert resultado["valor"] == 1.00

    @pytest.mark.asyncio
    async def test_consultar_pagamento_aprovado(self, mp_client):
        """Testa consulta de pagamento aprovado"""
        mock_response = {
            "id": 123456789,
            "status": "approved",
            "status_detail": "accredited",
            "transaction_amount": 150.00,
            "date_created": "2025-11-19T10:30:00.000-04:00",
            "date_approved": "2025-11-19T10:31:23.000-04:00",
            "payment_method_id": "pix",
            "external_reference": "VENDA-1234"
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            resultado = await mp_client.consultar_pagamento(123456789)

            assert resultado["id"] == 123456789
            assert resultado["status"] == "approved"
            assert resultado["status_detail"] == "accredited"
            assert resultado["data_aprovacao"] is not None

    @pytest.mark.asyncio
    async def test_consultar_pagamento_pendente(self, mp_client):
        """Testa consulta de pagamento pendente"""
        mock_response = {
            "id": 123456789,
            "status": "pending",
            "status_detail": "pending_waiting_payment",
            "transaction_amount": 150.00,
            "date_created": "2025-11-19T10:30:00.000-04:00",
            "date_approved": None,
            "payment_method_id": "pix"
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            resultado = await mp_client.consultar_pagamento(123456789)

            assert resultado["status"] == "pending"
            assert resultado["data_aprovacao"] is None

    @pytest.mark.asyncio
    async def test_consultar_pagamento_rejeitado(self, mp_client):
        """Testa consulta de pagamento rejeitado"""
        mock_response = {
            "id": 123456789,
            "status": "rejected",
            "status_detail": "cc_rejected_bad_filled_security_code",
            "transaction_amount": 150.00,
            "date_created": "2025-11-19T10:30:00.000-04:00",
            "payment_method_id": "pix"
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            resultado = await mp_client.consultar_pagamento(123456789)

            assert resultado["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_cancelar_pagamento_sucesso(self, mp_client):
        """Testa cancelamento de pagamento"""
        mock_response = {
            "id": 123456789,
            "status": "cancelled",
            "status_detail": "by_collector"
        }

        with patch("httpx.AsyncClient.put") as mock_put:
            mock_put.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            resultado = await mp_client.cancelar_pagamento(123456789)

            assert resultado["id"] == 123456789
            assert resultado["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_processar_webhook_payment(self, mp_client):
        """Testa processamento de webhook tipo payment"""
        webhook_data = {
            "id": 123456,
            "live_mode": False,
            "type": "payment",
            "date_created": "2025-11-19T10:31:23Z",
            "action": "payment.updated",
            "data": {
                "id": "123456789"
            }
        }

        mock_payment_response = {
            "id": 123456789,
            "status": "approved",
            "status_detail": "accredited",
            "transaction_amount": 150.00,
            "date_approved": "2025-11-19T10:31:23.000-04:00",
            "payment_method_id": "pix"
        }

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=lambda: mock_payment_response,
                raise_for_status=lambda: None
            )

            resultado = await mp_client.processar_webhook(webhook_data)

            assert resultado["id"] == 123456789
            assert resultado["status"] == "approved"

    @pytest.mark.asyncio
    async def test_processar_webhook_merchant_order(self, mp_client):
        """Testa processamento de webhook tipo merchant_order"""
        webhook_data = {
            "id": 123456,
            "type": "merchant_order",
            "data": {
                "id": "999888777"
            }
        }

        # Para merchant_order, apenas retorna os dados básicos
        resultado = await mp_client.processar_webhook(webhook_data)

        assert resultado["merchant_order_id"] == "999888777"

    @pytest.mark.asyncio
    async def test_criar_preferencia_checkout(self, mp_client):
        """Testa criação de preferência de checkout"""
        items = [
            {
                "title": "Cimento CP-II 50kg",
                "quantity": 10,
                "unit_price": 35.90,
                "currency_id": "BRL"
            }
        ]

        mock_response = {
            "id": "987654321",
            "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=987654321",
            "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id=987654321"
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            resultado = await mp_client.criar_preferencia_checkout(
                items=items,
                external_reference="VENDA-5678"
            )

            assert resultado["id"] == "987654321"
            assert "init_point" in resultado
            assert "sandbox_init_point" in resultado

    @pytest.mark.asyncio
    async def test_criar_preferencia_checkout_com_back_urls(self, mp_client):
        """Testa criação de preferência com URLs de retorno"""
        items = [{"title": "Produto X", "quantity": 1, "unit_price": 100.00}]
        back_urls = {
            "success": "https://meusite.com/pagamento/sucesso",
            "failure": "https://meusite.com/pagamento/falha",
            "pending": "https://meusite.com/pagamento/pendente"
        }

        mock_response = {
            "id": "111222333",
            "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=111222333"
        }

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=201,
                json=lambda: mock_response,
                raise_for_status=lambda: None
            )

            resultado = await mp_client.criar_preferencia_checkout(
                items=items,
                back_urls=back_urls
            )

            assert resultado["id"] == "111222333"

    @pytest.mark.asyncio
    async def test_erro_api_mercadopago(self, mp_client):
        """Testa tratamento de erro da API do Mercado Pago"""
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("API Error: 401 Unauthorized")
            mock_post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await mp_client.criar_pagamento_pix(
                    valor=Decimal("100.00"),
                    descricao="Teste erro"
                )

            assert "401 Unauthorized" in str(exc_info.value)


class TestConversorStatus:
    """Testes para conversão de status MP -> Sistema"""

    def test_converter_status_pending(self):
        """Testa conversão de status pending"""
        assert converter_status_mp("pending") == StatusPagamento.PENDENTE

    def test_converter_status_approved(self):
        """Testa conversão de status approved"""
        assert converter_status_mp("approved") == StatusPagamento.APROVADO

    def test_converter_status_rejected(self):
        """Testa conversão de status rejected"""
        assert converter_status_mp("rejected") == StatusPagamento.REJEITADO

    def test_converter_status_cancelled(self):
        """Testa conversão de status cancelled"""
        assert converter_status_mp("cancelled") == StatusPagamento.CANCELADO

    def test_converter_status_refunded(self):
        """Testa conversão de status refunded"""
        assert converter_status_mp("refunded") == StatusPagamento.ESTORNADO

    def test_converter_status_in_process(self):
        """Testa conversão de status in_process"""
        assert converter_status_mp("in_process") == StatusPagamento.PROCESSANDO

    def test_converter_status_desconhecido(self):
        """Testa conversão de status desconhecido"""
        # Status desconhecido deve retornar PENDENTE como fallback
        assert converter_status_mp("unknown_status") == StatusPagamento.PENDENTE


class TestMercadoPagoRouter:
    """Testes para endpoints REST do Mercado Pago"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Testa endpoint de health check"""
        response = await client.get("/api/v1/integrations/mercadopago/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "mercadopago" in data
        assert "ambiente" in data

    @pytest.mark.asyncio
    async def test_criar_pagamento_pix_endpoint(self, client, auth_headers):
        """Testa endpoint de criação de pagamento PIX"""
        mock_response = {
            "id": 123456789,
            "status": "pending",
            "qr_code": "00020126580014br.gov.bcb.pix...",
            "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
            "ticket_url": "https://www.mercadopago.com.br/payments/123456789/ticket",
            "transaction_id": 123456789,
            "valor": 150.00,
            "data_criacao": "2025-11-19T10:30:00Z",
            "external_reference": "VENDA-1234"
        }

        with patch("app.integrations.mercadopago.MercadoPagoClient.criar_pagamento_pix") as mock_criar:
            mock_criar.return_value = mock_response

            payload = {
                "valor": 150.00,
                "descricao": "Venda #1234",
                "email_pagador": "cliente@test.com",
                "external_reference": "VENDA-1234"
            }

            response = await client.post(
                "/api/v1/integrations/mercadopago/pix",
                json=payload,
                headers=auth_headers
            )

            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 123456789
            assert data["status"] == "pending"
            assert "qr_code" in data

    @pytest.mark.asyncio
    async def test_criar_pagamento_pix_sem_auth(self, client):
        """Testa endpoint sem autenticação"""
        payload = {
            "valor": 100.00,
            "descricao": "Teste"
        }

        response = await client.post(
            "/api/v1/integrations/mercadopago/pix",
            json=payload
        )

        # Deve retornar 401 Unauthorized
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_consultar_pagamento_endpoint(self, client, auth_headers):
        """Testa endpoint de consulta de pagamento"""
        mock_response = {
            "id": 123456789,
            "status": "approved",
            "status_detail": "accredited",
            "valor": 150.00,
            "data_criacao": "2025-11-19T10:30:00Z",
            "data_aprovacao": "2025-11-19T10:31:23Z",
            "metodo_pagamento": "pix"
        }

        with patch("app.integrations.mercadopago.MercadoPagoClient.consultar_pagamento") as mock_consultar:
            mock_consultar.return_value = mock_response

            response = await client.get(
                "/api/v1/integrations/mercadopago/pagamento/123456789",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 123456789
            assert data["status"] == "approved"

    @pytest.mark.asyncio
    async def test_cancelar_pagamento_endpoint(self, client, auth_headers):
        """Testa endpoint de cancelamento"""
        mock_response = {
            "id": 123456789,
            "status": "cancelled"
        }

        with patch("app.integrations.mercadopago.MercadoPagoClient.cancelar_pagamento") as mock_cancelar:
            mock_cancelar.return_value = mock_response

            response = await client.delete(
                "/api/v1/integrations/mercadopago/pagamento/123456789",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["sucesso"] is True
            assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_webhook_endpoint(self, client):
        """Testa endpoint de webhook (sem auth)"""
        webhook_payload = {
            "id": 123456,
            "type": "payment",
            "data": {
                "id": "123456789"
            }
        }

        mock_response = {
            "id": 123456789,
            "status": "approved"
        }

        with patch("app.integrations.mercadopago.MercadoPagoClient.processar_webhook") as mock_webhook:
            mock_webhook.return_value = mock_response

            response = await client.post(
                "/api/v1/integrations/mercadopago/webhook",
                json=webhook_payload
            )

            # Webhook não requer autenticação
            assert response.status_code == 200
            data = response.json()
            assert data["sucesso"] is True
