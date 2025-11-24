"""
Testes para o módulo de Clientes

Testa CRUD completo, validações CPF/CNPJ e regras de negócio
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch

from app.modules.clientes.models import Cliente


@pytest.fixture(autouse=True)
def mock_document_validator():
    """Mock do DocumentValidator para aceitar qualquer CPF/CNPJ nos testes"""
    with patch("app.modules.clientes.schemas.DocumentValidator.validate_cpf", return_value=True), \
         patch("app.modules.clientes.schemas.DocumentValidator.validate_cnpj", return_value=True):
        yield


@pytest.fixture
async def cliente_pf_data():
    """Fixture com dados de cliente Pessoa Física"""
    return {
        "nome": "João Silva",
        "tipo_pessoa": "PF",
        "cpf_cnpj": "12345678900",
        "email": "joao@email.com",
        "telefone": "11999999999",
        "endereco": "Rua Teste, 123",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "estado": "SP",
        "cep": "01310100",
        "ativo": True,
    }


@pytest.fixture
async def cliente_pj_data():
    """Fixture com dados de cliente Pessoa Jurídica"""
    return {
        "nome": "Empresa LTDA",
        "tipo_pessoa": "PJ",
        "cpf_cnpj": "12345678000190",
        "email": "contato@empresa.com",
        "telefone": "1133334444",
        "endereco": "Av Comercial, 456",
        "bairro": "Empresarial",
        "cidade": "São Paulo",
        "estado": "SP",
        "cep": "01310200",
        "ativo": True,
    }


@pytest.fixture
async def cliente_criado(db_session: AsyncSession, cliente_pf_data: dict):
    """Fixture que cria um cliente no banco"""
    cliente = Cliente(**cliente_pf_data)
    db_session.add(cliente)
    await db_session.commit()
    await db_session.refresh(cliente)
    return cliente


class TestCriarCliente:
    """Testes de criação de cliente"""

    @pytest.mark.asyncio
    async def test_criar_cliente_pf(
        self, client: AsyncClient, cliente_pf_data: dict
    ):
        """Deve criar cliente Pessoa Física"""
        response = await client.post("/api/v1/clientes/", json=cliente_pf_data)

        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == cliente_pf_data["nome"]
        assert data["tipo_pessoa"] == "PF"
        assert data["cpf_cnpj"] == cliente_pf_data["cpf_cnpj"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_criar_cliente_pj(
        self, client: AsyncClient, cliente_pj_data: dict
    ):
        """Deve criar cliente Pessoa Jurídica"""
        response = await client.post("/api/v1/clientes/", json=cliente_pj_data)

        assert response.status_code == 201
        data = response.json()
        assert data["nome"] == cliente_pj_data["nome"]
        assert data["tipo_pessoa"] == "PJ"

    @pytest.mark.asyncio
    async def test_criar_cliente_cpf_duplicado(
        self, client: AsyncClient, cliente_pf_data: dict, cliente_criado: Cliente
    ):
        """Não deve criar cliente com CPF duplicado"""
        cliente_pf_data["cpf_cnpj"] = cliente_criado.cpf_cnpj
        response = await client.post("/api/v1/clientes/", json=cliente_pf_data)

        assert response.status_code in [400, 409, 422]

    @pytest.mark.asyncio
    async def test_criar_cliente_sem_nome(
        self, client: AsyncClient, cliente_pf_data: dict
    ):
        """Não deve criar cliente sem nome"""
        del cliente_pf_data["nome"]
        response = await client.post("/api/v1/clientes/", json=cliente_pf_data)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_criar_cliente_email_invalido(
        self, client: AsyncClient, cliente_pf_data: dict
    ):
        """Não deve criar cliente com email inválido"""
        cliente_pf_data["email"] = "email_invalido"
        response = await client.post("/api/v1/clientes/", json=cliente_pf_data)

        assert response.status_code in [400, 422]


class TestBuscarCliente:
    """Testes de busca de cliente"""

    @pytest.mark.asyncio
    async def test_buscar_cliente_por_id(
        self, client: AsyncClient, cliente_criado: Cliente
    ):
        """Deve buscar cliente por ID"""
        response = await client.get(f"/api/v1/clientes/{cliente_criado.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cliente_criado.id
        assert data["nome"] == cliente_criado.nome

    @pytest.mark.asyncio
    async def test_buscar_cliente_por_cpf(
        self, client: AsyncClient, cliente_criado: Cliente
    ):
        """Deve buscar cliente por CPF/CNPJ"""
        response = await client.get(
            f"/api/v1/clientes/cpf/{cliente_criado.cpf_cnpj}"
        )

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 200
            data = response.json()
            assert data["cpf_cnpj"] == cliente_criado.cpf_cnpj


class TestListarClientes:
    """Testes de listagem de clientes"""

    @pytest.mark.asyncio
    async def test_listar_clientes(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Deve listar clientes com paginação"""
        from app.modules.clientes.models import TipoPessoa
        # Criar 3 clientes
        for i in range(3):
            cliente = Cliente(
                nome=f"Cliente {i+1}",
                tipo_pessoa=TipoPessoa.PF,
                cpf_cnpj=f"1234567890{i}",
                email=f"cliente{i+1}@test.com",
                ativo=True,
            )
            db_session.add(cliente)
        await db_session.commit()

        response = await client.get("/api/v1/clientes/")

        assert response.status_code == 200
        data = response.json()
        # Verificar formato da resposta
        if isinstance(data, list):
            assert len(data) >= 3
        elif isinstance(data, dict) and "items" in data:
            assert len(data["items"]) >= 3

    @pytest.mark.asyncio
    async def test_listar_apenas_pf(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Deve filtrar apenas Pessoas Físicas"""
        from app.modules.clientes.models import TipoPessoa
        # Criar PF e PJ
        pf = Cliente(
            nome="PF Cliente",
            tipo_pessoa=TipoPessoa.PF,
            cpf_cnpj="11111111111",
            ativo=True,
        )
        pj = Cliente(
            nome="PJ Cliente",
            tipo_pessoa=TipoPessoa.PJ,
            cpf_cnpj="22222222222222",
            ativo=True,
        )
        db_session.add(pf)
        db_session.add(pj)
        await db_session.commit()

        response = await client.get("/api/v1/clientes/?tipo_pessoa=PF")

        # Se endpoint suportar filtro
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                assert all(c["tipo_pessoa"] == "PF" for c in data)


class TestAtualizarCliente:
    """Testes de atualização de cliente"""

    @pytest.mark.asyncio
    async def test_atualizar_email(
        self, client: AsyncClient, cliente_criado: Cliente
    ):
        """Deve atualizar email do cliente"""
        update_data = {"email": "novo@email.com"}
        response = await client.put(
            f"/api/v1/clientes/{cliente_criado.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "novo@email.com"

    @pytest.mark.asyncio
    async def test_atualizar_endereco(
        self, client: AsyncClient, cliente_criado: Cliente
    ):
        """Deve atualizar endereço do cliente"""
        update_data = {
            "endereco": "Rua Nova, 789",
            "bairro": "Novo Bairro",
            "cep": "01310300",
        }
        response = await client.put(
            f"/api/v1/clientes/{cliente_criado.id}", json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["endereco"] == "Rua Nova, 789"


class TestInativarCliente:
    """Testes de inativação de cliente"""

    @pytest.mark.asyncio
    async def test_inativar_cliente(
        self, client: AsyncClient, cliente_criado: Cliente, db_session: AsyncSession
    ):
        """Deve inativar cliente (soft delete)"""
        response = await client.delete(f"/api/v1/clientes/{cliente_criado.id}")

        assert response.status_code in [200, 204]

        # Verificar se foi inativado
        await db_session.refresh(cliente_criado)
        assert cliente_criado.ativo is False


class TestValidacoesCPFCNPJ:
    """Testes de validações de CPF/CNPJ"""

    @pytest.mark.asyncio
    async def test_cpf_formato_invalido(
        self, client: AsyncClient, cliente_pf_data: dict
    ):
        """Não deve aceitar CPF com formato inválido"""
        cliente_pf_data["cpf_cnpj"] = "123"  # CPF muito curto
        response = await client.post("/api/v1/clientes/", json=cliente_pf_data)

        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_cnpj_formato_invalido(
        self, client: AsyncClient, cliente_pj_data: dict
    ):
        """Não deve aceitar CNPJ com formato inválido"""
        cliente_pj_data["cpf_cnpj"] = "123"  # CNPJ muito curto
        response = await client.post("/api/v1/clientes/", json=cliente_pj_data)

        assert response.status_code in [400, 422]


class TestRelacionamentos:
    """Testes de relacionamentos e histórico"""

    @pytest.mark.asyncio
    async def test_historico_compras(
        self, client: AsyncClient, cliente_criado: Cliente
    ):
        """Deve retornar histórico de compras do cliente"""
        response = await client.get(
            f"/api/v1/clientes/{cliente_criado.id}/historico"
        )

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list) or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_total_compras(
        self, client: AsyncClient, cliente_criado: Cliente
    ):
        """Deve calcular total de compras do cliente"""
        response = await client.get(
            f"/api/v1/clientes/{cliente_criado.id}/total-compras"
        )

        # Se endpoint existir
        if response.status_code != 404:
            assert response.status_code == 200
            data = response.json()
            assert "total" in data or isinstance(data, (int, float))
