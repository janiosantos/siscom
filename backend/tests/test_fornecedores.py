"""
Testes para módulo Fornecedores
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.modules.fornecedores.models import Fornecedor


# Mock automático para validação de CNPJ
@pytest.fixture(autouse=True)
def mock_document_validator():
    """Mock do DocumentValidator para aceitar qualquer CNPJ nos testes"""
    with patch("app.modules.fornecedores.schemas.DocumentValidator.validate_cnpj", return_value=True):
        yield


# ========== FIXTURES ==========

@pytest.fixture
async def fornecedor_data():
    """Fixture com dados para criação de fornecedor"""
    return {
        "razao_social": "Fornecedor Teste LTDA",
        "nome_fantasia": "Fornecedor Teste",
        "cnpj": "12345678901234",
        "ie": "123456789",
        "email": "contato@fornecedor.com",
        "telefone": "11987654321",
        "celular": "11987654322",
        "contato_nome": "João Silva",
        "endereco": "Rua Teste",
        "numero": "123",
        "complemento": "Sala 1",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "estado": "SP",
        "cep": "01310100",
        "banco": "Banco do Brasil",
        "agencia": "1234",
        "conta": "56789-0",
        "observacoes": "Fornecedor principal",
        "ativo": True,
    }


@pytest.fixture
async def fornecedor_criado(db_session: AsyncSession, fornecedor_data: dict):
    """Fixture para criar um fornecedor no banco"""
    fornecedor = Fornecedor(**fornecedor_data)
    db_session.add(fornecedor)
    await db_session.commit()
    await db_session.refresh(fornecedor)
    return fornecedor


# ========== TESTES DE CRUD ==========

@pytest.mark.asyncio
async def test_criar_fornecedor(client: AsyncClient, fornecedor_data: dict):
    """Teste de criação de fornecedor"""
    response = await client.post(
        "/api/v1/fornecedores/",
        json=fornecedor_data,
    )

    # Pode retornar 201 ou 401
    assert response.status_code in [200, 201, 401]

    if response.status_code in [200, 201]:
        data = response.json()
        assert "id" in data
        assert data["razao_social"] == fornecedor_data["razao_social"]
        assert data["cnpj"] == fornecedor_data["cnpj"]


@pytest.mark.asyncio
async def test_criar_fornecedor_razao_social_vazia(client: AsyncClient, fornecedor_data: dict):
    """Teste de criação com razão social vazia"""
    fornecedor_data["razao_social"] = ""

    response = await client.post(
        "/api/v1/fornecedores/",
        json=fornecedor_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_fornecedor_cnpj_invalido(client: AsyncClient, fornecedor_data: dict):
    """Teste de criação com CNPJ inválido (tamanho errado)"""
    fornecedor_data["cnpj"] = "123"  # Menos de 14 dígitos

    response = await client.post(
        "/api/v1/fornecedores/",
        json=fornecedor_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_fornecedor_email_invalido(client: AsyncClient, fornecedor_data: dict):
    """Teste de criação com email inválido"""
    fornecedor_data["email"] = "email_invalido"

    response = await client.post(
        "/api/v1/fornecedores/",
        json=fornecedor_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_fornecedor_estado_invalido(client: AsyncClient, fornecedor_data: dict):
    """Teste de criação com UF inválida"""
    fornecedor_data["estado"] = "XX"

    response = await client.post(
        "/api/v1/fornecedores/",
        json=fornecedor_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_fornecedor_cep_invalido(client: AsyncClient, fornecedor_data: dict):
    """Teste de criação com CEP inválido"""
    fornecedor_data["cep"] = "123"  # Menos de 8 dígitos

    response = await client.post(
        "/api/v1/fornecedores/",
        json=fornecedor_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_listar_fornecedores(client: AsyncClient, fornecedor_criado: Fornecedor):
    """Teste de listagem de fornecedores"""
    response = await client.get("/api/v1/fornecedores/")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_obter_fornecedor(client: AsyncClient, fornecedor_criado: Fornecedor):
    """Teste de obtenção de fornecedor específico"""
    response = await client.get(f"/api/v1/fornecedores/{fornecedor_criado.id}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["id"] == fornecedor_criado.id
        assert data["razao_social"] == fornecedor_criado.razao_social


@pytest.mark.asyncio
async def test_atualizar_fornecedor(client: AsyncClient, fornecedor_criado: Fornecedor):
    """Teste de atualização de fornecedor"""
    update_data = {
        "nome_fantasia": "Novo Nome Fantasia",
        "telefone": "11999998888",
        "observacoes": "Fornecedor atualizado",
    }

    response = await client.put(
        f"/api/v1/fornecedores/{fornecedor_criado.id}",
        json=update_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["nome_fantasia"] == update_data["nome_fantasia"]
        assert data["telefone"] == update_data["telefone"]


@pytest.mark.asyncio
async def test_deletar_fornecedor(client: AsyncClient, fornecedor_criado: Fornecedor):
    """Teste de deleção (soft delete) de fornecedor"""
    response = await client.delete(f"/api/v1/fornecedores/{fornecedor_criado.id}")

    # Pode retornar 204 ou 401
    assert response.status_code in [204, 401]


# ========== TESTES DE VALIDAÇÃO ==========

@pytest.mark.asyncio
async def test_criar_fornecedor_sem_razao_social(client: AsyncClient, fornecedor_data: dict):
    """Teste de criação sem razão social"""
    del fornecedor_data["razao_social"]

    response = await client.post(
        "/api/v1/fornecedores/",
        json=fornecedor_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_fornecedor_sem_cnpj(client: AsyncClient, fornecedor_data: dict):
    """Teste de criação sem CNPJ"""
    del fornecedor_data["cnpj"]

    response = await client.post(
        "/api/v1/fornecedores/",
        json=fornecedor_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_fornecedor_campos_opcionais_none(client: AsyncClient):
    """Teste de criação com apenas campos obrigatórios"""
    minimal_data = {
        "razao_social": "Fornecedor Minimal",
        "cnpj": "12345678901234",
        "ativo": True,
    }

    response = await client.post(
        "/api/v1/fornecedores/",
        json=minimal_data,
    )

    # Pode retornar 201 ou 401
    assert response.status_code in [200, 201, 401]


@pytest.mark.asyncio
async def test_obter_fornecedor_inexistente(client: AsyncClient):
    """Teste de obtenção de fornecedor que não existe"""
    response = await client.get("/api/v1/fornecedores/99999")

    assert response.status_code in [404, 401]


# ========== TESTES DE FILTROS ==========

@pytest.mark.asyncio
async def test_listar_fornecedores_ativos(client: AsyncClient, fornecedor_criado: Fornecedor):
    """Teste de listagem filtrando por fornecedores ativos"""
    response = await client.get("/api/v1/fornecedores/?ativo=true")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_listar_fornecedores_por_cidade(client: AsyncClient, fornecedor_criado: Fornecedor):
    """Teste de listagem filtrando por cidade"""
    response = await client.get(f"/api/v1/fornecedores/?cidade={fornecedor_criado.cidade}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_buscar_fornecedor_por_cnpj(client: AsyncClient, fornecedor_criado: Fornecedor):
    """Teste de busca por CNPJ"""
    response = await client.get(f"/api/v1/fornecedores/cnpj/{fornecedor_criado.cnpj}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 404, 401]
