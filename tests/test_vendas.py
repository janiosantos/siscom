"""
Testes do módulo vendas

Testa:
- vendas/service.py - Lógica de negócio
- vendas/repository.py - Acesso a dados
- vendas/models.py - Modelos
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.modules.vendas.service import VendasService
from app.modules.vendas.repository import VendaRepository
from app.modules.vendas.models import Venda, ItemVenda, StatusVenda
from app.modules.vendas.schemas import (
    VendaCreate,
    VendaUpdate,
    ItemVendaCreate,
    StatusVendaEnum,
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


# ========== Fixtures ==========

@pytest.fixture
def mock_session():
    """Mock do AsyncSession"""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.add = Mock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def venda_repository(mock_session):
    """Repository com session mockada"""
    return VendaRepository(mock_session)


@pytest.fixture
def vendas_service(mock_session):
    """Service com dependencies mockadas"""
    service = VendasService(mock_session)

    # Mock repositories
    service.produto_repository = AsyncMock()
    service.estoque_service = AsyncMock()
    service.repository = AsyncMock()

    return service


@pytest.fixture
def mock_produto():
    """Mock de produto"""
    produto = Mock()
    produto.id = 1
    produto.descricao = "Cimento CP-II 50kg"
    produto.ativo = True
    produto.preco_venda = Decimal("32.90")
    return produto


@pytest.fixture
def mock_venda():
    """Mock de venda"""
    venda = Mock(spec=Venda)
    venda.id = 1
    venda.cliente_id = 10
    venda.vendedor_id = 5
    venda.data_venda = datetime.utcnow()
    venda.subtotal = Decimal("100.00")
    venda.desconto = Decimal("10.00")
    venda.valor_total = Decimal("90.00")
    venda.forma_pagamento = "DINHEIRO"
    venda.status = StatusVenda.PENDENTE
    venda.observacoes = "Teste"
    venda.itens = []
    venda.created_at = datetime.utcnow()
    venda.updated_at = datetime.utcnow()
    return venda


# ========== Testes VendasService - Criar Venda ==========

class TestVendasServiceCriarVenda:
    """Testes de criação de venda"""

    @pytest.mark.asyncio
    async def test_criar_venda_produto_inexistente(self, vendas_service):
        """Deve falhar se produto não existe"""
        # Mock produto repository retornando None
        vendas_service.produto_repository.get_by_id.return_value = None

        venda_data = VendaCreate(
            vendedor_id=1,
            forma_pagamento="CARTAO",
            desconto=0.0,
            itens=[
                ItemVendaCreate(
                    produto_id=999,  # Produto inexistente
                    quantidade=1.0,
                    preco_unitario=10.0,
                    desconto_item=0.0
                )
            ]
        )

        with pytest.raises(NotFoundException, match="Produto 999 não encontrado"):
            await vendas_service.criar_venda(venda_data)

    @pytest.mark.asyncio
    async def test_criar_venda_produto_inativo(self, vendas_service, mock_produto):
        """Deve falhar se produto está inativo"""
        # Produto inativo
        mock_produto.ativo = False
        vendas_service.produto_repository.get_by_id.return_value = mock_produto

        venda_data = VendaCreate(
            vendedor_id=1,
            forma_pagamento="DINHEIRO",
            desconto=0.0,
            itens=[
                ItemVendaCreate(
                    produto_id=1,
                    quantidade=2.0,
                    preco_unitario=32.90,
                    desconto_item=0.0
                )
            ]
        )

        with pytest.raises(ValidationException, match="está inativo"):
            await vendas_service.criar_venda(venda_data)

    @pytest.mark.asyncio
    async def test_criar_venda_desconto_maior_que_subtotal(self, vendas_service, mock_produto, mock_venda):
        """Deve falhar se desconto > subtotal"""
        vendas_service.produto_repository.get_by_id.return_value = mock_produto
        vendas_service.estoque_service.validar_estoque_suficiente.return_value = None
        vendas_service.repository.create_venda.return_value = mock_venda
        vendas_service.repository.create_item_venda.return_value = Mock()
        vendas_service.estoque_service.saida_estoque.return_value = None

        venda_data = VendaCreate(
            vendedor_id=1,
            forma_pagamento="DINHEIRO",
            desconto=200.0,  # Desconto maior que subtotal
            itens=[
                ItemVendaCreate(
                    produto_id=1,
                    quantidade=1.0,
                    preco_unitario=100.0,
                    desconto_item=0.0
                )
            ]
        )

        with pytest.raises(ValidationException, match="Desconto não pode ser maior"):
            await vendas_service.criar_venda(venda_data)

    @pytest.mark.asyncio
    async def test_criar_venda_sucesso(self, vendas_service, mock_produto, mock_venda):
        """Deve criar venda com sucesso"""
        # Setup mocks
        vendas_service.produto_repository.get_by_id.return_value = mock_produto
        vendas_service.estoque_service.validar_estoque_suficiente.return_value = None
        vendas_service.repository.create_venda.return_value = mock_venda
        vendas_service.repository.create_item_venda.return_value = Mock()
        vendas_service.estoque_service.saida_estoque.return_value = None
        vendas_service.repository.get_by_id.return_value = mock_venda

        venda_data = VendaCreate(
            vendedor_id=1,
            forma_pagamento="CARTAO",
            desconto=5.0,
            itens=[
                ItemVendaCreate(
                    produto_id=1,
                    quantidade=2.0,
                    preco_unitario=50.0,
                    desconto_item=0.0
                )
            ]
        )

        result = await vendas_service.criar_venda(venda_data)

        # Verificar chamadas
        vendas_service.produto_repository.get_by_id.assert_called_once_with(1)
        vendas_service.estoque_service.validar_estoque_suficiente.assert_called_once()
        vendas_service.repository.create_venda.assert_called_once()
        vendas_service.estoque_service.saida_estoque.assert_called_once()

    @pytest.mark.asyncio
    async def test_criar_venda_multiplos_itens(self, vendas_service, mock_produto, mock_venda):
        """Deve criar venda com múltiplos itens"""
        vendas_service.produto_repository.get_by_id.return_value = mock_produto
        vendas_service.estoque_service.validar_estoque_suficiente.return_value = None
        vendas_service.repository.create_venda.return_value = mock_venda
        vendas_service.repository.create_item_venda.return_value = Mock()
        vendas_service.estoque_service.saida_estoque.return_value = None
        vendas_service.repository.get_by_id.return_value = mock_venda

        venda_data = VendaCreate(
            vendedor_id=1,
            forma_pagamento="PIX",
            desconto=0.0,
            itens=[
                ItemVendaCreate(produto_id=1, quantidade=2.0, preco_unitario=50.0, desconto_item=0.0),
                ItemVendaCreate(produto_id=1, quantidade=1.0, preco_unitario=30.0, desconto_item=5.0),
                ItemVendaCreate(produto_id=1, quantidade=3.0, preco_unitario=20.0, desconto_item=0.0),
            ]
        )

        await vendas_service.criar_venda(venda_data)

        # Verificar que criou 3 itens
        assert vendas_service.repository.create_item_venda.call_count == 3

        # Verificar que registrou 3 saídas de estoque
        assert vendas_service.estoque_service.saida_estoque.call_count == 3


# ========== Testes VendasService - Finalizar Venda ==========

class TestVendasServiceFinalizarVenda:
    """Testes de finalização de venda"""

    @pytest.mark.asyncio
    async def test_finalizar_venda_inexistente(self, vendas_service):
        """Deve falhar ao finalizar venda inexistente"""
        vendas_service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundException, match="não encontrada"):
            await vendas_service.finalizar_venda(999)

    @pytest.mark.asyncio
    async def test_finalizar_venda_ja_finalizada(self, vendas_service, mock_venda):
        """Deve falhar ao finalizar venda já finalizada"""
        mock_venda.status = StatusVenda.FINALIZADA
        vendas_service.repository.get_by_id.return_value = mock_venda

        with pytest.raises(BusinessRuleException, match="não pode ser finalizada"):
            await vendas_service.finalizar_venda(1)

    @pytest.mark.asyncio
    async def test_finalizar_venda_cancelada(self, vendas_service, mock_venda):
        """Deve falhar ao finalizar venda cancelada"""
        mock_venda.status = StatusVenda.CANCELADA
        vendas_service.repository.get_by_id.return_value = mock_venda

        with pytest.raises(BusinessRuleException, match="não pode ser finalizada"):
            await vendas_service.finalizar_venda(1)

    @pytest.mark.asyncio
    async def test_finalizar_venda_sucesso(self, vendas_service, mock_venda):
        """Deve finalizar venda com sucesso"""
        mock_venda.status = StatusVenda.PENDENTE
        mock_venda_finalizada = Mock(spec=Venda)
        mock_venda_finalizada.status = StatusVenda.FINALIZADA

        vendas_service.repository.get_by_id.return_value = mock_venda
        vendas_service.repository.finalizar_venda.return_value = mock_venda_finalizada

        result = await vendas_service.finalizar_venda(1)

        vendas_service.repository.finalizar_venda.assert_called_once_with(1)


# ========== Testes VendasService - Cancelar Venda ==========

class TestVendasServiceCancelarVenda:
    """Testes de cancelamento de venda"""

    @pytest.mark.asyncio
    async def test_cancelar_venda_inexistente(self, vendas_service):
        """Deve falhar ao cancelar venda inexistente"""
        vendas_service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await vendas_service.cancelar_venda(999)

    @pytest.mark.asyncio
    async def test_cancelar_venda_ja_cancelada(self, vendas_service, mock_venda):
        """Deve falhar ao cancelar venda já cancelada"""
        mock_venda.status = StatusVenda.CANCELADA
        vendas_service.repository.get_by_id.return_value = mock_venda

        with pytest.raises(BusinessRuleException, match="já está cancelada"):
            await vendas_service.cancelar_venda(1)

    @pytest.mark.asyncio
    async def test_cancelar_venda_devolve_estoque(self, vendas_service, mock_venda):
        """Deve devolver estoque ao cancelar venda"""
        # Setup venda com itens
        mock_item1 = Mock()
        mock_item1.produto_id = 1
        mock_item1.quantidade = 2.0
        mock_item1.preco_unitario = 50.0

        mock_item2 = Mock()
        mock_item2.produto_id = 2
        mock_item2.quantidade = 1.0
        mock_item2.preco_unitario = 30.0

        mock_venda.status = StatusVenda.FINALIZADA
        mock_venda.itens = [mock_item1, mock_item2]
        mock_venda.vendedor_id = 5

        vendas_service.repository.get_by_id.return_value = mock_venda
        vendas_service.estoque_service.ajuste_estoque.return_value = None
        vendas_service.repository.cancelar_venda.return_value = mock_venda

        await vendas_service.cancelar_venda(1)

        # Verificar que ajuste_estoque foi chamado 2 vezes (um para cada item)
        assert vendas_service.estoque_service.ajuste_estoque.call_count == 2


# ========== Testes VendasService - Listar e Buscar ==========

class TestVendasServiceListarBuscar:
    """Testes de listagem e busca"""

    @pytest.mark.asyncio
    async def test_get_venda_inexistente(self, vendas_service):
        """Deve falhar ao buscar venda inexistente"""
        vendas_service.repository.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await vendas_service.get_venda(999)

    @pytest.mark.asyncio
    async def test_get_venda_sucesso(self, vendas_service, mock_venda):
        """Deve buscar venda com sucesso"""
        vendas_service.repository.get_by_id.return_value = mock_venda

        result = await vendas_service.get_venda(1)

        vendas_service.repository.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_vendas_paginacao(self, vendas_service, mock_venda):
        """Deve listar vendas com paginação"""
        vendas = [mock_venda, mock_venda]
        vendas_service.repository.get_all.return_value = vendas
        vendas_service.repository.count.return_value = 25

        result = await vendas_service.list_vendas(page=2, page_size=10)

        # Verificar skip correto (page 2 = skip 10)
        call_args = vendas_service.repository.get_all.call_args
        assert call_args[1]["skip"] == 10
        assert call_args[1]["limit"] == 10

        # Verificar cálculo de páginas
        assert result.pages == 3  # 25 vendas / 10 por página = 3 páginas

    @pytest.mark.asyncio
    async def test_list_vendas_filtros(self, vendas_service, mock_venda):
        """Deve listar vendas com filtros"""
        vendas_service.repository.get_all.return_value = [mock_venda]
        vendas_service.repository.count.return_value = 1

        data_inicio = datetime(2025, 1, 1)
        data_fim = datetime(2025, 1, 31)

        await vendas_service.list_vendas(
            status=StatusVendaEnum.FINALIZADA,
            cliente_id=10,
            vendedor_id=5,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        # Verificar que filtros foram passados
        call_args = vendas_service.repository.get_all.call_args
        assert call_args[1]["status"] == StatusVenda.FINALIZADA
        assert call_args[1]["cliente_id"] == 10
        assert call_args[1]["vendedor_id"] == 5

    @pytest.mark.asyncio
    async def test_list_vendas_page_size_invalido(self, vendas_service):
        """Deve ajustar page_size inválido"""
        vendas_service.repository.get_all.return_value = []
        vendas_service.repository.count.return_value = 0

        # Page size muito grande
        await vendas_service.list_vendas(page_size=500)
        call_args = vendas_service.repository.get_all.call_args
        assert call_args[1]["limit"] == 50  # Deve usar padrão

        # Page size negativo
        await vendas_service.list_vendas(page_size=-10)
        call_args = vendas_service.repository.get_all.call_args
        assert call_args[1]["limit"] == 50

    @pytest.mark.asyncio
    async def test_list_vendas_page_invalida(self, vendas_service):
        """Deve ajustar page inválida"""
        vendas_service.repository.get_all.return_value = []
        vendas_service.repository.count.return_value = 0

        # Page zero ou negativa
        await vendas_service.list_vendas(page=0)
        call_args = vendas_service.repository.get_all.call_args
        assert call_args[1]["skip"] == 0  # Deve usar page 1

    @pytest.mark.asyncio
    async def test_get_vendas_periodo(self, vendas_service, mock_venda):
        """Deve buscar vendas por período"""
        vendas_service.repository.get_vendas_periodo.return_value = [mock_venda]
        vendas_service.repository.count.return_value = 1

        data_inicio = datetime(2025, 1, 1)
        data_fim = datetime(2025, 1, 31)

        result = await vendas_service.get_vendas_periodo(data_inicio, data_fim)

        vendas_service.repository.get_vendas_periodo.assert_called_once()
        assert result.total == 1

    @pytest.mark.asyncio
    async def test_get_total_vendas_periodo(self, vendas_service):
        """Deve calcular total de vendas por período"""
        vendas_service.repository.get_total_vendas_periodo.return_value = 1500.50

        data_inicio = datetime(2025, 1, 1)
        data_fim = datetime(2025, 1, 31)

        total = await vendas_service.get_total_vendas_periodo(
            data_inicio,
            data_fim,
            status=StatusVendaEnum.FINALIZADA
        )

        assert total == 1500.50
        vendas_service.repository.get_total_vendas_periodo.assert_called_once()


# ========== Testes VendaRepository ==========

class TestVendaRepository:
    """Testes do repository de vendas"""

    @pytest.mark.asyncio
    async def test_create_venda(self, venda_repository, mock_session):
        """Deve criar venda"""
        venda_data = VendaCreate(
            vendedor_id=1,
            forma_pagamento="DINHEIRO",
            desconto=0.0,
            itens=[]
        )

        mock_venda = Mock(spec=Venda)
        mock_session.refresh = AsyncMock(side_effect=lambda x: setattr(x, 'id', 1))

        await venda_repository.create_venda(venda_data)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_item_venda(self, venda_repository, mock_session):
        """Deve criar item de venda"""
        item_data = ItemVendaCreate(
            produto_id=1,
            quantidade=2.0,
            preco_unitario=50.0,
            desconto_item=0.0
        )

        await venda_repository.create_item_venda(
            venda_id=1,
            item_data=item_data,
            subtotal=100.0,
            total=100.0
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id(self, venda_repository, mock_session, mock_venda):
        """Deve buscar venda por ID"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_venda
        mock_session.execute.return_value = mock_result

        result = await venda_repository.get_by_id(1)

        assert result == mock_venda
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_nao_encontrada(self, venda_repository, mock_session):
        """Deve retornar None se venda não existe"""
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await venda_repository.get_by_id(999)

        assert result is None


# ========== Testes Models ==========

class TestVendaModels:
    """Testes dos modelos"""

    def test_status_venda_enum(self):
        """Deve ter todos os status"""
        assert StatusVenda.PENDENTE.value == "PENDENTE"
        assert StatusVenda.FINALIZADA.value == "FINALIZADA"
        assert StatusVenda.CANCELADA.value == "CANCELADA"

    def test_venda_repr(self, mock_venda):
        """Deve ter representação string"""
        repr_str = repr(mock_venda)
        assert "Venda" in repr_str
        assert str(mock_venda.id) in repr_str


# ========== Testes de Integração ==========

class TestVendasIntegration:
    """Testes de integração entre componentes"""

    @pytest.mark.asyncio
    async def test_fluxo_completo_venda(self, vendas_service, mock_produto, mock_venda):
        """Teste de fluxo completo: criar → finalizar → cancelar"""
        # Setup mocks para criar
        vendas_service.produto_repository.get_by_id.return_value = mock_produto
        vendas_service.estoque_service.validar_estoque_suficiente.return_value = None
        vendas_service.repository.create_venda.return_value = mock_venda
        vendas_service.repository.create_item_venda.return_value = Mock()
        vendas_service.estoque_service.saida_estoque.return_value = None
        vendas_service.repository.get_by_id.return_value = mock_venda

        # 1. Criar venda
        venda_data = VendaCreate(
            vendedor_id=1,
            forma_pagamento="CARTAO",
            desconto=0.0,
            itens=[
                ItemVendaCreate(
                    produto_id=1,
                    quantidade=1.0,
                    preco_unitario=50.0,
                    desconto_item=0.0
                )
            ]
        )

        venda_criada = await vendas_service.criar_venda(venda_data)

        # 2. Finalizar venda
        mock_venda.status = StatusVenda.PENDENTE
        mock_venda_finalizada = Mock()
        mock_venda_finalizada.status = StatusVenda.FINALIZADA
        vendas_service.repository.finalizar_venda.return_value = mock_venda_finalizada

        await vendas_service.finalizar_venda(mock_venda.id)

        # 3. Cancelar venda
        mock_venda.status = StatusVenda.FINALIZADA
        mock_venda.itens = [Mock(produto_id=1, quantidade=1.0, preco_unitario=50.0)]
        vendas_service.repository.cancelar_venda.return_value = mock_venda
        vendas_service.estoque_service.ajuste_estoque.return_value = None

        await vendas_service.cancelar_venda(mock_venda.id)

        # Verificar que todas as operações foram chamadas
        assert vendas_service.repository.create_venda.called
        assert vendas_service.repository.finalizar_venda.called
        assert vendas_service.repository.cancelar_venda.called
        assert vendas_service.estoque_service.ajuste_estoque.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
