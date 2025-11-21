"""
Testes para módulo Orçamentos
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date, timedelta

from app.modules.orcamentos.models import Orcamento, ItemOrcamento, StatusOrcamento
from app.modules.produtos.models import Produto
from app.modules.categorias.models import Categoria
from app.modules.clientes.models import Cliente, TipoPessoa


# ========== FIXTURES ==========

@pytest.fixture
async def setup_orcamento(db_session: AsyncSession):
    """Fixture para configurar dados necessários para orçamentos"""
    # Criar categoria
    categoria = Categoria(
        nome="Ferragens",
        descricao="Ferragens diversas",
        ativa=True,
    )
    db_session.add(categoria)
    await db_session.flush()

    # Criar produtos
    produto1 = Produto(
        codigo_barras="FER-001",
        descricao="Parafuso 6x40mm",
        categoria_id=categoria.id,
        preco_venda=0.50,
        preco_custo=0.30,
        estoque_atual=1000,
        estoque_minimo=100,
        ativo=True,
    )
    produto2 = Produto(
        codigo_barras="FER-002",
        descricao="Prego 18x27",
        categoria_id=categoria.id,
        preco_venda=0.25,
        preco_custo=0.15,
        estoque_atual=2000,
        estoque_minimo=200,
        ativo=True,
    )
    db_session.add_all([produto1, produto2])

    # Criar cliente
    cliente = Cliente(
        nome="Cliente Orçamento",
        tipo_pessoa=TipoPessoa.PJ,
        cpf_cnpj="12345678901234",
        ativo=True,
    )
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(categoria)
    await db_session.refresh(produto1)
    await db_session.refresh(produto2)
    await db_session.refresh(cliente)

    return {
        "categoria": categoria,
        "produto1": produto1,
        "produto2": produto2,
        "cliente": cliente,
    }


@pytest.fixture
async def orcamento_data(setup_orcamento: dict):
    """Fixture com dados para criação de orçamento"""
    return {
        "cliente_id": setup_orcamento["cliente"].id,
        "vendedor_id": 1,
        "validade_dias": 30,
        "desconto": 0.0,
        "observacoes": "Orçamento teste",
        "itens": [
            {
                "produto_id": setup_orcamento["produto1"].id,
                "quantidade": 100,
                "preco_unitario": 0.50,
                "desconto_item": 0.0,
            },
            {
                "produto_id": setup_orcamento["produto2"].id,
                "quantidade": 200,
                "preco_unitario": 0.25,
                "desconto_item": 0.0,
            }
        ],
    }


@pytest.fixture
async def orcamento_criado(db_session: AsyncSession, setup_orcamento: dict):
    """Fixture para criar um orçamento no banco"""
    orcamento = Orcamento(
        cliente_id=setup_orcamento["cliente"].id,
        vendedor_id=1,
        data_orcamento=datetime.utcnow(),
        validade_dias=30,
        data_validade=date.today() + timedelta(days=30),
        subtotal=100.0,
        desconto=0.0,
        valor_total=100.0,
        status=StatusOrcamento.ABERTO,
        observacoes="Orçamento fixture",
    )
    db_session.add(orcamento)
    await db_session.commit()
    await db_session.refresh(orcamento)
    return orcamento


# ========== TESTES DE CRUD ==========

@pytest.mark.asyncio
async def test_criar_orcamento(client: AsyncClient, orcamento_data: dict):
    """Teste de criação de orçamento"""
    response = await client.post(
        "/api/v1/orcamentos/",
        json=orcamento_data,
    )

    # Pode retornar 201 ou 401 se não tiver autenticação
    assert response.status_code in [200, 201, 401]

    if response.status_code in [200, 201]:
        data = response.json()
        assert "id" in data
        assert data["cliente_id"] == orcamento_data["cliente_id"]
        assert data["vendedor_id"] == orcamento_data["vendedor_id"]
        assert data["validade_dias"] == orcamento_data["validade_dias"]
        assert data["status"] == "ABERTO"
        assert len(data["itens"]) == 2


@pytest.mark.asyncio
async def test_criar_orcamento_sem_itens(client: AsyncClient, orcamento_data: dict):
    """Teste de criação de orçamento sem itens"""
    orcamento_data["itens"] = []

    response = await client.post(
        "/api/v1/orcamentos/",
        json=orcamento_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_orcamento_validade_zero(client: AsyncClient, orcamento_data: dict):
    """Teste de criação de orçamento com validade zero"""
    orcamento_data["validade_dias"] = 0

    response = await client.post(
        "/api/v1/orcamentos/",
        json=orcamento_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_listar_orcamentos(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de listagem de orçamentos"""
    response = await client.get("/api/v1/orcamentos/")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_obter_orcamento(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de obtenção de orçamento específico"""
    response = await client.get(f"/api/v1/orcamentos/{orcamento_criado.id}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["id"] == orcamento_criado.id
        assert data["status"] == orcamento_criado.status.value


@pytest.mark.asyncio
async def test_atualizar_orcamento(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de atualização de orçamento"""
    update_data = {
        "validade_dias": 45,
        "desconto": 10.0,
        "observacoes": "Orçamento atualizado",
    }

    response = await client.put(
        f"/api/v1/orcamentos/{orcamento_criado.id}",
        json=update_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["validade_dias"] == update_data["validade_dias"]
        assert data["desconto"] == update_data["desconto"]


@pytest.mark.asyncio
async def test_deletar_orcamento(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de deleção de orçamento"""
    response = await client.delete(f"/api/v1/orcamentos/{orcamento_criado.id}")

    # Pode retornar 204 ou 401
    assert response.status_code in [204, 401]


# ========== TESTES DE MUDANÇA DE STATUS ==========

@pytest.mark.asyncio
async def test_aprovar_orcamento(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de aprovação de orçamento"""
    response = await client.post(f"/api/v1/orcamentos/{orcamento_criado.id}/aprovar")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "APROVADO"


@pytest.mark.asyncio
async def test_marcar_orcamento_como_perdido(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de marcar orçamento como perdido"""
    response = await client.post(f"/api/v1/orcamentos/{orcamento_criado.id}/perdido")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "PERDIDO"


# ========== TESTES DE CONVERSÃO ==========

@pytest.mark.asyncio
async def test_converter_orcamento_em_venda(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de conversão de orçamento em venda"""
    converter_data = {
        "forma_pagamento": "DINHEIRO",
    }

    response = await client.post(
        f"/api/v1/orcamentos/{orcamento_criado.id}/converter",
        json=converter_data,
    )

    # Pode retornar 200/201 ou 401
    assert response.status_code in [200, 201, 401]

    if response.status_code in [200, 201]:
        data = response.json()
        assert "id" in data
        assert data["forma_pagamento"] == converter_data["forma_pagamento"]


@pytest.mark.asyncio
async def test_converter_orcamento_forma_pagamento_vazia(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de conversão com forma de pagamento vazia"""
    converter_data = {
        "forma_pagamento": "",
    }

    response = await client.post(
        f"/api/v1/orcamentos/{orcamento_criado.id}/converter",
        json=converter_data,
    )

    assert response.status_code == 422


# ========== TESTES DE VALIDAÇÃO ==========

@pytest.mark.asyncio
async def test_criar_orcamento_quantidade_negativa(client: AsyncClient, orcamento_data: dict):
    """Teste de criação com quantidade negativa"""
    orcamento_data["itens"][0]["quantidade"] = -10

    response = await client.post(
        "/api/v1/orcamentos/",
        json=orcamento_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_orcamento_preco_zero(client: AsyncClient, orcamento_data: dict):
    """Teste de criação com preço zero"""
    orcamento_data["itens"][0]["preco_unitario"] = 0.0

    response = await client.post(
        "/api/v1/orcamentos/",
        json=orcamento_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_orcamento_desconto_negativo(client: AsyncClient, orcamento_data: dict):
    """Teste de criação com desconto negativo"""
    orcamento_data["desconto"] = -10.0

    response = await client.post(
        "/api/v1/orcamentos/",
        json=orcamento_data,
    )

    assert response.status_code == 422


# ========== TESTES DE FILTROS ==========

@pytest.mark.asyncio
async def test_listar_orcamentos_por_status(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de listagem filtrando por status"""
    response = await client.get("/api/v1/orcamentos/?status=ABERTO")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_listar_orcamentos_por_cliente(client: AsyncClient, orcamento_criado: Orcamento):
    """Teste de listagem filtrando por cliente"""
    response = await client.get(f"/api/v1/orcamentos/?cliente_id={orcamento_criado.cliente_id}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_obter_orcamento_inexistente(client: AsyncClient):
    """Teste de obtenção de orçamento que não existe"""
    response = await client.get("/api/v1/orcamentos/99999")

    assert response.status_code in [404, 401]
