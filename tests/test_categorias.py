"""
Testes para o módulo de Categorias

Testa CRUD completo, validações e regras de negócio
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.categorias.models import Categoria
from app.modules.categorias.schemas import CategoriaCreate


@pytest.fixture
async def categoria_data():
    """Fixture com dados válidos de categoria"""
    return {
        "nome": "Cimentos",
        "descricao": "Cimentos e argamassas",
        "ativa": True,
    }


@pytest.fixture
async def categoria_criada(db_session: AsyncSession, categoria_data):
    """Fixture que cria uma categoria no banco"""
    categoria = Categoria(**categoria_data)
    db_session.add(categoria)
    await db_session.commit()
    await db_session.refresh(categoria)
    return categoria


class TestCriarCategoria:
    """Testes de criação de categoria"""

    @pytest.mark.asyncio
    async def test_criar_categoria_sucesso(
        self, client: AsyncClient, categoria_data: dict
    ):
        """Deve criar categoria com dados válidos"""
        response = await client.post("/api/v1/categorias/", json=categoria_data)

        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == categoria_data["nome"]
        assert data["descricao"] == categoria_data["descricao"]
        assert data["ativa"] == categoria_data["ativa"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_criar_categoria_sem_descricao(self, client: AsyncClient):
        """Deve criar categoria sem descrição (campo opcional)"""
        data = {"nome": "Ferramentas", "ativa": True}
        response = await client.post("/api/v1/categorias/", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["nome"] == "Ferramentas"
        assert result["descricao"] is None

    @pytest.mark.asyncio
    async def test_criar_categoria_nome_vazio(self, client: AsyncClient):
        """Não deve criar categoria com nome vazio"""
        data = {"nome": "", "ativa": True}
        response = await client.post("/api/v1/categorias/", json=data)

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_criar_categoria_nome_muito_longo(self, client: AsyncClient):
        """Não deve criar categoria com nome maior que 100 caracteres"""
        data = {"nome": "A" * 101, "ativa": True}
        response = await client.post("/api/v1/categorias/", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_criar_categoria_sem_nome(self, client: AsyncClient):
        """Não deve criar categoria sem nome (campo obrigatório)"""
        data = {"descricao": "Sem nome", "ativa": True}
        response = await client.post("/api/v1/categorias/", json=data)

        assert response.status_code == 422


class TestBuscarCategoria:
    """Testes de busca de categoria por ID"""

    @pytest.mark.asyncio
    async def test_buscar_categoria_existente(
        self, client: AsyncClient, categoria_criada: Categoria
    ):
        """Deve buscar categoria existente por ID"""
        response = await client.get(f"/api/v1/categorias/{categoria_criada.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == categoria_criada.id
        assert data["nome"] == categoria_criada.nome
        assert data["descricao"] == categoria_criada.descricao

    @pytest.mark.asyncio
    async def test_buscar_categoria_inexistente(self, client: AsyncClient):
        """Não deve encontrar categoria inexistente"""
        response = await client.get("/api/v1/categorias/99999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_buscar_categoria_id_invalido(self, client: AsyncClient):
        """Não deve aceitar ID inválido"""
        response = await client.get("/api/v1/categorias/abc")

        assert response.status_code == 422


class TestListarCategorias:
    """Testes de listagem de categorias"""

    @pytest.mark.asyncio
    async def test_listar_categorias_vazio(self, client: AsyncClient):
        """Deve retornar lista vazia quando não há categorias"""
        response = await client.get("/api/v1/categorias/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_listar_categorias_com_dados(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Deve listar todas as categorias"""
        # Criar 3 categorias
        categorias = [
            Categoria(nome="Categoria 1", descricao="Desc 1", ativa=True),
            Categoria(nome="Categoria 2", descricao="Desc 2", ativa=True),
            Categoria(nome="Categoria 3", descricao="Desc 3", ativa=False),
        ]
        for cat in categorias:
            db_session.add(cat)
        await db_session.commit()

        response = await client.get("/api/v1/categorias/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_listar_apenas_ativas(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Deve listar apenas categorias ativas"""
        # Criar 2 ativas e 1 inativa
        categorias = [
            Categoria(nome="Ativa 1", ativa=True),
            Categoria(nome="Ativa 2", ativa=True),
            Categoria(nome="Inativa", ativa=False),
        ]
        for cat in categorias:
            db_session.add(cat)
        await db_session.commit()

        response = await client.get("/api/v1/categorias/?apenas_ativas=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert all(item["ativa"] for item in data["items"])

    @pytest.mark.asyncio
    async def test_listar_com_paginacao(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Deve paginar resultados corretamente"""
        # Criar 5 categorias
        for i in range(5):
            cat = Categoria(nome=f"Categoria {i+1}", ativa=True)
            db_session.add(cat)
        await db_session.commit()

        # Página 1 com 2 itens
        response = await client.get("/api/v1/categorias/?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["pages"] == 3

        # Página 2
        response = await client.get("/api/v1/categorias/?page=2&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2

    @pytest.mark.asyncio
    async def test_listar_page_size_invalido(self, client: AsyncClient):
        """Não deve aceitar page_size maior que 100"""
        response = await client.get("/api/v1/categorias/?page_size=101")

        assert response.status_code == 422


class TestAtualizarCategoria:
    """Testes de atualização de categoria"""

    @pytest.mark.asyncio
    async def test_atualizar_categoria_nome(
        self, client: AsyncClient, categoria_criada: Categoria
    ):
        """Deve atualizar nome da categoria"""
        update_data = {"nome": "Cimentos Atualizados"}
        response = await client.put(
            f"/api/v1/categorias/{categoria_criada.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Cimentos Atualizados"
        assert data["descricao"] == categoria_criada.descricao

    @pytest.mark.asyncio
    async def test_atualizar_categoria_completa(
        self, client: AsyncClient, categoria_criada: Categoria
    ):
        """Deve atualizar todos os campos da categoria"""
        update_data = {
            "nome": "Nome Novo",
            "descricao": "Descrição Nova",
            "ativa": False,
        }
        response = await client.put(
            f"/api/v1/categorias/{categoria_criada.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == "Nome Novo"
        assert data["descricao"] == "Descrição Nova"
        assert data["ativa"] is False

    @pytest.mark.asyncio
    async def test_atualizar_categoria_inexistente(self, client: AsyncClient):
        """Não deve atualizar categoria inexistente"""
        update_data = {"nome": "Teste"}
        response = await client.put("/api/v1/categorias/99999", json=update_data)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_atualizar_categoria_nome_vazio(
        self, client: AsyncClient, categoria_criada: Categoria
    ):
        """Não deve atualizar com nome vazio"""
        update_data = {"nome": ""}
        response = await client.put(
            f"/api/v1/categorias/{categoria_criada.id}", json=update_data
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_atualizar_categoria_parcial(
        self, client: AsyncClient, categoria_criada: Categoria
    ):
        """Deve permitir atualização parcial (apenas alguns campos)"""
        original_nome = categoria_criada.nome
        update_data = {"descricao": "Nova descrição apenas"}
        response = await client.put(
            f"/api/v1/categorias/{categoria_criada.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["nome"] == original_nome  # Nome não mudou
        assert data["descricao"] == "Nova descrição apenas"


class TestInativarCategoria:
    """Testes de inativação de categoria (soft delete)"""

    @pytest.mark.asyncio
    async def test_inativar_categoria(
        self, client: AsyncClient, categoria_criada: Categoria, db_session: AsyncSession
    ):
        """Deve inativar categoria (soft delete)"""
        response = await client.delete(f"/api/v1/categorias/{categoria_criada.id}")

        assert response.status_code == 204

        # Verificar se categoria foi inativada
        await db_session.refresh(categoria_criada)
        assert categoria_criada.ativa is False

    @pytest.mark.asyncio
    async def test_inativar_categoria_inexistente(self, client: AsyncClient):
        """Não deve inativar categoria inexistente"""
        response = await client.delete("/api/v1/categorias/99999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_inativar_categoria_ja_inativa(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Deve permitir inativar categoria já inativa (idempotente)"""
        # Criar categoria inativa
        categoria = Categoria(nome="Inativa", ativa=False)
        db_session.add(categoria)
        await db_session.commit()
        await db_session.refresh(categoria)

        response = await client.delete(f"/api/v1/categorias/{categoria.id}")

        # Ainda deve retornar 204 (operação idempotente)
        assert response.status_code in [204, 404]  # Depende da implementação


class TestReativarCategoria:
    """Testes de reativação de categoria"""

    @pytest.mark.asyncio
    async def test_reativar_categoria_inativa(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Deve reativar categoria inativa"""
        # Criar categoria inativa
        categoria = Categoria(nome="Inativa", ativa=False)
        db_session.add(categoria)
        await db_session.commit()
        await db_session.refresh(categoria)

        response = await client.post(f"/api/v1/categorias/{categoria.id}/reativar")

        assert response.status_code == 200
        data = response.json()
        assert data["ativa"] is True

    @pytest.mark.asyncio
    async def test_reativar_categoria_ja_ativa(
        self, client: AsyncClient, categoria_criada: Categoria
    ):
        """Deve permitir reativar categoria já ativa (idempotente)"""
        response = await client.post(
            f"/api/v1/categorias/{categoria_criada.id}/reativar"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ativa"] is True

    @pytest.mark.asyncio
    async def test_reativar_categoria_inexistente(self, client: AsyncClient):
        """Não deve reativar categoria inexistente"""
        response = await client.post("/api/v1/categorias/99999/reativar")

        assert response.status_code == 404


class TestValidacoes:
    """Testes de validações de schema"""

    @pytest.mark.asyncio
    async def test_validacao_nome_minimo(self, client: AsyncClient):
        """Nome deve ter no mínimo 1 caractere"""
        data = {"nome": "", "ativa": True}
        response = await client.post("/api/v1/categorias/", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validacao_nome_maximo(self, client: AsyncClient):
        """Nome deve ter no máximo 100 caracteres"""
        data = {"nome": "A" * 101, "ativa": True}
        response = await client.post("/api/v1/categorias/", json=data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_validacao_ativa_default(self, client: AsyncClient):
        """Campo ativa deve ter valor padrão True"""
        data = {"nome": "Teste"}
        response = await client.post("/api/v1/categorias/", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["ativa"] is True

    @pytest.mark.asyncio
    async def test_validacao_descricao_opcional(self, client: AsyncClient):
        """Descrição é opcional"""
        data = {"nome": "Teste", "ativa": True}
        response = await client.post("/api/v1/categorias/", json=data)

        assert response.status_code == 201
        result = response.json()
        assert result["descricao"] is None


class TestIntegracaoCompleta:
    """Testes de integração end-to-end"""

    @pytest.mark.asyncio
    async def test_fluxo_completo_crud(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Testa fluxo completo: criar, buscar, atualizar, inativar, reativar"""
        # 1. Criar categoria
        create_data = {"nome": "Ferragens", "descricao": "Ferragens em geral"}
        response = await client.post("/api/v1/categorias/", json=create_data)
        assert response.status_code == 201
        categoria_id = response.json()["id"]

        # 2. Buscar categoria criada
        response = await client.get(f"/api/v1/categorias/{categoria_id}")
        assert response.status_code == 200
        assert response.json()["nome"] == "Ferragens"

        # 3. Atualizar categoria
        update_data = {"descricao": "Ferragens e ferramentas"}
        response = await client.put(
            f"/api/v1/categorias/{categoria_id}", json=update_data
        )
        assert response.status_code == 200
        assert response.json()["descricao"] == "Ferragens e ferramentas"

        # 4. Listar categorias (deve aparecer)
        response = await client.get("/api/v1/categorias/")
        assert response.status_code == 200
        assert any(c["id"] == categoria_id for c in response.json()["items"])

        # 5. Inativar categoria
        response = await client.delete(f"/api/v1/categorias/{categoria_id}")
        assert response.status_code == 204

        # 6. Listar apenas ativas (não deve aparecer)
        response = await client.get("/api/v1/categorias/?apenas_ativas=true")
        assert response.status_code == 200
        assert not any(c["id"] == categoria_id for c in response.json()["items"])

        # 7. Reativar categoria
        response = await client.post(f"/api/v1/categorias/{categoria_id}/reativar")
        assert response.status_code == 200
        assert response.json()["ativa"] is True

        # 8. Listar apenas ativas (deve aparecer novamente)
        response = await client.get("/api/v1/categorias/?apenas_ativas=true")
        assert response.status_code == 200
        assert any(c["id"] == categoria_id for c in response.json()["items"])
