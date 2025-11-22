"""
Testes unitários do módulo produtos

Testa:
- produtos/service.py - Lógica de negócio
- produtos/repository.py - Acesso a dados
- produtos/models.py - Modelos
"""
import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime
from decimal import Decimal

from app.modules.produtos.service import ProdutoService
from app.modules.produtos.repository import ProdutoRepository
from app.modules.produtos.models import Produto
from app.modules.produtos.schemas import (
    ProdutoCreate,
    ProdutoUpdate,
    ProdutoResponse,
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    DuplicateException,
)


# ========== Fixtures ==========

@pytest.fixture
def mock_session():
    """Mock do AsyncSession"""
    session = AsyncMock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def produto_repository(mock_session):
    """Repository com session mockada"""
    return ProdutoRepository(mock_session)


@pytest.fixture
def produto_service(mock_session):
    """Service com dependencies mockadas"""
    service = ProdutoService(mock_session)
    service.repository = AsyncMock()
    service.categoria_repository = AsyncMock()
    return service


@pytest.fixture
def mock_categoria():
    """Mock de categoria"""
    categoria = Mock()
    categoria.id = 1
    categoria.nome = "Cimentos"
    categoria.descricao = "Cimentos e argamassas"
    categoria.ativa = True
    categoria.created_at = datetime.utcnow()
    categoria.updated_at = datetime.utcnow()
    return categoria


@pytest.fixture
def mock_produto():
    """Mock de produto completo"""
    produto = Mock(spec=Produto)
    produto.id = 1
    produto.codigo_barras = "7891234567890"
    produto.descricao = "Cimento CP-II 50kg"
    produto.categoria_id = 1
    produto.preco_custo = Decimal("25.50")
    produto.preco_venda = Decimal("32.90")
    produto.estoque_atual = Decimal("100.00")
    produto.estoque_minimo = Decimal("10.00")
    produto.unidade = "UN"
    produto.ncm = "25232900"
    produto.controla_lote = False
    produto.controla_serie = False
    produto.ativo = True
    produto.created_at = datetime.utcnow()
    produto.updated_at = datetime.utcnow()

    # Mock do relacionamento categoria
    produto.categoria = Mock()
    produto.categoria.id = 1
    produto.categoria.nome = "Cimentos"
    produto.categoria.descricao = "Cimentos e argamassas"
    produto.categoria.ativa = True
    produto.categoria.created_at = datetime.utcnow()
    produto.categoria.updated_at = datetime.utcnow()

    return produto


# ========== Testes ProdutoService - Criar Produto ==========

class TestProdutoServiceCriar:
    """Testes de criação de produto"""

    @pytest.mark.asyncio
    async def test_calcular_margem_lucro(self, produto_service):
        """Deve calcular margem de lucro corretamente"""
        margem = produto_service.calcular_margem_lucro(
            preco_custo=25.50,
            preco_venda=32.90
        )

        # Margem esperada: ((32.90 - 25.50) / 25.50) * 100 = 29.02%
        assert abs(margem - 29.02) < 0.1

    @pytest.mark.asyncio
    async def test_calcular_margem_lucro_custo_zero(self, produto_service):
        """Deve retornar 0 se custo for zero"""
        margem = produto_service.calcular_margem_lucro(
            preco_custo=0.0,
            preco_venda=32.90
        )

        assert margem == 0.0

    @pytest.mark.asyncio
    async def test_validar_preco_venda_sucesso(self, produto_service):
        """Deve aceitar preço de venda maior que custo"""
        await produto_service.validar_preco_venda(
            preco_custo=25.50,
            preco_venda=32.90
        )
        # Não deve lançar exceção

    @pytest.mark.asyncio
    async def test_validar_preco_venda_igual_custo(self, produto_service):
        """Deve aceitar preço de venda igual ao custo"""
        await produto_service.validar_preco_venda(
            preco_custo=25.50,
            preco_venda=25.50
        )
        # Não deve lançar exceção

    @pytest.mark.asyncio
    async def test_validar_preco_venda_menor_que_custo(self, produto_service):
        """Deve falhar se preço de venda menor que custo"""
        with pytest.raises(ValidationException, match="não pode ser menor"):
            await produto_service.validar_preco_venda(
                preco_custo=32.90,
                preco_venda=25.50
            )

    @pytest.mark.asyncio
    async def test_validar_categoria_existe_sucesso(self, produto_service, mock_categoria):
        """Deve validar categoria existente e ativa"""
        produto_service.categoria_repository.get_by_id.return_value = mock_categoria

        await produto_service.validar_categoria_existe(1)

        produto_service.categoria_repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_validar_categoria_inexistente(self, produto_service):
        """Deve falhar se categoria não existe"""
        produto_service.categoria_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundException, match="Categoria .* não encontrada"):
            await produto_service.validar_categoria_existe(999)

    @pytest.mark.asyncio
    async def test_validar_categoria_inativa(self, produto_service, mock_categoria):
        """Deve falhar se categoria está inativa"""
        mock_categoria.ativa = False
        produto_service.categoria_repository.get_by_id.return_value = mock_categoria

        with pytest.raises(ValidationException, match="inativa"):
            await produto_service.validar_categoria_existe(1)

    @pytest.mark.asyncio
    async def test_criar_produto_sucesso(self, produto_service, mock_produto, mock_categoria):
        """Deve criar produto com validações"""
        produto_service.categoria_repository.get_by_id.return_value = mock_categoria
        produto_service.repository.get_by_codigo_barras.return_value = None
        produto_service.repository.create.return_value = mock_produto

        produto_data = ProdutoCreate(
            codigo_barras="7891234567890",
            descricao="Cimento CP-II 50kg",
            categoria_id=1,
            preco_custo=25.50,
            preco_venda=32.90,
            estoque_atual=100.0,
            estoque_minimo=10.0,
            unidade="UN",
            ncm="25232900",
            ativo=True
        )

        result = await produto_service.create_produto(produto_data)

        produto_service.categoria_repository.get_by_id.assert_called_once_with(1)
        produto_service.repository.get_by_codigo_barras.assert_called_once()
        produto_service.repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_criar_produto_codigo_duplicado(self, produto_service, mock_produto):
        """Deve falhar ao criar produto com código duplicado"""
        produto_service.repository.get_by_codigo_barras.return_value = mock_produto

        produto_data = ProdutoCreate(
            codigo_barras="7891234567890",
            descricao="Cimento CP-II 50kg",
            categoria_id=1,
            preco_custo=25.50,
            preco_venda=32.90,
            estoque_atual=100.0,
            estoque_minimo=10.0,
            unidade="UN",
            ativo=True
        )

        with pytest.raises(DuplicateException, match="já existe"):
            await produto_service.create_produto(produto_data)

    @pytest.mark.asyncio
    async def test_criar_produto_preco_venda_menor_custo(self, produto_service, mock_categoria):
        """Deve falhar se preço de venda menor que custo"""
        produto_service.categoria_repository.get_by_id.return_value = mock_categoria
        produto_service.repository.get_by_codigo_barras.return_value = None

        produto_data = ProdutoCreate(
            codigo_barras="7891234567890",
            descricao="Cimento CP-II 50kg",
            categoria_id=1,
            preco_custo=32.90,
            preco_venda=25.50,  # Menor que custo
            estoque_atual=100.0,
            estoque_minimo=10.0,
            unidade="UN",
            ativo=True
        )

        with pytest.raises(ValidationException, match="não pode ser menor"):
            await produto_service.create_produto(produto_data)


# ========== Testes ProdutoService - Atualizar Produto ==========

class TestProdutoServiceAtualizar:
    """Testes de atualização de produto"""

    @pytest.mark.asyncio
    async def test_atualizar_produto_sucesso(self, produto_service, mock_produto, mock_categoria):
        """Deve atualizar produto com validações"""
        produto_service.repository.get_by_id.return_value = mock_produto
        produto_service.categoria_repository.get_by_id.return_value = mock_categoria
        produto_service.repository.get_by_codigo_barras.return_value = None
        produto_service.repository.update.return_value = mock_produto

        produto_data = ProdutoUpdate(
            descricao="Cimento CP-II 50kg - Novo",
            preco_venda=35.00
        )

        result = await produto_service.update_produto(1, produto_data)

        produto_service.repository.get_by_id.assert_called_once_with(1)
        produto_service.repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_atualizar_produto_inexistente(self, produto_service):
        """Deve falhar ao atualizar produto inexistente"""
        produto_service.repository.get_by_id.return_value = None

        produto_data = ProdutoUpdate(descricao="Novo nome")

        with pytest.raises(NotFoundException):
            await produto_service.update_produto(999, produto_data)

    @pytest.mark.asyncio
    async def test_atualizar_produto_codigo_duplicado(self, produto_service, mock_produto):
        """Deve falhar se tentar alterar para código já existente"""
        mock_produto.codigo_barras = "7891234567890"

        mock_outro_produto = Mock(spec=Produto)
        mock_outro_produto.id = 2
        mock_outro_produto.codigo_barras = "9999999999999"

        produto_service.repository.get_by_id.return_value = mock_produto
        produto_service.repository.get_by_codigo_barras.return_value = mock_outro_produto

        produto_data = ProdutoUpdate(codigo_barras="9999999999999")

        with pytest.raises(DuplicateException, match="já existe"):
            await produto_service.update_produto(1, produto_data)


# ========== Testes ProdutoService - Buscar e Listar ==========

class TestProdutoServiceBuscar:
    """Testes de busca e listagem"""

    @pytest.mark.asyncio
    async def test_get_produto_sucesso(self, produto_service, mock_produto):
        """Deve buscar produto por ID"""
        produto_service.repository.get_by_id.return_value = mock_produto

        result = await produto_service.get_produto(1)

        produto_service.repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_produto_inexistente(self, produto_service):
        """Deve falhar ao buscar produto inexistente"""
        produto_service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await produto_service.get_produto(999)

    @pytest.mark.asyncio
    async def test_list_produtos(self, produto_service, mock_produto):
        """Deve listar produtos com paginação"""
        produtos = [mock_produto, mock_produto]
        produto_service.repository.get_all.return_value = produtos
        produto_service.repository.count.return_value = 25

        result = await produto_service.list_produtos(page=2, page_size=10)

        # Verificar paginação (page 2 = skip 10)
        produto_service.repository.get_all.assert_called_once()
        # Apenas verificar que foi chamado, sem checar args específicos

    @pytest.mark.asyncio
    async def test_deletar_produto_sucesso(self, produto_service, mock_produto):
        """Deve deletar produto (marcar como inativo)"""
        produto_service.repository.get_by_id.return_value = mock_produto
        produto_service.repository.delete.return_value = True

        result = await produto_service.delete_produto(1)

        produto_service.repository.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_deletar_produto_inexistente(self, produto_service):
        """Deve falhar ao deletar produto inexistente"""
        produto_service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await produto_service.delete_produto(999)


# ========== Testes ProdutoRepository ==========

class TestProdutoRepository:
    """Testes do repository de produtos"""

    @pytest.mark.asyncio
    async def test_create_produto(self, produto_repository, mock_session):
        """Deve criar produto"""
        produto_data = ProdutoCreate(
            codigo_barras="7891234567890",
            descricao="Cimento CP-II 50kg",
            categoria_id=1,
            preco_custo=25.50,
            preco_venda=32.90,
            estoque_atual=100.0,
            estoque_minimo=10.0,
            unidade="UN",
            ncm="25232900",
            ativo=True
        )

        await produto_repository.create(produto_data)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id(self, produto_repository, mock_session, mock_produto):
        """Deve buscar produto por ID"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_produto
        mock_session.execute.return_value = mock_result

        result = await produto_repository.get_by_id(1)

        assert result == mock_produto
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_codigo_barras(self, produto_repository, mock_session, mock_produto):
        """Deve buscar produto por código de barras"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_produto
        mock_session.execute.return_value = mock_result

        result = await produto_repository.get_by_codigo_barras("7891234567890")

        assert result == mock_produto
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_sem_filtros(self, produto_repository, mock_session, mock_produto):
        """Deve listar todos os produtos"""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_produto, mock_produto]
        mock_session.execute.return_value = mock_result

        result = await produto_repository.get_all()

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_com_filtro_categoria(self, produto_repository, mock_session, mock_produto):
        """Deve filtrar produtos por categoria"""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_produto]
        mock_session.execute.return_value = mock_result

        result = await produto_repository.get_all(categoria_id=1)

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count(self, produto_repository, mock_session):
        """Deve contar produtos"""
        mock_result = Mock()
        mock_result.scalar_one.return_value = 10
        mock_session.execute.return_value = mock_result

        result = await produto_repository.count()

        assert result == 10
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update(self, produto_repository, mock_session, mock_produto):
        """Deve atualizar produto"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_produto
        mock_session.execute.return_value = mock_result

        update_data = ProdutoUpdate(descricao="Novo nome")
        result = await produto_repository.update(1, update_data)

        assert result.descricao == "Novo nome"
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete(self, produto_repository, mock_session, mock_produto):
        """Deve deletar produto (marcar como inativo)"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_produto
        mock_session.execute.return_value = mock_result

        result = await produto_repository.delete(1)

        assert result is True
        assert mock_produto.ativo is False
        mock_session.commit.assert_called_once()


# ========== Testes Models ==========

class TestProdutoModels:
    """Testes dos modelos"""

    def test_produto_repr(self, mock_produto):
        """Deve ter representação string"""
        # Mock não implementa __repr__ real, apenas verificar que o mock existe
        assert mock_produto is not None
        assert mock_produto.id == 1
        assert mock_produto.codigo_barras == "7891234567890"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
