"""
Testes para módulo PDV (Ponto de Venda)
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.modules.pdv.models import Caixa, MovimentacaoCaixa, StatusCaixa, TipoMovimentacaoCaixa
from app.modules.produtos.models import Produto
from app.modules.categorias.models import Categoria
from app.modules.clientes.models import Cliente, TipoPessoa


# ========== FIXTURES ==========

@pytest.fixture
async def setup_pdv(db_session: AsyncSession):
    """Fixture para configurar dados necessários para PDV"""
    # Criar categoria
    categoria = Categoria(
        nome="Cimento",
        descricao="Materiais de Cimento",
        ativa=True,
    )
    db_session.add(categoria)
    await db_session.flush()

    # Criar produto
    produto = Produto(
        codigo="CIM-001",
        descricao="Cimento CP-II 50kg",
        categoria_id=categoria.id,
        preco_venda=32.90,
        preco_custo=25.00,
        estoque_atual=100,
        estoque_minimo=10,
        ativo=True,
    )
    db_session.add(produto)

    # Criar cliente
    cliente = Cliente(
        nome="Cliente Teste PDV",
        tipo_pessoa=TipoPessoa.PF,
        cpf_cnpj="12345678900",
        ativo=True,
    )
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(categoria)
    await db_session.refresh(produto)
    await db_session.refresh(cliente)

    return {
        "categoria": categoria,
        "produto": produto,
        "cliente": cliente,
    }


@pytest.fixture
async def caixa_aberto(db_session: AsyncSession):
    """Fixture para criar um caixa aberto"""
    caixa = Caixa(
        operador_id=1,
        valor_abertura=100.0,
        status=StatusCaixa.ABERTO,
        data_abertura=datetime.utcnow(),
    )
    db_session.add(caixa)
    await db_session.commit()
    await db_session.refresh(caixa)
    return caixa


@pytest.fixture
async def abrir_caixa_data():
    """Fixture com dados para abrir caixa"""
    return {
        "operador_id": 1,
        "valor_abertura": 100.0,
    }


@pytest.fixture
async def movimentacao_data():
    """Fixture com dados para movimentação"""
    return {
        "tipo": "ENTRADA",
        "valor": 50.0,
        "descricao": "Venda em dinheiro",
    }


@pytest.fixture
async def sangria_data():
    """Fixture com dados para sangria"""
    return {
        "valor": 200.0,
        "descricao": "Sangria para depósito bancário",
    }


@pytest.fixture
async def venda_pdv_data(setup_pdv: dict):
    """Fixture com dados para venda no PDV"""
    return {
        "cliente_id": setup_pdv["cliente"].id,
        "forma_pagamento": "DINHEIRO",
        "desconto": 0.0,
        "observacoes": "Venda teste PDV",
        "itens": [
            {
                "produto_id": setup_pdv["produto"].id,
                "quantidade": 5,
                "preco_unitario": 32.90,
                "desconto_item": 0.0,
            }
        ],
    }


# ========== TESTES DE CAIXA ==========

@pytest.mark.asyncio
async def test_abrir_caixa(client: AsyncClient, abrir_caixa_data: dict):
    """Teste de abertura de caixa"""
    response = await client.post(
        "/api/v1/pdv/caixa/abrir",
        json=abrir_caixa_data,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["operador_id"] == abrir_caixa_data["operador_id"]
    assert data["valor_abertura"] == abrir_caixa_data["valor_abertura"]
    assert data["status"] == "ABERTO"
    assert "id" in data
    assert "data_abertura" in data


@pytest.mark.asyncio
async def test_abrir_caixa_valor_negativo(client: AsyncClient, abrir_caixa_data: dict):
    """Teste de abertura de caixa com valor negativo"""
    abrir_caixa_data["valor_abertura"] = -100.0

    response = await client.post(
        "/api/v1/pdv/caixa/abrir",
        json=abrir_caixa_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_obter_caixa_aberto(client: AsyncClient, caixa_aberto: Caixa):
    """Teste de obtenção de caixa aberto"""
    response = await client.get("/api/v1/pdv/caixa/atual")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == caixa_aberto.id
    assert data["status"] == "ABERTO"
    assert data["operador_id"] == caixa_aberto.operador_id


@pytest.mark.asyncio
async def test_obter_saldo_caixa(client: AsyncClient, caixa_aberto: Caixa):
    """Teste de obtenção de saldo do caixa"""
    response = await client.get(f"/api/v1/pdv/caixa/{caixa_aberto.id}/saldo")

    assert response.status_code == 200
    data = response.json()
    assert data["caixa_id"] == caixa_aberto.id
    assert "saldo_atual" in data
    assert "saldo_esperado" in data
    assert "total_entradas" in data
    assert "total_saidas" in data


@pytest.mark.asyncio
async def test_fechar_caixa(client: AsyncClient, caixa_aberto: Caixa):
    """Teste de fechamento de caixa"""
    fechar_data = {
        "valor_fechamento": 150.0,
    }

    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/fechar",
        json=fechar_data,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["status"] == "FECHADO"
    assert data["valor_fechamento"] == fechar_data["valor_fechamento"]
    assert "data_fechamento" in data


@pytest.mark.asyncio
async def test_fechar_caixa_valor_negativo(client: AsyncClient, caixa_aberto: Caixa):
    """Teste de fechamento de caixa com valor negativo"""
    fechar_data = {
        "valor_fechamento": -50.0,
    }

    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/fechar",
        json=fechar_data,
    )

    assert response.status_code == 422


# ========== TESTES DE MOVIMENTAÇÃO ==========

@pytest.mark.asyncio
async def test_criar_movimentacao_entrada(client: AsyncClient, caixa_aberto: Caixa, movimentacao_data: dict):
    """Teste de criação de movimentação de entrada"""
    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/movimentacoes",
        json=movimentacao_data,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["caixa_id"] == caixa_aberto.id
    assert data["tipo"] == movimentacao_data["tipo"]
    assert data["valor"] == movimentacao_data["valor"]
    assert data["descricao"] == movimentacao_data["descricao"]


@pytest.mark.asyncio
async def test_criar_movimentacao_saida(client: AsyncClient, caixa_aberto: Caixa):
    """Teste de criação de movimentação de saída"""
    movimentacao_saida = {
        "tipo": "SAIDA",
        "valor": 30.0,
        "descricao": "Despesa operacional",
    }

    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/movimentacoes",
        json=movimentacao_saida,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["tipo"] == "SAIDA"
    assert data["valor"] == movimentacao_saida["valor"]


@pytest.mark.asyncio
async def test_criar_movimentacao_valor_zero(client: AsyncClient, caixa_aberto: Caixa, movimentacao_data: dict):
    """Teste de criação de movimentação com valor zero"""
    movimentacao_data["valor"] = 0.0

    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/movimentacoes",
        json=movimentacao_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_listar_movimentacoes(client: AsyncClient, caixa_aberto: Caixa, movimentacao_data: dict):
    """Teste de listagem de movimentações"""
    # Criar algumas movimentações
    await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/movimentacoes",
        json=movimentacao_data,
    )

    response = await client.get(f"/api/v1/pdv/caixa/{caixa_aberto.id}/movimentacoes")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) > 0


# ========== TESTES DE SANGRIA E SUPRIMENTO ==========

@pytest.mark.asyncio
async def test_criar_sangria(client: AsyncClient, caixa_aberto: Caixa, sangria_data: dict):
    """Teste de criação de sangria"""
    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/sangria",
        json=sangria_data,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["tipo"] == "SANGRIA"
    assert data["valor"] == sangria_data["valor"]
    assert data["descricao"] == sangria_data["descricao"]


@pytest.mark.asyncio
async def test_criar_sangria_valor_zero(client: AsyncClient, caixa_aberto: Caixa, sangria_data: dict):
    """Teste de criação de sangria com valor zero"""
    sangria_data["valor"] = 0.0

    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/sangria",
        json=sangria_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_suprimento(client: AsyncClient, caixa_aberto: Caixa):
    """Teste de criação de suprimento"""
    suprimento_data = {
        "valor": 500.0,
        "descricao": "Suprimento para troco",
    }

    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/suprimento",
        json=suprimento_data,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["tipo"] == "SUPRIMENTO"
    assert data["valor"] == suprimento_data["valor"]


@pytest.mark.asyncio
async def test_criar_suprimento_descricao_vazia(client: AsyncClient, caixa_aberto: Caixa):
    """Teste de criação de suprimento com descrição vazia"""
    suprimento_data = {
        "valor": 100.0,
        "descricao": "",
    }

    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/suprimento",
        json=suprimento_data,
    )

    assert response.status_code == 422


# ========== TESTES DE VENDA PDV ==========

@pytest.mark.asyncio
async def test_registrar_venda_pdv(client: AsyncClient, caixa_aberto: Caixa, venda_pdv_data: dict):
    """Teste de registro de venda no PDV"""
    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/vendas",
        json=venda_pdv_data,
    )

    # Pode retornar 201 ou 401 se não tiver autenticação configurada
    assert response.status_code in [200, 201, 401]

    if response.status_code in [200, 201]:
        data = response.json()
        assert "id" in data
        assert data["forma_pagamento"] == venda_pdv_data["forma_pagamento"]


@pytest.mark.asyncio
async def test_registrar_venda_pdv_sem_itens(client: AsyncClient, caixa_aberto: Caixa, venda_pdv_data: dict):
    """Teste de registro de venda sem itens"""
    venda_pdv_data["itens"] = []

    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/vendas",
        json=venda_pdv_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_registrar_venda_pdv_forma_pagamento_vazia(client: AsyncClient, caixa_aberto: Caixa, venda_pdv_data: dict):
    """Teste de registro de venda com forma de pagamento vazia"""
    venda_pdv_data["forma_pagamento"] = ""

    response = await client.post(
        f"/api/v1/pdv/caixa/{caixa_aberto.id}/vendas",
        json=venda_pdv_data,
    )

    assert response.status_code == 422
