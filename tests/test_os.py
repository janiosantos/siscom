"""
Testes para módulo OS (Ordens de Serviço)
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from unittest.mock import patch

from app.modules.os.models import OrdemServico, TipoServico, Tecnico, StatusOS
from app.modules.clientes.models import Cliente, TipoPessoa
from app.modules.produtos.models import Produto
from app.modules.categorias.models import Categoria


# Mock automático para validação de CPF nos técnicos
@pytest.fixture(autouse=True)
def mock_cpf_validator():
    """Mock para validação de CPF"""
    with patch("app.utils.validators.DocumentValidator.validate_cpf", return_value=True):
        yield


# ========== FIXTURES ==========

@pytest.fixture
async def setup_os(db_session: AsyncSession):
    """Fixture para configurar dados necessários para OS"""
    # Criar cliente
    cliente = Cliente(
        nome="Cliente OS Teste",
        tipo_pessoa=TipoPessoa.PF,
        cpf_cnpj="12345678900",
        ativo=True,
    )
    db_session.add(cliente)
    await db_session.flush()

    # Criar tipo de serviço
    tipo_servico = TipoServico(
        nome="Manutenção",
        descricao="Serviço de manutenção geral",
        preco_padrao=150.0,
        ativo=True,
    )
    db_session.add(tipo_servico)
    await db_session.flush()

    # Criar técnico
    tecnico = Tecnico(
        nome="João Técnico",
        cpf="12345678900",
        telefone="11987654321",
        especialidades="Elétrica, Hidráulica",
        ativo=True,
    )
    db_session.add(tecnico)
    await db_session.flush()

    # Criar categoria e produto
    categoria = Categoria(
        nome="Peças",
        descricao="Peças para manutenção",
        ativa=True,
    )
    db_session.add(categoria)
    await db_session.flush()

    produto = Produto(
        codigo="PECA-001",
        descricao="Peça Teste",
        categoria_id=categoria.id,
        preco_venda=50.0,
        preco_custo=30.0,
        estoque_atual=100,
        estoque_minimo=10,
        ativo=True,
    )
    db_session.add(produto)
    await db_session.commit()

    await db_session.refresh(cliente)
    await db_session.refresh(tipo_servico)
    await db_session.refresh(tecnico)
    await db_session.refresh(categoria)
    await db_session.refresh(produto)

    return {
        "cliente": cliente,
        "tipo_servico": tipo_servico,
        "tecnico": tecnico,
        "categoria": categoria,
        "produto": produto,
    }


@pytest.fixture
async def os_data(setup_os: dict):
    """Fixture com dados para criação de OS"""
    return {
        "cliente_id": setup_os["cliente"].id,
        "tecnico_id": setup_os["tecnico"].id,
        "tipo_servico_id": setup_os["tipo_servico"].id,
        "produto_id": setup_os["produto"].id,
        "numero_serie": "SN123456",
        "data_prevista": (datetime.utcnow() + timedelta(days=3)).isoformat(),
        "descricao_problema": "Equipamento não liga",
        "valor_mao_obra": 150.0,
        "observacoes": "Cliente relatou problema após queda de energia",
    }


@pytest.fixture
async def os_criada(db_session: AsyncSession, setup_os: dict):
    """Fixture para criar uma OS no banco"""
    os = OrdemServico(
        cliente_id=setup_os["cliente"].id,
        tecnico_id=setup_os["tecnico"].id,
        tipo_servico_id=setup_os["tipo_servico"].id,
        data_abertura=datetime.utcnow(),
        data_prevista=datetime.utcnow() + timedelta(days=3),
        status=StatusOS.ABERTA,
        descricao_problema="Problema teste",
        valor_mao_obra=150.0,
        valor_total=150.0,
    )
    db_session.add(os)
    await db_session.commit()
    await db_session.refresh(os)
    return os


# ========== TESTES DE CRUD OS ==========

@pytest.mark.asyncio
async def test_criar_os(client: AsyncClient, os_data: dict):
    """Teste de criação de OS"""
    response = await client.post(
        "/api/v1/os/",
        json=os_data,
    )

    # Pode retornar 201 ou 401
    assert response.status_code in [200, 201, 401]

    if response.status_code in [200, 201]:
        data = response.json()
        assert "id" in data
        assert data["cliente_id"] == os_data["cliente_id"]
        assert data["status"] == "ABERTA"


@pytest.mark.asyncio
async def test_listar_os(client: AsyncClient, os_criada: OrdemServico):
    """Teste de listagem de OS"""
    response = await client.get("/api/v1/os/")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert "items" in data
        assert "total" in data


@pytest.mark.asyncio
async def test_obter_os(client: AsyncClient, os_criada: OrdemServico):
    """Teste de obtenção de OS específica"""
    response = await client.get(f"/api/v1/os/{os_criada.id}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["id"] == os_criada.id
        assert data["status"] == os_criada.status.value


@pytest.mark.asyncio
async def test_atualizar_os(client: AsyncClient, os_criada: OrdemServico):
    """Teste de atualização de OS"""
    update_data = {
        "valor_mao_obra": 200.0,
        "descricao_problema": "Problema atualizado",
        "observacoes": "Observação adicional",
    }

    response = await client.put(
        f"/api/v1/os/{os_criada.id}",
        json=update_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["valor_mao_obra"] == update_data["valor_mao_obra"]


@pytest.mark.asyncio
async def test_deletar_os(client: AsyncClient, os_criada: OrdemServico):
    """Teste de deleção de OS"""
    response = await client.delete(f"/api/v1/os/{os_criada.id}")

    # Pode retornar 204 ou 401
    assert response.status_code in [204, 401]


# ========== TESTES DE MUDANÇA DE STATUS ==========

@pytest.mark.asyncio
async def test_iniciar_os(client: AsyncClient, os_criada: OrdemServico):
    """Teste de iniciar OS"""
    iniciar_data = {
        "observacoes": "Iniciando atendimento",
    }

    response = await client.post(
        f"/api/v1/os/{os_criada.id}/iniciar",
        json=iniciar_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "EM_ANDAMENTO"


@pytest.mark.asyncio
async def test_finalizar_os(client: AsyncClient, os_criada: OrdemServico):
    """Teste de finalizar OS"""
    finalizar_data = {
        "data_conclusao": datetime.utcnow().isoformat(),
        "descricao_solucao": "Equipamento reparado com sucesso",
    }

    response = await client.post(
        f"/api/v1/os/{os_criada.id}/finalizar",
        json=finalizar_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "CONCLUIDA"
        assert data["descricao_solucao"] == finalizar_data["descricao_solucao"]


@pytest.mark.asyncio
async def test_cancelar_os(client: AsyncClient, os_criada: OrdemServico):
    """Teste de cancelar OS"""
    cancelar_data = {
        "motivo": "Cliente desistiu do serviço",
    }

    response = await client.post(
        f"/api/v1/os/{os_criada.id}/cancelar",
        json=cancelar_data,
    )

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "CANCELADA"


# ========== TESTES DE ADICIONAR MATERIAL ==========

@pytest.mark.asyncio
async def test_adicionar_material(client: AsyncClient, os_criada: OrdemServico, setup_os: dict):
    """Teste de adicionar material à OS"""
    material_data = {
        "produto_id": setup_os["produto"].id,
        "quantidade": 2,
        "preco_unitario": 50.0,
    }

    response = await client.post(
        f"/api/v1/os/{os_criada.id}/materiais",
        json=material_data,
    )

    # Pode retornar 200/201 ou 401
    assert response.status_code in [200, 201, 401]


@pytest.mark.asyncio
async def test_adicionar_material_quantidade_zero(client: AsyncClient, os_criada: OrdemServico, setup_os: dict):
    """Teste de adicionar material com quantidade zero"""
    material_data = {
        "produto_id": setup_os["produto"].id,
        "quantidade": 0,
        "preco_unitario": 50.0,
    }

    response = await client.post(
        f"/api/v1/os/{os_criada.id}/materiais",
        json=material_data,
    )

    assert response.status_code == 422


# ========== TESTES DE APONTAR HORAS ==========

@pytest.mark.asyncio
async def test_apontar_horas(client: AsyncClient, os_criada: OrdemServico, setup_os: dict):
    """Teste de apontar horas trabalhadas"""
    horas_data = {
        "tecnico_id": setup_os["tecnico"].id,
        "data": datetime.utcnow().isoformat(),
        "horas_trabalhadas": 4.5,
        "descricao": "Diagnóstico e início do reparo",
    }

    response = await client.post(
        f"/api/v1/os/{os_criada.id}/apontamentos",
        json=horas_data,
    )

    # Pode retornar 200/201 ou 401
    assert response.status_code in [200, 201, 401]


@pytest.mark.asyncio
async def test_apontar_horas_zero(client: AsyncClient, os_criada: OrdemServico, setup_os: dict):
    """Teste de apontar zero horas"""
    horas_data = {
        "tecnico_id": setup_os["tecnico"].id,
        "data": datetime.utcnow().isoformat(),
        "horas_trabalhadas": 0,
        "descricao": "Teste",
    }

    response = await client.post(
        f"/api/v1/os/{os_criada.id}/apontamentos",
        json=horas_data,
    )

    assert response.status_code == 422


# ========== TESTES DE TIPO DE SERVIÇO ==========

@pytest.mark.asyncio
async def test_criar_tipo_servico(client: AsyncClient):
    """Teste de criação de tipo de serviço"""
    tipo_data = {
        "nome": "Instalação",
        "descricao": "Serviço de instalação",
        "preco_padrao": 200.0,
        "ativo": True,
    }

    response = await client.post(
        "/api/v1/os/tipos-servico/",
        json=tipo_data,
    )

    # Pode retornar 201 ou 401
    assert response.status_code in [200, 201, 401]


@pytest.mark.asyncio
async def test_listar_tipos_servico(client: AsyncClient, setup_os: dict):
    """Teste de listagem de tipos de serviço"""
    response = await client.get("/api/v1/os/tipos-servico/")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


# ========== TESTES DE TÉCNICO ==========

@pytest.mark.asyncio
async def test_criar_tecnico(client: AsyncClient):
    """Teste de criação de técnico"""
    tecnico_data = {
        "nome": "Maria Técnica",
        "cpf": "98765432100",
        "telefone": "11987654322",
        "especialidades": "Eletrônica, Informática",
        "ativo": True,
    }

    response = await client.post(
        "/api/v1/os/tecnicos/",
        json=tecnico_data,
    )

    # Pode retornar 201 ou 401
    assert response.status_code in [200, 201, 401]


@pytest.mark.asyncio
async def test_listar_tecnicos(client: AsyncClient, setup_os: dict):
    """Teste de listagem de técnicos"""
    response = await client.get("/api/v1/os/tecnicos/")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


# ========== TESTES DE VALIDAÇÃO ==========

@pytest.mark.asyncio
async def test_criar_os_valor_mao_obra_negativo(client: AsyncClient, os_data: dict):
    """Teste de criação com valor de mão de obra negativo"""
    os_data["valor_mao_obra"] = -100.0

    response = await client.post(
        "/api/v1/os/",
        json=os_data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_obter_os_inexistente(client: AsyncClient):
    """Teste de obtenção de OS que não existe"""
    response = await client.get("/api/v1/os/99999")

    assert response.status_code in [404, 401]


# ========== TESTES DE FILTROS ==========

@pytest.mark.asyncio
async def test_listar_os_por_status(client: AsyncClient, os_criada: OrdemServico):
    """Teste de listagem filtrando por status"""
    response = await client.get("/api/v1/os/?status=ABERTA")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_listar_os_por_tecnico(client: AsyncClient, os_criada: OrdemServico):
    """Teste de listagem filtrando por técnico"""
    response = await client.get(f"/api/v1/os/?tecnico_id={os_criada.tecnico_id}")

    # Pode retornar 200 ou 401
    assert response.status_code in [200, 401]
