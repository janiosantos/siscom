"""
Testes de integração para endpoints do Dashboard
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, date
from decimal import Decimal

from app.modules.vendas.models import Venda
from app.modules.produtos.models import Produto
from app.modules.categorias.models import Categoria
from app.modules.clientes.models import Cliente
from app.modules.auth.models import User, Role


@pytest.mark.asyncio
async def test_get_dashboard_stats(client: AsyncClient, auth_headers, sample_vendas):
    """Testa GET /api/v1/dashboard/stats"""
    response = await client.get(
        "/api/v1/dashboard/stats",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "vendas_hoje" in data
    assert "vendas_mes" in data
    assert "pedidos_abertos" in data
    assert "pedidos_atrasados" in data
    assert "ticket_medio" in data
    assert "faturamento_mes" in data
    assert "crescimento_mes" in data
    assert "meta_mes" in data

    assert isinstance(data["vendas_hoje"], int)
    assert isinstance(data["vendas_mes"], int)
    assert isinstance(data["ticket_medio"], (int, float))
    assert isinstance(data["faturamento_mes"], (int, float))


@pytest.mark.asyncio
async def test_get_vendas_por_dia(client: AsyncClient, auth_headers, sample_vendas):
    """Testa GET /api/v1/dashboard/vendas-por-dia"""
    hoje = date.today()
    response = await client.get(
        f"/api/v1/dashboard/vendas-por-dia?data_inicio={hoje - timedelta(days=7)}&data_fim={hoje}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "data" in item
        assert "vendas" in item
        assert "faturamento" in item
        assert isinstance(item["vendas"], int)
        assert isinstance(item["faturamento"], (int, float))


@pytest.mark.asyncio
async def test_get_vendas_por_dia_sem_parametros(client: AsyncClient, auth_headers):
    """Testa GET /api/v1/dashboard/vendas-por-dia sem parâmetros (últimos 30 dias)"""
    response = await client.get(
        "/api/v1/dashboard/vendas-por-dia",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_produtos_mais_vendidos(client: AsyncClient, auth_headers, sample_vendas):
    """Testa GET /api/v1/dashboard/produtos-mais-vendidos"""
    response = await client.get(
        "/api/v1/dashboard/produtos-mais-vendidos?limit=10",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "produto_id" in item
        assert "produto" in item
        assert "quantidade" in item
        assert "faturamento" in item
        assert isinstance(item["quantidade"], (int, float))
        assert isinstance(item["faturamento"], (int, float))


@pytest.mark.asyncio
async def test_get_vendas_por_vendedor(client: AsyncClient, auth_headers, sample_vendas):
    """Testa GET /api/v1/dashboard/vendas-por-vendedor"""
    response = await client.get(
        "/api/v1/dashboard/vendas-por-vendedor",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "vendedor_id" in item
        assert "vendedor" in item
        assert "vendas" in item
        assert "faturamento" in item
        assert "ticket_medio" in item
        assert isinstance(item["vendas"], int)
        assert isinstance(item["faturamento"], (int, float))


@pytest.mark.asyncio
async def test_get_status_pedidos(client: AsyncClient, auth_headers, sample_vendas):
    """Testa GET /api/v1/dashboard/status-pedidos"""
    response = await client.get(
        "/api/v1/dashboard/status-pedidos",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    if len(data) > 0:
        item = data[0]
        assert "status" in item
        assert "quantidade" in item
        assert "percentual" in item
        assert isinstance(item["quantidade"], int)
        assert isinstance(item["percentual"], (int, float))


@pytest.mark.asyncio
async def test_dashboard_stats_sem_autenticacao(client: AsyncClient):
    """Testa que endpoints requerem autenticação"""
    response = await client.get("/api/v1/dashboard/stats")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_com_filtro_vendedor(client: AsyncClient, auth_headers, sample_user):
    """Testa filtro por vendedor em endpoints"""
    response = await client.get(
        f"/api/v1/dashboard/vendas-por-dia?vendedor_id={sample_user.id}",
        headers=auth_headers
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_com_data_invalida(client: AsyncClient, auth_headers):
    """Testa validação de datas inválidas"""
    response = await client.get(
        "/api/v1/dashboard/vendas-por-dia?data_inicio=invalid",
        headers=auth_headers
    )

    # Deve retornar erro de validação
    assert response.status_code == 422


# ===== Fixtures =====

@pytest.fixture
async def sample_user(db_session):
    """Cria usuário de teste"""
    user = User(
        nome="Vendedor Dashboard",
        email="dashboard@teste.com",
        senha_hash="hash123",
        ativo=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_cliente(db_session):
    """Cria cliente de teste"""
    cliente = Cliente(
        nome="Cliente Dashboard",
        cpf_cnpj="98765432100",
        tipo_pessoa="F",
        ativo=True
    )
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)
    return cliente


@pytest.fixture
async def sample_categoria(db_session):
    """Cria categoria de teste"""
    categoria = Categoria(
        nome="Materiais Dashboard",
        descricao="Materiais para teste"
    )
    db_session.add(categoria)
    await db_session.commit()
    await db_session.refresh(categoria)
    return categoria


@pytest.fixture
async def sample_produtos(db_session, sample_categoria):
    """Cria produtos de teste"""
    produtos = []
    for i in range(3):
        produto = Produto(
            codigo=f"DASH-{i:03d}",
            descricao=f"Produto Dashboard {i}",
            categoria_id=sample_categoria.id,
            unidade="UN",
            preco_custo=Decimal("30.00"),
            preco_venda=Decimal("60.00"),
            estoque_atual=Decimal("20.0"),
            ativo=True
        )
        db_session.add(produto)
        produtos.append(produto)

    await db_session.commit()
    for p in produtos:
        await db_session.refresh(p)

    return produtos


@pytest.fixture
async def sample_vendas(db_session, sample_user, sample_cliente):
    """Cria vendas de teste"""
    vendas = []
    hoje = datetime.now()

    for i in range(5):
        venda = Venda(
            data_venda=hoje - timedelta(days=i),
            cliente_id=sample_cliente.id,
            vendedor_id=sample_user.id,
            status="finalizada" if i < 3 else "aberta",
            forma_pagamento="pix",
            valor_total=Decimal("200.00"),
            desconto=Decimal("10.00"),
            valor_final=Decimal("190.00")
        )
        db_session.add(venda)
        vendas.append(venda)

    await db_session.commit()
    for v in vendas:
        await db_session.refresh(v)

    return vendas


@pytest.fixture
async def auth_headers(client: AsyncClient, db_session):
    """Cria headers com token de autenticação"""
    # Criar usuário admin
    admin_role = Role(nome="Admin", descricao="Administrador")
    db_session.add(admin_role)
    await db_session.commit()

    admin_user = User(
        nome="Admin Test",
        email="admin@test.com",
        senha_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eX.4eDZMvHYe",  # "password123"
        ativo=True,
        role_id=admin_role.id
    )
    db_session.add(admin_user)
    await db_session.commit()

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]

    return {
        "Authorization": f"Bearer {access_token}"
    }
