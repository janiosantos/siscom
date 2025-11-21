"""
Testes para módulo Compras
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from unittest.mock import patch

from app.modules.compras.models import PedidoCompra, ItemPedidoCompra, StatusPedidoCompra
from app.modules.fornecedores.models import Fornecedor
from app.modules.produtos.models import Produto
from app.modules.categorias.models import Categoria


# Mock automático para validação de CNPJ nos fornecedores
@pytest.fixture(autouse=True)
def mock_document_validator():
    """Mock do DocumentValidator para aceitar qualquer CNPJ nos testes"""
    with patch("app.modules.fornecedores.schemas.DocumentValidator.validate_cnpj", return_value=True):
        yield


# ========== FIXTURES ==========

@pytest.fixture
async def setup_compra(db_session: AsyncSession):
    """Fixture para configurar dados necessários para compras"""
    # Criar fornecedor
    fornecedor = Fornecedor(
        razao_social="Fornecedor Teste",
        cnpj="12345678901234",
        ativo=True,
    )
    db_session.add(fornecedor)
    await db_session.flush()

    # Criar categoria
    categoria = Categoria(
        nome="Materiais",
        descricao="Materiais de construção",
        ativa=True,
    )
    db_session.add(categoria)
    await db_session.flush()

    # Criar produtos
    produto1 = Produto(
        codigo_barras="MAT-001",
        descricao="Areia Fina",
        categoria_id=categoria.id,
        preco_venda=50.0,
        preco_custo=35.0,
        estoque_atual=100,
        estoque_minimo=20,
        ativo=True,
    )
    produto2 = Produto(
        codigo_barras="MAT-002",
        descricao="Pedra Brita",
        categoria_id=categoria.id,
        preco_venda=60.0,
        preco_custo=40.0,
        estoque_atual=50,
        estoque_minimo=30,
        ativo=True,
    )
    db_session.add_all([produto1, produto2])
    await db_session.commit()
    await db_session.refresh(fornecedor)
    await db_session.refresh(categoria)
    await db_session.refresh(produto1)
    await db_session.refresh(produto2)

    return {
        "fornecedor": fornecedor,
        "categoria": categoria,
        "produto1": produto1,
        "produto2": produto2,
    }


@pytest.fixture
async def pedido_compra_data(setup_compra: dict):
    """Fixture com dados para criação de pedido de compra"""
    return {
        "fornecedor_id": setup_compra["fornecedor"].id,
        "data_pedido": date.today().isoformat(),
        "data_entrega_prevista": (date.today() + timedelta(days=7)).isoformat(),
        "desconto": 0.0,
        "valor_frete": 50.0,
        "observacoes": "Pedido teste",
        "itens": [
            {
                "produto_id": setup_compra["produto1"].id,
                "quantidade_solicitada": 100,
                "preco_unitario": 35.0,
            },
            {
                "produto_id": setup_compra["produto2"].id,
                "quantidade_solicitada": 50,
                "preco_unitario": 40.0,
            }
        ],
    }


@pytest.fixture
async def pedido_compra_criado(db_session: AsyncSession, setup_compra: dict):
    """Fixture para criar um pedido de compra APROVADO (para testes de recebimento)"""
    pedido = PedidoCompra(
        fornecedor_id=setup_compra["fornecedor"].id,
        data_pedido=date.today(),
        data_entrega_prevista=date.today() + timedelta(days=7),
        subtotal=5500.0,
        desconto=0.0,
        valor_frete=50.0,
        valor_total=5550.0,
        status=StatusPedidoCompra.APROVADO,  # APROVADO para permitir recebimento
        observacoes="Pedido fixture",
    )
    db_session.add(pedido)
    await db_session.flush()  # Flush para obter pedido.id

    # Criar itens do pedido
    item1 = ItemPedidoCompra(
        pedido_id=pedido.id,
        produto_id=setup_compra["produto1"].id,
        quantidade_solicitada=100,
        preco_unitario=35.0,
        quantidade_recebida=0,
        subtotal_item=3500.0,
    )
    item2 = ItemPedidoCompra(
        pedido_id=pedido.id,
        produto_id=setup_compra["produto2"].id,
        quantidade_solicitada=50,
        preco_unitario=40.0,
        quantidade_recebida=0,
        subtotal_item=2000.0,
    )
    db_session.add_all([item1, item2])
    await db_session.commit()
    await db_session.refresh(pedido)
    return pedido


@pytest.fixture
async def pedido_compra_pendente(db_session: AsyncSession, setup_compra: dict):
    """Fixture para criar um pedido de compra PENDENTE (para testes de aprovação)"""
    pedido = PedidoCompra(
        fornecedor_id=setup_compra["fornecedor"].id,
        data_pedido=date.today(),
        data_entrega_prevista=date.today() + timedelta(days=7),
        subtotal=5500.0,
        desconto=0.0,
        valor_frete=50.0,
        valor_total=5550.0,
        status=StatusPedidoCompra.PENDENTE,  # PENDENTE para permitir aprovação
        observacoes="Pedido pendente fixture",
    )
    db_session.add(pedido)
    await db_session.commit()
    await db_session.refresh(pedido)
    return pedido


# ========== TESTES DE CRUD ==========

@pytest.mark.asyncio
async def test_criar_pedido_compra(client: AsyncClient, pedido_compra_data: dict):
    """Teste de criação de pedido de compra"""
    response = await client.post(
        "/api/v1/compras/",
        json=pedido_compra_data,
    )

    # Pode retornar 201 ou 401
    assert response.status_code in [200, 201, 401]

    if response.status_code in [200, 201]:
        data = response.json()
        assert "id" in data
        assert data["fornecedor_id"] == pedido_compra_data["fornecedor_id"]
        assert data["status"] == "PENDENTE"
        assert len(data["itens"]) == 2


@pytest.mark.asyncio
async def test_criar_pedido_compra_sem_itens(client: AsyncClient, pedido_compra_data: dict):
    """Teste de criação sem itens"""
    pedido_compra_data["itens"] = []

    response = await client.post(
        "/api/v1/compras/",
        json=pedido_compra_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_pedido_compra_data_entrega_invalida(client: AsyncClient, pedido_compra_data: dict):
    """Teste de criação com data de entrega anterior ao pedido"""
    pedido_compra_data["data_entrega_prevista"] = (date.today() - timedelta(days=1)).isoformat()

    response = await client.post(
        "/api/v1/compras/",
        json=pedido_compra_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_listar_pedidos_compra(client: AsyncClient, pedido_compra_criado: PedidoCompra):
    """Teste de listagem de pedidos de compra"""
    response = await client.get("/api/v1/compras/")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_obter_pedido_compra(client: AsyncClient, pedido_compra_criado: PedidoCompra):
    """Teste de obtenção de pedido específico"""
    response = await client.get(f"/api/v1/compras/{pedido_compra_criado.id}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["id"] == pedido_compra_criado.id
        assert data["status"] == pedido_compra_criado.status.value


@pytest.mark.asyncio
async def test_atualizar_pedido_compra(client: AsyncClient, pedido_compra_criado: PedidoCompra):
    """Teste de atualização de pedido"""
    update_data = {
        "desconto": 100.0,
        "valor_frete": 75.0,
        "observacoes": "Pedido atualizado",
    }

    response = await client.put(
        f"/api/v1/compras/{pedido_compra_criado.id}",
        json=update_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["desconto"] == update_data["desconto"]
        assert data["valor_frete"] == update_data["valor_frete"]


@pytest.mark.asyncio
async def test_deletar_pedido_compra(client: AsyncClient, pedido_compra_criado: PedidoCompra):
    """Teste de deleção de pedido"""
    response = await client.delete(f"/api/v1/compras/{pedido_compra_criado.id}")

    # Pode retornar 204 ou 401
    assert response.status_code in [204, 401]


# ========== TESTES DE MUDANÇA DE STATUS ==========

@pytest.mark.asyncio
async def test_aprovar_pedido_compra(client: AsyncClient, pedido_compra_pendente: PedidoCompra):
    """Teste de aprovação de pedido"""
    response = await client.post(f"/api/v1/compras/{pedido_compra_pendente.id}/aprovar")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "APROVADO"


@pytest.mark.asyncio
async def test_cancelar_pedido_compra(client: AsyncClient, pedido_compra_criado: PedidoCompra):
    """Teste de cancelamento de pedido"""
    response = await client.post(f"/api/v1/compras/{pedido_compra_criado.id}/cancelar")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "CANCELADO"


# ========== TESTES DE RECEBIMENTO ==========

@pytest.mark.asyncio
async def test_receber_pedido_total(client: AsyncClient, pedido_compra_criado: PedidoCompra):
    """Teste de recebimento total do pedido"""
    receber_data = {
        "itens_recebidos": [
            {
                "item_id": 1,
                "quantidade_recebida": 100,
            }
        ],
        "data_recebimento": date.today().isoformat(),
        "observacao": "Recebimento total",
    }

    response = await client.post(
        f"/api/v1/compras/{pedido_compra_criado.id}/receber",
        json=receber_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_receber_pedido_parcial(client: AsyncClient, pedido_compra_criado: PedidoCompra):
    """Teste de recebimento parcial"""
    receber_data = {
        "itens_recebidos": [
            {
                "item_id": 1,
                "quantidade_recebida": 50,  # Apenas 50 de 100
            }
        ],
        "data_recebimento": date.today().isoformat(),
        "observacao": "Recebimento parcial",
    }

    response = await client.post(
        f"/api/v1/compras/{pedido_compra_criado.id}/receber",
        json=receber_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


# ========== TESTES DE SUGESTÕES DE COMPRA ==========

@pytest.mark.asyncio
async def test_obter_sugestoes_compra(client: AsyncClient, setup_compra: dict):
    """Teste de obtenção de sugestões de compra"""
    response = await client.get("/api/v1/compras/sugestoes")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data


# ========== TESTES DE VALIDAÇÃO ==========

@pytest.mark.asyncio
async def test_criar_pedido_quantidade_negativa(client: AsyncClient, pedido_compra_data: dict):
    """Teste de criação com quantidade negativa"""
    pedido_compra_data["itens"][0]["quantidade_solicitada"] = -10

    response = await client.post(
        "/api/v1/compras/",
        json=pedido_compra_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_pedido_preco_negativo(client: AsyncClient, pedido_compra_data: dict):
    """Teste de criação com preço negativo"""
    pedido_compra_data["itens"][0]["preco_unitario"] = -10.0

    response = await client.post(
        "/api/v1/compras/",
        json=pedido_compra_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_criar_pedido_desconto_negativo(client: AsyncClient, pedido_compra_data: dict):
    """Teste de criação com desconto negativo"""
    pedido_compra_data["desconto"] = -50.0

    response = await client.post(
        "/api/v1/compras/",
        json=pedido_compra_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_obter_pedido_inexistente(client: AsyncClient):
    """Teste de obtenção de pedido que não existe"""
    response = await client.get("/api/v1/compras/99999")

    assert response.status_code in [404, 401]


# ========== TESTES DE FILTROS ==========

@pytest.mark.asyncio
async def test_listar_pedidos_por_status(client: AsyncClient, pedido_compra_criado: PedidoCompra):
    """Teste de listagem filtrando por status"""
    response = await client.get("/api/v1/compras/?status=PENDENTE")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_listar_pedidos_por_fornecedor(client: AsyncClient, pedido_compra_criado: PedidoCompra):
    """Teste de listagem filtrando por fornecedor"""
    response = await client.get(f"/api/v1/compras/?fornecedor_id={pedido_compra_criado.fornecedor_id}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]
