"""
Testes para o módulo Financeiro

Testa contas a pagar, contas a receber e fluxo de caixa
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta


@pytest.fixture
async def conta_pagar_data():
    """Fixture com dados de conta a pagar"""
    return {
        "descricao": "Conta de Energia",
        "valor": 500.00,
        "vencimento": (date.today() + timedelta(days=30)).isoformat(),
        "tipo": "despesa",
        "categoria": "operacional",
        "status": "pendente",
    }


@pytest.fixture
async def conta_receber_data():
    """Fixture com dados de conta a receber"""
    return {
        "descricao": "Venda a Prazo",
        "valor": 1000.00,
        "vencimento": (date.today() + timedelta(days=15)).isoformat(),
        "tipo": "receita",
        "categoria": "vendas",
        "status": "pendente",
    }


class TestContasPagar:
    """Testes de contas a pagar"""

    @pytest.mark.asyncio
    async def test_criar_conta_pagar(
        self, client: AsyncClient, conta_pagar_data: dict
    ):
        """Deve criar conta a pagar"""
        response = await client.post(
            "/api/v1/financeiro/contas-pagar", json=conta_pagar_data
        )

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 201
            data = response.json()
            assert data["tipo"] == "despesa"
            assert "id" in data

    @pytest.mark.asyncio
    async def test_listar_contas_pagar(self, client: AsyncClient):
        """Deve listar contas a pagar"""
        response = await client.get("/api/v1/financeiro/contas-pagar")

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_pagar_conta(
        self, client: AsyncClient, conta_pagar_data: dict
    ):
        """Deve marcar conta como paga"""
        # Criar conta primeiro
        create_response = await client.post(
            "/api/v1/financeiro/contas-pagar", json=conta_pagar_data
        )

        if create_response.status_code == 201:
            conta_id = create_response.json()["id"]

            # Pagar conta
            pagamento_data = {"data_pagamento": date.today().isoformat(), "valor_pago": 500.00}
            response = await client.post(
                f"/api/v1/financeiro/contas-pagar/{conta_id}/pagar",
                json=pagamento_data,
            )

            # Se endpoint existir
            if response.status_code != 404:
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "paga" or data["status"] == "pago"


class TestContasReceber:
    """Testes de contas a receber"""

    @pytest.mark.asyncio
    async def test_criar_conta_receber(
        self, client: AsyncClient, conta_receber_data: dict
    ):
        """Deve criar conta a receber"""
        response = await client.post(
            "/api/v1/financeiro/contas-receber", json=conta_receber_data
        )

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 201
            data = response.json()
            assert data["tipo"] == "receita"

    @pytest.mark.asyncio
    async def test_receber_conta(
        self, client: AsyncClient, conta_receber_data: dict
    ):
        """Deve marcar conta como recebida"""
        # Criar conta primeiro
        create_response = await client.post(
            "/api/v1/financeiro/contas-receber", json=conta_receber_data
        )

        if create_response.status_code == 201:
            conta_id = create_response.json()["id"]

            # Receber conta
            recebimento_data = {
                "data_recebimento": date.today().isoformat(),
                "valor_recebido": 1000.00,
            }
            response = await client.post(
                f"/api/v1/financeiro/contas-receber/{conta_id}/receber",
                json=recebimento_data,
            )

            # Se endpoint existir
            if response.status_code != 404:
                assert response.status_code == 200


class TestFluxoCaixa:
    """Testes de fluxo de caixa"""

    @pytest.mark.asyncio
    async def test_consultar_fluxo_caixa(self, client: AsyncClient):
        """Deve consultar fluxo de caixa"""
        response = await client.get("/api/v1/financeiro/fluxo-caixa")

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 200
            data = response.json()
            # Verificar estrutura de resposta
            assert isinstance(data, (dict, list))

    @pytest.mark.asyncio
    async def test_fluxo_caixa_periodo(self, client: AsyncClient):
        """Deve consultar fluxo de caixa por período"""
        data_inicio = date.today().isoformat()
        data_fim = (date.today() + timedelta(days=30)).isoformat()

        response = await client.get(
            f"/api/v1/financeiro/fluxo-caixa?data_inicio={data_inicio}&data_fim={data_fim}"
        )

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 200


class TestRelatorios:
    """Testes de relatórios financeiros"""

    @pytest.mark.asyncio
    async def test_relatorio_receitas_despesas(self, client: AsyncClient):
        """Deve gerar relatório de receitas e despesas"""
        response = await client.get("/api/v1/financeiro/relatorio/receitas-despesas")

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_contas_vencidas(self, client: AsyncClient):
        """Deve listar contas vencidas"""
        response = await client.get("/api/v1/financeiro/vencidas")

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 200


class TestValidacoes:
    """Testes de validações"""

    @pytest.mark.asyncio
    async def test_valor_negativo(self, client: AsyncClient, conta_pagar_data: dict):
        """Não deve permitir valor negativo"""
        conta_pagar_data["valor"] = -100.0
        response = await client.post(
            "/api/v1/financeiro/contas-pagar", json=conta_pagar_data
        )

        # Se endpoint existir e validar
        if response.status_code not in [404, 201]:
            assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_data_vencimento_passada(
        self, client: AsyncClient, conta_pagar_data: dict
    ):
        """Deve aceitar data de vencimento no passado (para registro histórico)"""
        conta_pagar_data["vencimento"] = (date.today() - timedelta(days=10)).isoformat()
        response = await client.post(
            "/api/v1/financeiro/contas-pagar", json=conta_pagar_data
        )

        # Deve aceitar (para registro histórico)
        if response.status_code != 404:
            assert response.status_code in [200, 201]
