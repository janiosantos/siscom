"""
Testes de integração para endpoints de Export
"""
import pytest
from httpx import AsyncClient
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_export_dashboard_stats_csv(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/dashboard - CSV stats"""
    response = await client.post(
        "/api/v1/export/dashboard",
        headers=auth_headers,
        json={
            "formato": "csv",
            "tipo": "stats"
        }
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert ".csv" in response.headers["content-disposition"]

    content = response.content.decode('utf-8-sig')
    assert "Métrica" in content
    assert "Valor" in content


@pytest.mark.asyncio
async def test_export_dashboard_vendas_dia_excel(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/dashboard - Excel vendas por dia"""
    try:
        import openpyxl
        OPENPYXL_AVAILABLE = True
    except ImportError:
        OPENPYXL_AVAILABLE = False

    if not OPENPYXL_AVAILABLE:
        pytest.skip("openpyxl não disponível")

    hoje = date.today()
    response = await client.post(
        "/api/v1/export/dashboard",
        headers=auth_headers,
        json={
            "formato": "excel",
            "tipo": "vendas_dia",
            "filtros": {
                "data_inicio": str(hoje - timedelta(days=30)),
                "data_fim": str(hoje)
            }
        }
    )

    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]
    assert ".xlsx" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_export_dashboard_produtos(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/dashboard - Produtos mais vendidos"""
    response = await client.post(
        "/api/v1/export/dashboard",
        headers=auth_headers,
        json={
            "formato": "csv",
            "tipo": "produtos"
        }
    )

    assert response.status_code == 200
    content = response.content.decode('utf-8-sig')
    assert "Produto" in content
    assert "Quantidade" in content


@pytest.mark.asyncio
async def test_export_dashboard_vendedores(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/dashboard - Vendas por vendedor"""
    response = await client.post(
        "/api/v1/export/dashboard",
        headers=auth_headers,
        json={
            "formato": "csv",
            "tipo": "vendedores"
        }
    )

    assert response.status_code == 200
    content = response.content.decode('utf-8-sig')
    assert "Vendedor" in content
    assert "Ticket Médio" in content


@pytest.mark.asyncio
async def test_export_dashboard_status(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/dashboard - Status pedidos"""
    response = await client.post(
        "/api/v1/export/dashboard",
        headers=auth_headers,
        json={
            "formato": "csv",
            "tipo": "status"
        }
    )

    assert response.status_code == 200
    content = response.content.decode('utf-8-sig')
    assert "Status" in content
    assert "Percentual" in content


@pytest.mark.asyncio
async def test_export_orcamentos_csv(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/orcamentos - CSV"""
    response = await client.post(
        "/api/v1/export/orcamentos",
        headers=auth_headers,
        json={
            "formato": "csv"
        }
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "orcamentos_" in response.headers["content-disposition"]

    content = response.content.decode('utf-8-sig')
    assert "Cliente" in content
    assert "Valor Total" in content


@pytest.mark.asyncio
async def test_export_orcamentos_com_filtros(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/orcamentos - Com filtros"""
    hoje = date.today()
    response = await client.post(
        "/api/v1/export/orcamentos",
        headers=auth_headers,
        json={
            "formato": "csv",
            "filtros": {
                "data_inicio": str(hoje - timedelta(days=60)),
                "data_fim": str(hoje),
                "status": "pendente"
            }
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_export_orcamentos_por_ids(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/orcamentos - Por IDs específicos"""
    response = await client.post(
        "/api/v1/export/orcamentos",
        headers=auth_headers,
        json={
            "formato": "csv",
            "ids": [1, 2, 3]
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_export_vendas_csv(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/vendas - CSV"""
    response = await client.post(
        "/api/v1/export/vendas",
        headers=auth_headers,
        json={
            "formato": "csv"
        }
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "vendas_" in response.headers["content-disposition"]

    content = response.content.decode('utf-8-sig')
    assert "Cliente" in content
    assert "Forma Pagamento" in content
    assert "Valor Final" in content


@pytest.mark.asyncio
async def test_export_vendas_filtro_vendedor(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/vendas - Filtro por vendedor"""
    response = await client.post(
        "/api/v1/export/vendas",
        headers=auth_headers,
        json={
            "formato": "csv",
            "filtros": {
                "vendedor_id": 1
            }
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_export_vendas_filtro_cliente(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/vendas - Filtro por cliente"""
    response = await client.post(
        "/api/v1/export/vendas",
        headers=auth_headers,
        json={
            "formato": "csv",
            "filtros": {
                "cliente_id": 1
            }
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_export_vendas_filtro_status(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/vendas - Filtro por status"""
    response = await client.post(
        "/api/v1/export/vendas",
        headers=auth_headers,
        json={
            "formato": "csv",
            "filtros": {
                "status": "finalizada"
            }
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_export_produtos_csv(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/produtos - CSV"""
    response = await client.post(
        "/api/v1/export/produtos",
        headers=auth_headers,
        json={
            "formato": "csv",
            "apenas_ativos": True
        }
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "produtos_" in response.headers["content-disposition"]

    content = response.content.decode('utf-8-sig')
    assert "Código" in content
    assert "Descrição" in content
    assert "Preço Venda" in content


@pytest.mark.asyncio
async def test_export_produtos_por_categoria(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/produtos - Por categoria"""
    response = await client.post(
        "/api/v1/export/produtos",
        headers=auth_headers,
        json={
            "formato": "csv",
            "categoria_id": 1,
            "apenas_ativos": True
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_export_produtos_todos(client: AsyncClient, auth_headers):
    """Testa POST /api/v1/export/produtos - Todos (ativos e inativos)"""
    response = await client.post(
        "/api/v1/export/produtos",
        headers=auth_headers,
        json={
            "formato": "csv",
            "apenas_ativos": False
        }
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_export_sem_autenticacao(client: AsyncClient):
    """Testa que endpoints requerem autenticação"""
    response = await client.post(
        "/api/v1/export/dashboard",
        json={
            "formato": "csv",
            "tipo": "stats"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_export_formato_invalido(client: AsyncClient, auth_headers):
    """Testa validação de formato inválido"""
    response = await client.post(
        "/api/v1/export/dashboard",
        headers=auth_headers,
        json={
            "formato": "pdf",  # Formato não suportado
            "tipo": "stats"
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_export_tipo_invalido(client: AsyncClient, auth_headers):
    """Testa validação de tipo inválido"""
    response = await client.post(
        "/api/v1/export/dashboard",
        headers=auth_headers,
        json={
            "formato": "csv",
            "tipo": "invalid_type"
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_export_excel_formato_correto(client: AsyncClient, auth_headers):
    """Testa que Excel retorna tipo MIME correto"""
    try:
        import openpyxl
        OPENPYXL_AVAILABLE = True
    except ImportError:
        OPENPYXL_AVAILABLE = False

    if not OPENPYXL_AVAILABLE:
        pytest.skip("openpyxl não disponível")

    response = await client.post(
        "/api/v1/export/dashboard",
        headers=auth_headers,
        json={
            "formato": "excel",
            "tipo": "stats"
        }
    )

    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    assert ".xlsx" in response.headers["content-disposition"]


# ===== Fixture de autenticação =====

@pytest.fixture
async def auth_headers(client: AsyncClient, db_session):
    """Cria headers com token de autenticação"""
    from app.modules.auth.models import User, Role

    # Criar role admin
    admin_role = Role(nome="Admin", descricao="Administrador")
    db_session.add(admin_role)
    await db_session.commit()

    # Criar usuário admin
    admin_user = User(
        nome="Admin Export",
        email="export@test.com",
        senha_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eX.4eDZMvHYe",
        ativo=True,
        role_id=admin_role.id
    )
    db_session.add(admin_user)
    await db_session.commit()

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "export@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]

    return {
        "Authorization": f"Bearer {access_token}"
    }
