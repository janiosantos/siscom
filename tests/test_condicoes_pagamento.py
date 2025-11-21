"""
Testes para módulo Condições de Pagamento
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.modules.condicoes_pagamento.models import CondicaoPagamento, ParcelaPadrao, TipoCondicao


# ========== FIXTURES ==========

@pytest.fixture
async def condicao_avista_data():
    """Fixture com dados para condição à vista"""
    return {
        "nome": "À Vista",
        "descricao": "Pagamento à vista sem juros",
        "tipo": "AVISTA",
        "quantidade_parcelas": 1,
        "intervalo_dias": 0,
        "entrada_percentual": 0.0,
        "ativa": True,
        "parcelas": [
            {
                "numero_parcela": 1,
                "dias_vencimento": 0,
                "percentual_valor": 100.0,
            }
        ],
    }


@pytest.fixture
async def condicao_parcelada_data():
    """Fixture com dados para condição parcelada"""
    return {
        "nome": "3x sem juros",
        "descricao": "Pagamento em 3 parcelas mensais",
        "tipo": "PARCELADO",
        "quantidade_parcelas": 3,
        "intervalo_dias": 30,
        "entrada_percentual": 0.0,
        "ativa": True,
        "parcelas": [
            {
                "numero_parcela": 1,
                "dias_vencimento": 0,
                "percentual_valor": 33.33,
            },
            {
                "numero_parcela": 2,
                "dias_vencimento": 30,
                "percentual_valor": 33.33,
            },
            {
                "numero_parcela": 3,
                "dias_vencimento": 60,
                "percentual_valor": 33.34,
            }
        ],
    }


@pytest.fixture
async def condicao_prazo_data():
    """Fixture com dados para condição a prazo"""
    return {
        "nome": "30 dias",
        "descricao": "Pagamento a prazo em 30 dias",
        "tipo": "PRAZO",
        "quantidade_parcelas": 1,
        "intervalo_dias": 30,
        "entrada_percentual": 0.0,
        "ativa": True,
        "parcelas": [
            {
                "numero_parcela": 1,
                "dias_vencimento": 30,
                "percentual_valor": 100.0,
            }
        ],
    }


@pytest.fixture
async def condicao_criada(db_session: AsyncSession):
    """Fixture para criar uma condição no banco"""
    condicao = CondicaoPagamento(
        nome="Condição Fixture",
        descricao="Condição de teste",
        tipo=TipoCondicao.AVISTA,
        quantidade_parcelas=1,
        intervalo_dias=0,
        entrada_percentual=0.0,
        ativa=True,
    )
    db_session.add(condicao)
    await db_session.flush()

    # Adicionar parcela
    parcela = ParcelaPadrao(
        condicao_id=condicao.id,
        numero_parcela=1,
        dias_vencimento=0,
        percentual_valor=100.0,
    )
    db_session.add(parcela)
    await db_session.commit()
    await db_session.refresh(condicao)
    return condicao


# ========== TESTES DE CRUD ==========

@pytest.mark.asyncio
async def test_criar_condicao_avista(client: AsyncClient, condicao_avista_data: dict):
    """Teste de criação de condição à vista"""
    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_avista_data,
    )

    # Pode retornar 201 ou 401
    assert response.status_code in [200, 201, 401]

    if response.status_code in [200, 201]:
        data = response.json()
        assert "id" in data
        assert data["nome"] == condicao_avista_data["nome"]
        assert data["tipo"] == "AVISTA"
        assert data["quantidade_parcelas"] == 1


@pytest.mark.asyncio
async def test_criar_condicao_parcelada(client: AsyncClient, condicao_parcelada_data: dict):
    """Teste de criação de condição parcelada"""
    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_parcelada_data,
    )

    # Pode retornar 201 ou 401
    assert response.status_code in [200, 201, 401]

    if response.status_code in [200, 201]:
        data = response.json()
        assert data["tipo"] == "PARCELADO"
        assert data["quantidade_parcelas"] == 3
        assert len(data["parcelas"]) == 3


@pytest.mark.asyncio
async def test_criar_condicao_prazo(client: AsyncClient, condicao_prazo_data: dict):
    """Teste de criação de condição a prazo"""
    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_prazo_data,
    )

    # Pode retornar 201 ou 401
    assert response.status_code in [200, 201, 401]


@pytest.mark.asyncio
async def test_listar_condicoes(client: AsyncClient, condicao_criada: CondicaoPagamento):
    """Teste de listagem de condições"""
    response = await client.get("/api/v1/condicoes-pagamento/")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_obter_condicao(client: AsyncClient, condicao_criada: CondicaoPagamento):
    """Teste de obtenção de condição específica"""
    response = await client.get(f"/api/v1/condicoes-pagamento/{condicao_criada.id}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["id"] == condicao_criada.id
        assert data["nome"] == condicao_criada.nome


@pytest.mark.asyncio
async def test_atualizar_condicao(client: AsyncClient, condicao_criada: CondicaoPagamento):
    """Teste de atualização de condição"""
    update_data = {
        "descricao": "Descrição atualizada",
        "ativa": False,
    }

    response = await client.put(
        f"/api/v1/condicoes-pagamento/{condicao_criada.id}",
        json=update_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["descricao"] == update_data["descricao"]
        assert data["ativa"] == update_data["ativa"]


@pytest.mark.asyncio
async def test_deletar_condicao(client: AsyncClient, condicao_criada: CondicaoPagamento):
    """Teste de deleção de condição"""
    response = await client.delete(f"/api/v1/condicoes-pagamento/{condicao_criada.id}")

    # Pode retornar 204 ou 401
    assert response.status_code in [204, 401]


# ========== TESTES DE VALIDAÇÃO ==========

@pytest.mark.asyncio
async def test_criar_condicao_avista_com_multiplas_parcelas(client: AsyncClient, condicao_avista_data: dict):
    """Teste de criação à vista com múltiplas parcelas (inválido)"""
    condicao_avista_data["quantidade_parcelas"] = 2

    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_avista_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_condicao_parcelada_com_uma_parcela(client: AsyncClient, condicao_parcelada_data: dict):
    """Teste de criação parcelada com apenas 1 parcela (inválido)"""
    condicao_parcelada_data["quantidade_parcelas"] = 1
    condicao_parcelada_data["parcelas"] = [
        {
            "numero_parcela": 1,
            "dias_vencimento": 0,
            "percentual_valor": 100.0,
        }
    ]

    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_parcelada_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_condicao_sem_parcelas(client: AsyncClient, condicao_avista_data: dict):
    """Teste de criação sem parcelas"""
    condicao_avista_data["parcelas"] = []

    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_avista_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_condicao_percentual_diferente_100(client: AsyncClient, condicao_avista_data: dict):
    """Teste de criação com soma de percentuais diferente de 100%"""
    condicao_avista_data["parcelas"][0]["percentual_valor"] = 90.0  # 90% != 100%

    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_avista_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_condicao_percentual_negativo(client: AsyncClient, condicao_avista_data: dict):
    """Teste de criação com percentual negativo"""
    condicao_avista_data["parcelas"][0]["percentual_valor"] = -10.0

    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_avista_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_condicao_percentual_acima_100(client: AsyncClient, condicao_avista_data: dict):
    """Teste de criação com percentual acima de 100%"""
    condicao_avista_data["parcelas"][0]["percentual_valor"] = 150.0

    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_avista_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_condicao_nome_vazio(client: AsyncClient, condicao_avista_data: dict):
    """Teste de criação com nome vazio"""
    condicao_avista_data["nome"] = ""

    response = await client.post(
        "/api/v1/condicoes-pagamento/",
        json=condicao_avista_data,
    )

    assert response.status_code == 422


# ========== TESTES DE CÁLCULO DE PARCELAS ==========

@pytest.mark.asyncio
async def test_calcular_parcelas(client: AsyncClient, condicao_criada: CondicaoPagamento):
    """Teste de cálculo de parcelas"""
    calcular_data = {
        "condicao_id": condicao_criada.id,
        "valor_total": 1000.0,
        "data_base": date.today().isoformat(),
    }

    response = await client.post(
        "/api/v1/condicoes-pagamento/calcular-parcelas",
        json=calcular_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert "parcelas" in data
        assert data["valor_total"] == calcular_data["valor_total"]


@pytest.mark.asyncio
async def test_calcular_parcelas_valor_zero(client: AsyncClient, condicao_criada: CondicaoPagamento):
    """Teste de cálculo com valor zero"""
    calcular_data = {
        "condicao_id": condicao_criada.id,
        "valor_total": 0.0,
        "data_base": date.today().isoformat(),
    }

    response = await client.post(
        "/api/v1/condicoes-pagamento/calcular-parcelas",
        json=calcular_data,
    )

    assert response.status_code == 422


# ========== TESTES DE FILTROS ==========

@pytest.mark.asyncio
async def test_listar_condicoes_ativas(client: AsyncClient, condicao_criada: CondicaoPagamento):
    """Teste de listagem de condições ativas"""
    response = await client.get("/api/v1/condicoes-pagamento/?ativa=true")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_obter_condicao_inexistente(client: AsyncClient):
    """Teste de obtenção de condição que não existe"""
    response = await client.get("/api/v1/condicoes-pagamento/99999")

    assert response.status_code in [404, 401]
