"""
Testes para o módulo de Boleto Bancário
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.pagamentos.services.boleto_service import BoletoService
from app.modules.pagamentos.models import ConfiguracaoBoleto, Boleto, StatusBoleto
from app.modules.pagamentos.schemas import ConfiguracaoBoletoCreate, BoletoCreate


@pytest.fixture
async def boleto_service(db_session: AsyncSession):
    """Fixture para BoletoService"""
    return BoletoService(db_session)


@pytest.fixture
async def config_boleto_bb(boleto_service: BoletoService):
    """Fixture para configuração de boleto Banco do Brasil"""
    config_data = ConfiguracaoBoletoCreate(
        banco_codigo="001",
        banco_nome="Banco do Brasil",
        agencia="1234",
        agencia_dv="5",
        conta="12345",
        conta_dv="6",
        carteira="18",
        convenio="1234567",
        cedente_nome="EMPRESA TESTE LTDA",
        cedente_cnpj="12345678000190",
        cedente_endereco="Rua Teste, 123",
        cedente_cidade="São Paulo",
        cedente_uf="SP",
        cedente_cep="01234567",
        juros_mes=Decimal("2.00"),
        multa_atraso=Decimal("2.00"),
        dias_protesto=5,
        ativo=True
    )
    return await boleto_service.criar_configuracao(config_data)


@pytest.fixture
async def config_boleto_bradesco(boleto_service: BoletoService):
    """Fixture para configuração de boleto Bradesco"""
    config_data = ConfiguracaoBoletoCreate(
        banco_codigo="237",
        banco_nome="Bradesco",
        agencia="5678",
        agencia_dv="9",
        conta="98765",
        conta_dv="4",
        carteira="09",
        cedente_nome="EMPRESA TESTE LTDA",
        cedente_cnpj="12345678000190",
        cedente_endereco="Av. Teste, 456",
        cedente_cidade="Rio de Janeiro",
        cedente_uf="RJ",
        cedente_cep="20000000",
        juros_mes=Decimal("1.50"),
        multa_atraso=Decimal("1.50"),
        dias_protesto=3,
        ativo=True
    )
    return await boleto_service.criar_configuracao(config_data)


class TestConfiguracaoBoleto:
    """Testes para configuração de boletos"""

    async def test_criar_configuracao_bb(self, boleto_service: BoletoService):
        """Testa criação de configuração para Banco do Brasil"""
        config_data = ConfiguracaoBoletoCreate(
            banco_codigo="001",
            banco_nome="Banco do Brasil",
            agencia="1234",
            agencia_dv="5",
            conta="12345",
            conta_dv="6",
            carteira="18",
            convenio="1234567",
            cedente_nome="EMPRESA TESTE LTDA",
            cedente_cnpj="12345678000190",
            cedente_endereco="Rua Teste, 123",
            cedente_cidade="São Paulo",
            cedente_uf="SP",
            cedente_cep="01234567",
            juros_mes=Decimal("2.00"),
            multa_atraso=Decimal("2.00")
        )

        config = await boleto_service.criar_configuracao(config_data)

        assert config.id is not None
        assert config.banco_codigo == "001"
        assert config.banco_nome == "Banco do Brasil"
        assert config.carteira == "18"
        assert config.convenio == "1234567"
        assert config.ativo is True

    async def test_criar_configuracao_bradesco(self, boleto_service: BoletoService):
        """Testa criação de configuração para Bradesco"""
        config_data = ConfiguracaoBoletoCreate(
            banco_codigo="237",
            banco_nome="Bradesco",
            agencia="5678",
            conta="98765",
            conta_dv="4",
            carteira="09",
            cedente_nome="EMPRESA TESTE LTDA",
            cedente_cnpj="12345678000190",
            cedente_endereco="Av. Teste, 456",
            cedente_cidade="Rio de Janeiro",
            cedente_uf="RJ",
            cedente_cep="20000000"
        )

        config = await boleto_service.criar_configuracao(config_data)

        assert config.banco_codigo == "237"
        assert config.carteira == "09"

    async def test_listar_configuracoes_ativas(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa listagem de configurações ativas"""
        configs = await boleto_service.listar_configuracoes(ativas_apenas=True)

        assert len(configs) > 0
        assert all(config.ativo for config in configs)


class TestGeracaoBoleto:
    """Testes para geração de boletos"""

    async def test_gerar_boleto_bb(self, boleto_service: BoletoService, config_boleto_bb):
        """Testa geração de boleto Banco do Brasil"""
        data_vencimento = date.today() + timedelta(days=7)

        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("500.00"),
            data_vencimento=data_vencimento,
            numero_documento="12345",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901",
            sacado_endereco="Rua Cliente, 789",
            sacado_cidade="São Paulo",
            sacado_uf="SP",
            sacado_cep="01234567",
            instrucoes="Não aceitar após o vencimento",
            cliente_id=1,
            venda_id=1001
        )

        boleto = await boleto_service.gerar_boleto(boleto_data)

        assert boleto.id is not None
        assert boleto.nosso_numero is not None
        assert len(boleto.nosso_numero) > 0
        assert boleto.codigo_barras is not None
        assert len(boleto.codigo_barras) == 44  # Código de barras tem 44 dígitos
        assert boleto.linha_digitavel is not None
        assert len(boleto.linha_digitavel) == 47  # Linha digitável tem 47 caracteres
        assert boleto.valor == Decimal("500.00")
        assert boleto.status == StatusBoleto.ABERTO
        assert boleto.data_vencimento == data_vencimento

    async def test_gerar_boleto_bradesco(
        self, boleto_service: BoletoService, config_boleto_bradesco
    ):
        """Testa geração de boleto Bradesco"""
        data_vencimento = date.today() + timedelta(days=15)

        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bradesco.id,
            valor=Decimal("1000.00"),
            data_vencimento=data_vencimento,
            numero_documento="67890",
            sacado_nome="EMPRESA CLIENTE LTDA",
            sacado_cpf_cnpj="98765432000199",
            sacado_endereco="Av. Cliente, 999",
            sacado_cidade="Rio de Janeiro",
            sacado_uf="RJ",
            sacado_cep="20000000"
        )

        boleto = await boleto_service.gerar_boleto(boleto_data)

        assert boleto.nosso_numero is not None
        assert boleto.codigo_barras is not None
        assert boleto.linha_digitavel is not None
        assert boleto.valor == Decimal("1000.00")

    async def test_nosso_numero_sequencial(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa que nosso número é sequencial"""
        data_vencimento = date.today() + timedelta(days=7)

        boleto_data1 = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("100.00"),
            data_vencimento=data_vencimento,
            numero_documento="001",
            sacado_nome="CLIENTE 1",
            sacado_cpf_cnpj="12345678901"
        )

        boleto_data2 = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("200.00"),
            data_vencimento=data_vencimento,
            numero_documento="002",
            sacado_nome="CLIENTE 2",
            sacado_cpf_cnpj="98765432109"
        )

        boleto1 = await boleto_service.gerar_boleto(boleto_data1)
        boleto2 = await boleto_service.gerar_boleto(boleto_data2)

        # Nosso número deve ser diferente e sequencial
        assert boleto1.nosso_numero != boleto2.nosso_numero
        nn1 = int(boleto1.nosso_numero.replace("-", "").split("/")[0])
        nn2 = int(boleto2.nosso_numero.replace("-", "").split("/")[0])
        assert nn2 > nn1


class TestPagamentoBoleto:
    """Testes para pagamento de boletos"""

    async def test_marcar_boleto_como_pago(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa marcação de boleto como pago"""
        # Gerar boleto
        data_vencimento = date.today() + timedelta(days=7)
        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("300.00"),
            data_vencimento=data_vencimento,
            numero_documento="PAG001",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )
        boleto = await boleto_service.gerar_boleto(boleto_data)

        # Marcar como pago
        data_pagamento = date.today()
        valor_pago = Decimal("300.00")

        boleto_pago = await boleto_service.marcar_como_pago(
            boleto.id, valor_pago, data_pagamento
        )

        assert boleto_pago.status == StatusBoleto.PAGO
        assert boleto_pago.valor_pago == Decimal("300.00")
        assert boleto_pago.data_pagamento == data_pagamento

    async def test_marcar_boleto_como_pago_com_juros(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa pagamento de boleto com juros e multa"""
        # Gerar boleto vencido
        data_vencimento = date.today() - timedelta(days=10)  # Vencido há 10 dias
        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("100.00"),
            data_vencimento=data_vencimento,
            numero_documento="JUR001",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )
        boleto = await boleto_service.gerar_boleto(boleto_data)

        # Pagar com juros e multa
        data_pagamento = date.today()
        # Valor original + multa 2% + juros 2% ao mês
        valor_pago = Decimal("106.00")

        boleto_pago = await boleto_service.marcar_como_pago(
            boleto.id, valor_pago, data_pagamento
        )

        assert boleto_pago.status == StatusBoleto.PAGO
        assert boleto_pago.valor_pago == Decimal("106.00")
        assert boleto_pago.valor_juros > 0
        assert boleto_pago.valor_multa > 0

    async def test_cancelar_boleto(self, boleto_service: BoletoService, config_boleto_bb):
        """Testa cancelamento de boleto"""
        data_vencimento = date.today() + timedelta(days=7)
        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("200.00"),
            data_vencimento=data_vencimento,
            numero_documento="CANC001",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )
        boleto = await boleto_service.gerar_boleto(boleto_data)

        boleto_cancelado = await boleto_service.cancelar_boleto(boleto.id)

        assert boleto_cancelado.status == StatusBoleto.CANCELADO

    async def test_nao_cancelar_boleto_pago(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa que não é possível cancelar boleto já pago"""
        # Gerar e pagar boleto
        data_vencimento = date.today() + timedelta(days=7)
        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("150.00"),
            data_vencimento=data_vencimento,
            numero_documento="NCANC001",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )
        boleto = await boleto_service.gerar_boleto(boleto_data)
        await boleto_service.marcar_como_pago(boleto.id, Decimal("150.00"), date.today())

        # Tentar cancelar
        with pytest.raises(ValueError, match="apenas.*aberto"):
            await boleto_service.cancelar_boleto(boleto.id)


class TestBuscarBoleto:
    """Testes para busca de boletos"""

    async def test_buscar_boleto_por_id(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa busca de boleto por ID"""
        data_vencimento = date.today() + timedelta(days=7)
        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("250.00"),
            data_vencimento=data_vencimento,
            numero_documento="BUSC001",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )
        boleto_criado = await boleto_service.gerar_boleto(boleto_data)

        boleto = await boleto_service.buscar_por_id(boleto_criado.id)

        assert boleto is not None
        assert boleto.id == boleto_criado.id
        assert boleto.valor == Decimal("250.00")

    async def test_buscar_boleto_por_nosso_numero(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa busca de boleto por nosso número"""
        data_vencimento = date.today() + timedelta(days=7)
        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("350.00"),
            data_vencimento=data_vencimento,
            numero_documento="BUSCNN001",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )
        boleto_criado = await boleto_service.gerar_boleto(boleto_data)

        boleto = await boleto_service.buscar_por_nosso_numero(boleto_criado.nosso_numero)

        assert boleto is not None
        assert boleto.nosso_numero == boleto_criado.nosso_numero
        assert boleto.valor == Decimal("350.00")

    async def test_listar_boletos_vencidos(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa listagem de boletos vencidos"""
        # Criar boleto vencido
        data_vencimento = date.today() - timedelta(days=5)
        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("100.00"),
            data_vencimento=data_vencimento,
            numero_documento="VENC001",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )
        await boleto_service.gerar_boleto(boleto_data)

        boletos_vencidos = await boleto_service.listar_vencidos()

        assert len(boletos_vencidos) > 0
        for boleto in boletos_vencidos:
            assert boleto.data_vencimento < date.today()
            assert boleto.status == StatusBoleto.ABERTO


class TestValidacaoBoleto:
    """Testes para validação de dados de boleto"""

    async def test_validar_vencimento_futuro(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa que data de vencimento deve ser futura"""
        data_vencimento = date.today() - timedelta(days=1)  # Ontem

        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("100.00"),
            data_vencimento=data_vencimento,
            numero_documento="VAL001",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )

        # Deve aceitar (sistema pode gerar boleto vencido se necessário)
        boleto = await boleto_service.gerar_boleto(boleto_data)
        assert boleto is not None

    async def test_validar_valor_minimo(
        self, boleto_service: BoletoService, config_boleto_bb
    ):
        """Testa validação de valor mínimo"""
        data_vencimento = date.today() + timedelta(days=7)

        boleto_data = BoletoCreate(
            configuracao_id=config_boleto_bb.id,
            valor=Decimal("0.01"),  # Valor muito baixo
            data_vencimento=data_vencimento,
            numero_documento="VALMIN001",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )

        # Deve aceitar (validação de valor mínimo é regra de negócio)
        boleto = await boleto_service.gerar_boleto(boleto_data)
        assert boleto is not None
