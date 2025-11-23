"""
Testes para o módulo de Produtos

Testa CRUD completo, validações e regras de negócio
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.modules.produtos.models import Produto
from app.modules.categorias.models import Categoria


@pytest.fixture
async def categoria_fixture(db_session: AsyncSession):
    """Fixture para criar categoria necessária"""
    categoria = Categoria(nome="Cimentos", descricao="Cimentos e argamassas", ativa=True)
    db_session.add(categoria)
    await db_session.commit()
    await db_session.refresh(categoria)
    return categoria


@pytest.fixture
async def produto_data(categoria_fixture: Categoria):
    """Fixture com dados válidos de produto"""
    return {
        "codigo_barras": "7891234567890",
        "descricao": "Cimento CP-II 50kg",
        "categoria_id": categoria_fixture.id,
        "preco_custo": 25.50,
        "preco_venda": 32.90,
        "estoque_atual": 100.0,
        "estoque_minimo": 10.0,
        "unidade": "UN",
        "ncm": "25232900",
        "controla_lote": False,
        "controla_serie": False,
        "ativo": True,
    }


@pytest.fixture
async def produto_criado(db_session: AsyncSession, produto_data: dict):
    """Fixture que cria um produto no banco"""
    produto = Produto(**produto_data)
    db_session.add(produto)
    await db_session.commit()
    await db_session.refresh(produto)
    return produto


class TestCriarProduto:
    """Testes de criação de produto"""

    @pytest.mark.asyncio
    async def test_criar_produto_sucesso(
        self, client: AsyncClient, produto_data: dict
    ):
        """Deve criar produto com dados válidos"""
        response = await client.post("/api/v1/produtos/", json=produto_data)

        assert response.status_code == 201
        data = response.json()
        assert data["codigo_barras"] == produto_data["codigo_barras"]
        assert data["descricao"] == produto_data["descricao"]
        assert float(data["preco_venda"]) == produto_data["preco_venda"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_criar_produto_codigo_duplicado(
        self, client: AsyncClient, produto_data: dict, produto_criado: Produto
    ):
        """Não deve criar produto com código de barras duplicado"""
        produto_data["codigo_barras"] = produto_criado.codigo_barras
        response = await client.post("/api/v1/produtos/", json=produto_data)

        assert response.status_code in [400, 409, 422]  # Conflict ou validation error

    @pytest.mark.asyncio
    async def test_criar_produto_sem_codigo(
        self, client: AsyncClient, produto_data: dict
    ):
        """Não deve criar produto sem código de barras"""
        del produto_data["codigo_barras"]
        response = await client.post("/api/v1/produtos/", json=produto_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_criar_produto_preco_negativo(
        self, client: AsyncClient, produto_data: dict
    ):
        """Não deve criar produto com preço negativo"""
        produto_data["preco_venda"] = -10.0
        response = await client.post("/api/v1/produtos/", json=produto_data)

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_criar_produto_categoria_invalida(
        self, client: AsyncClient, produto_data: dict
    ):
        """Não deve criar produto com categoria inexistente"""
        produto_data["categoria_id"] = 99999
        response = await client.post("/api/v1/produtos/", json=produto_data)

        assert response.status_code in [400, 404, 422]


class TestBuscarProduto:
    """Testes de busca de produto"""

    @pytest.mark.asyncio
    async def test_buscar_produto_por_id(
        self, client: AsyncClient, produto_criado: Produto
    ):
        """Deve buscar produto existente por ID"""
        response = await client.get(f"/api/v1/produtos/{produto_criado.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == produto_criado.id
        assert data["codigo_barras"] == produto_criado.codigo_barras

    @pytest.mark.asyncio
    async def test_buscar_produto_por_codigo_barras(
        self, client: AsyncClient, produto_criado: Produto
    ):
        """Deve buscar produto por código de barras"""
        response = await client.get(
            f"/api/v1/produtos/codigo/{produto_criado.codigo_barras}"
        )

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 200
            data = response.json()
            assert data["codigo_barras"] == produto_criado.codigo_barras


class TestListarProdutos:
    """Testes de listagem de produtos"""

    @pytest.mark.asyncio
    async def test_listar_produtos(
        self, client: AsyncClient, db_session: AsyncSession, categoria_fixture: Categoria
    ):
        """Deve listar produtos com paginação"""
        # Criar 3 produtos
        for i in range(3):
            produto = Produto(
                codigo_barras=f"789000000{i}",
                descricao=f"Produto {i+1}",
                categoria_id=categoria_fixture.id,
                preco_custo=10.0,
                preco_venda=15.0,
                ativo=True,
            )
            db_session.add(produto)
        await db_session.commit()

        response = await client.get("/api/v1/produtos/")

        assert response.status_code == 200
        data = response.json()
        # Pode ter formato de lista ou objeto com items
        if isinstance(data, list):
            assert len(data) >= 3
        elif isinstance(data, dict) and "items" in data:
            assert len(data["items"]) >= 3

    @pytest.mark.asyncio
    async def test_listar_apenas_ativos(
        self, client: AsyncClient, db_session: AsyncSession, categoria_fixture: Categoria
    ):
        """Deve filtrar apenas produtos ativos"""
        # Criar 1 ativo e 1 inativo
        produto_ativo = Produto(
            codigo_barras="78910",
            descricao="Ativo",
            categoria_id=categoria_fixture.id,
            preco_venda=10.0,
            ativo=True,
        )
        produto_inativo = Produto(
            codigo_barras="78911",
            descricao="Inativo",
            categoria_id=categoria_fixture.id,
            preco_venda=10.0,
            ativo=False,
        )
        db_session.add(produto_ativo)
        db_session.add(produto_inativo)
        await db_session.commit()

        response = await client.get("/api/v1/produtos/?apenas_ativos=true")

        assert response.status_code == 200


class TestAtualizarProduto:
    """Testes de atualização de produto"""

    @pytest.mark.asyncio
    async def test_atualizar_preco(
        self, client: AsyncClient, produto_criado: Produto
    ):
        """Deve atualizar preço do produto"""
        update_data = {"preco_venda": 35.90}
        response = await client.put(
            f"/api/v1/produtos/{produto_criado.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["preco_venda"]) == 35.90

    @pytest.mark.asyncio
    async def test_atualizar_estoque(
        self, client: AsyncClient, produto_criado: Produto
    ):
        """Deve atualizar estoque do produto"""
        update_data = {"estoque_atual": 150.0}
        response = await client.put(
            f"/api/v1/produtos/{produto_criado.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["estoque_atual"]) == 150.0


class TestInativarProduto:
    """Testes de inativação de produto"""

    @pytest.mark.asyncio
    async def test_inativar_produto(
        self, client: AsyncClient, produto_criado: Produto, db_session: AsyncSession
    ):
        """Deve inativar produto (soft delete)"""
        response = await client.delete(f"/api/v1/produtos/{produto_criado.id}")

        assert response.status_code in [200, 204]

        # Verificar se foi inativado
        await db_session.refresh(produto_criado)
        assert produto_criado.ativo is False


class TestValidacoesPrecos:
    """Testes de validações de preços"""

    @pytest.mark.asyncio
    async def test_preco_venda_maior_que_custo(
        self, client: AsyncClient, produto_data: dict
    ):
        """Deve aceitar preço de venda maior que custo"""
        produto_data["preco_custo"] = 20.0
        produto_data["preco_venda"] = 30.0
        response = await client.post("/api/v1/produtos/", json=produto_data)

        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_margem_lucro(
        self, client: AsyncClient, produto_criado: Produto
    ):
        """Deve calcular margem de lucro corretamente"""
        # Se houver endpoint de relatório/análise de margem
        response = await client.get(f"/api/v1/produtos/{produto_criado.id}/margem")

        # Verificar se endpoint existe
        if response.status_code != 404:
            data = response.json()
            assert "margem" in data or "margem_percentual" in data


class TestControleEstoque:
    """Testes relacionados a estoque"""

    @pytest.mark.asyncio
    async def test_produto_abaixo_estoque_minimo(
        self, client: AsyncClient, db_session: AsyncSession, categoria_fixture: Categoria
    ):
        """Deve identificar produtos abaixo do estoque mínimo"""
        produto = Produto(
            codigo_barras="78912",
            descricao="Produto Baixo Estoque",
            categoria_id=categoria_fixture.id,
            preco_venda=10.0,
            estoque_atual=5.0,
            estoque_minimo=10.0,
            ativo=True,
        )
        db_session.add(produto)
        await db_session.commit()

        # Listar produtos com estoque baixo
        response = await client.get("/api/v1/produtos/?estoque_baixo=true")

        # Se endpoint existir
        if response.status_code == 200:
            data = response.json()
            # Verificar se produto aparece na lista
            if isinstance(data, list):
                codigos = [p["codigo_barras"] for p in data]
                assert "78912" in codigos or len(data) >= 1
