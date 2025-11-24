"""
Testes para o módulo de Conciliação Bancária
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.pagamentos.services.conciliacao_service import ConciliacaoService
from app.modules.pagamentos.services.pix_service import PixService
from app.modules.pagamentos.services.boleto_service import BoletoService
from app.modules.pagamentos.models import ExtratoBancario
from app.modules.pagamentos.schemas import ImportCSVRequest


@pytest.fixture
async def conciliacao_service(db_session: AsyncSession):
    """Fixture para ConciliacaoService"""
    return ConciliacaoService(db_session)


@pytest.fixture
async def pix_service(db_session: AsyncSession):
    """Fixture para PixService"""
    return PixService(db_session)


@pytest.fixture
async def boleto_service(db_session: AsyncSession):
    """Fixture para BoletoService"""
    return BoletoService(db_session)


@pytest.fixture
def extrato_csv_content():
    """Fixture com conteúdo CSV de extrato bancário"""
    return """data,descricao,documento,valor,tipo
2024-01-15,PIX RECEBIDO,E12345678202401151200ABC123456789,150.00,C
2024-01-16,BOLETO PAGO,00012345678901234567,500.00,C
2024-01-17,PIX RECEBIDO,E98765432202401171400XYZ987654321,200.50,C
2024-01-18,TARIFA BANCARIA,,5.00,D
2024-01-19,BOLETO PAGO,00098765432109876543,1000.00,C
"""


class TestImportCSV:
    """Testes para importação de extrato CSV"""

    async def test_importar_csv_valido(
        self, conciliacao_service: ConciliacaoService, extrato_csv_content
    ):
        """Testa importação de CSV válido"""
        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=extrato_csv_content
        )

        resultado = await conciliacao_service.importar_extrato_csv(import_data)

        assert resultado["sucesso"] == 5
        assert resultado["erros"] == 0
        assert resultado["total"] == 5

    async def test_importar_csv_com_campos_opcionais(
        self, conciliacao_service: ConciliacaoService
    ):
        """Testa importação de CSV com campos opcionais"""
        csv_content = """data,descricao,documento,valor,tipo,saldo
2024-01-15,PIX RECEBIDO,E12345678202401151200ABC123456789,150.00,C,1500.00
2024-01-16,BOLETO PAGO,00012345678901234567,500.00,C,2000.00
"""

        import_data = ImportCSVRequest(
            banco_codigo="237",
            agencia="5678",
            conta="98765-4",
            conteudo_csv=csv_content
        )

        resultado = await conciliacao_service.importar_extrato_csv(import_data)

        assert resultado["sucesso"] == 2
        assert resultado["total"] == 2

    async def test_importar_csv_com_erros(
        self, conciliacao_service: ConciliacaoService
    ):
        """Testa importação de CSV com linhas inválidas"""
        csv_content = """data,descricao,documento,valor,tipo
2024-01-15,PIX RECEBIDO,E12345678202401151200ABC123456789,150.00,C
invalido,ERRO,DOC123,ABC,C
2024-01-17,PIX VALIDO,E98765432202401171400XYZ987654321,200.50,C
"""

        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=csv_content
        )

        resultado = await conciliacao_service.importar_extrato_csv(import_data)

        assert resultado["sucesso"] == 2
        assert resultado["erros"] == 1
        assert resultado["total"] == 3

    async def test_importar_csv_vazio(self, conciliacao_service: ConciliacaoService):
        """Testa importação de CSV vazio"""
        csv_content = """data,descricao,documento,valor,tipo
"""

        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=csv_content
        )

        resultado = await conciliacao_service.importar_extrato_csv(import_data)

        assert resultado["total"] == 0
        assert resultado["sucesso"] == 0


class TestConciliacaoAutomatica:
    """Testes para conciliação automática"""

    async def test_conciliar_pix_por_e2e_id(
        self,
        conciliacao_service: ConciliacaoService,
        pix_service: PixService,
        db_session: AsyncSession
    ):
        """Testa conciliação automática de PIX por E2E ID"""
        # Criar chave PIX
        from app.modules.pagamentos.schemas import ChavePixCreate, TransacaoPixCreate
        from app.modules.pagamentos.models import TipoChavePix

        chave_data = ChavePixCreate(
            tipo=TipoChavePix.CNPJ,
            chave="12345678000190",
            banco="001",
            agencia="1234",
            conta="12345-6",
            tipo_conta="CORRENTE",
            nome_titular="EMPRESA TESTE LTDA"
        )
        chave = await pix_service.criar_chave_pix(chave_data)

        # Criar transação PIX
        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave.id,
            valor=Decimal("150.00"),
            descricao="Venda #1234"
        )
        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        # Simular pagamento via webhook
        from app.modules.pagamentos.schemas import WebhookPixPayload
        from datetime import datetime

        webhook_data = WebhookPixPayload(
            txid=transacao.txid,
            e2e_id="E12345678202401151200ABC123456789",
            valor_pago=Decimal("150.00"),
            data_pagamento=datetime.now(),
            psp="MERCADO_PAGO",
            status="APROVADO"
        )
        await pix_service.processar_webhook_pagamento(webhook_data)

        # Importar extrato com mesmo E2E ID
        csv_content = """data,descricao,documento,valor,tipo
2024-01-15,PIX RECEBIDO,E12345678202401151200ABC123456789,150.00,C
"""
        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=csv_content
        )
        await conciliacao_service.importar_extrato_csv(import_data)

        # Executar conciliação automática
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today() + timedelta(days=1)

        resultado = await conciliacao_service.conciliar_automaticamente(
            banco_codigo="001",
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        assert resultado["conciliados"] > 0
        assert resultado["conciliados_pix"] > 0

    async def test_conciliar_boleto_por_nosso_numero(
        self,
        conciliacao_service: ConciliacaoService,
        boleto_service: BoletoService
    ):
        """Testa conciliação automática de boleto por nosso número"""
        # Criar configuração de boleto
        from app.modules.pagamentos.schemas import ConfiguracaoBoletoCreate, BoletoCreate

        config_data = ConfiguracaoBoletoCreate(
            banco_codigo="001",
            banco_nome="Banco do Brasil",
            agencia="1234",
            conta="12345",
            conta_dv="6",
            carteira="18",
            convenio="1234567",
            cedente_nome="EMPRESA TESTE LTDA",
            cedente_cnpj="12345678000190",
            cedente_endereco="Rua Teste, 123",
            cedente_cidade="São Paulo",
            cedente_uf="SP",
            cedente_cep="01234567"
        )
        config = await boleto_service.criar_configuracao(config_data)

        # Gerar boleto
        data_vencimento = date.today() + timedelta(days=7)
        boleto_data = BoletoCreate(
            configuracao_id=config.id,
            valor=Decimal("500.00"),
            data_vencimento=data_vencimento,
            numero_documento="12345",
            sacado_nome="CLIENTE TESTE",
            sacado_cpf_cnpj="12345678901"
        )
        boleto = await boleto_service.gerar_boleto(boleto_data)

        # Importar extrato com nosso número
        # Extrair apenas números do nosso número para o documento
        nosso_numero_numeros = ''.join(filter(str.isdigit, boleto.nosso_numero))

        csv_content = f"""data,descricao,documento,valor,tipo
2024-01-16,BOLETO PAGO,{nosso_numero_numeros},500.00,C
"""
        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=csv_content
        )
        await conciliacao_service.importar_extrato_csv(import_data)

        # Executar conciliação automática
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today() + timedelta(days=1)

        resultado = await conciliacao_service.conciliar_automaticamente(
            banco_codigo="001",
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        assert resultado["conciliados"] > 0
        assert resultado["conciliados_boleto"] > 0

    async def test_tolerancia_valor(
        self,
        conciliacao_service: ConciliacaoService,
        pix_service: PixService
    ):
        """Testa tolerância de valor na conciliação (±R$0.01)"""
        # Criar chave e transação PIX
        from app.modules.pagamentos.schemas import ChavePixCreate, TransacaoPixCreate, WebhookPixPayload
        from app.modules.pagamentos.models import TipoChavePix
        from datetime import datetime

        chave_data = ChavePixCreate(
            tipo=TipoChavePix.CNPJ,
            chave="12345678000190",
            banco="001",
            agencia="1234",
            conta="12345-6",
            tipo_conta="CORRENTE",
            nome_titular="EMPRESA TESTE LTDA"
        )
        chave = await pix_service.criar_chave_pix(chave_data)

        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave.id,
            valor=Decimal("100.00"),
            descricao="Teste tolerância"
        )
        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        webhook_data = WebhookPixPayload(
            txid=transacao.txid,
            e2e_id="E12345678202401171400TOL123456789",
            valor_pago=Decimal("100.00"),
            data_pagamento=datetime.now(),
            psp="MERCADO_PAGO",
            status="APROVADO"
        )
        await pix_service.processar_webhook_pagamento(webhook_data)

        # Importar extrato com valor ligeiramente diferente (dentro da tolerância)
        csv_content = """data,descricao,documento,valor,tipo
2024-01-17,PIX RECEBIDO,E12345678202401171400TOL123456789,100.01,C
"""
        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=csv_content
        )
        await conciliacao_service.importar_extrato_csv(import_data)

        # Deve conciliar mesmo com diferença de R$0.01
        data_inicio = date.today() - timedelta(days=30)
        data_fim = date.today() + timedelta(days=1)

        resultado = await conciliacao_service.conciliar_automaticamente(
            banco_codigo="001",
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        assert resultado["conciliados"] > 0


class TestListarPendentes:
    """Testes para listagem de lançamentos pendentes"""

    async def test_listar_pendentes(
        self, conciliacao_service: ConciliacaoService, extrato_csv_content
    ):
        """Testa listagem de lançamentos pendentes de conciliação"""
        # Importar extrato
        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=extrato_csv_content
        )
        await conciliacao_service.importar_extrato_csv(import_data)

        # Listar pendentes
        pendentes = await conciliacao_service.listar_pendentes(
            banco_codigo="001",
            conta="12345-6"
        )

        # Todos devem estar pendentes (não há PIX/Boletos para conciliar)
        assert len(pendentes) > 0
        for lancamento in pendentes:
            assert lancamento.status_conciliacao == StatusConciliacao.PENDENTE

    async def test_listar_pendentes_por_periodo(
        self, conciliacao_service: ConciliacaoService
    ):
        """Testa listagem de pendentes por período"""
        # Importar extrato com datas específicas
        csv_content = """data,descricao,documento,valor,tipo
2024-01-01,LANCAMENTO ANTIGO,DOC001,100.00,C
2024-01-15,LANCAMENTO RECENTE,DOC002,200.00,C
2024-01-30,LANCAMENTO MUITO RECENTE,DOC003,300.00,C
"""
        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=csv_content
        )
        await conciliacao_service.importar_extrato_csv(import_data)

        # Listar apenas do período 15-31/01
        pendentes = await conciliacao_service.listar_pendentes(
            banco_codigo="001",
            conta="12345-6",
            data_inicio=date(2024, 1, 15),
            data_fim=date(2024, 1, 31)
        )

        # Deve retornar apenas os 2 lançamentos do período
        assert len(pendentes) >= 2


class TestConciliacaoManual:
    """Testes para conciliação manual"""

    async def test_conciliar_manualmente_com_pix(
        self,
        conciliacao_service: ConciliacaoService,
        pix_service: PixService
    ):
        """Testa conciliação manual de lançamento com PIX"""
        # Criar PIX
        from app.modules.pagamentos.schemas import ChavePixCreate, TransacaoPixCreate
        from app.modules.pagamentos.models import TipoChavePix

        chave_data = ChavePixCreate(
            tipo=TipoChavePix.CNPJ,
            chave="12345678000190",
            banco="001",
            agencia="1234",
            conta="12345-6",
            tipo_conta="CORRENTE",
            nome_titular="EMPRESA TESTE LTDA"
        )
        chave = await pix_service.criar_chave_pix(chave_data)

        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave.id,
            valor=Decimal("250.00"),
            descricao="Teste manual"
        )
        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        # Importar lançamento
        csv_content = """data,descricao,documento,valor,tipo
2024-01-20,PIX MANUAL,MANUAL001,250.00,C
"""
        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=csv_content
        )
        await conciliacao_service.importar_extrato_csv(import_data)

        # Buscar lançamento pendente
        pendentes = await conciliacao_service.listar_pendentes(
            banco_codigo="001",
            conta="12345-6"
        )
        lancamento = next(
            (l for l in pendentes if l.documento == "MANUAL001"),
            None
        )

        assert lancamento is not None

        # Conciliar manualmente
        resultado = await conciliacao_service.conciliar_manualmente(
            lancamento_id=lancamento.id,
            transacao_pix_id=transacao.id
        )

        assert resultado.status_conciliacao == StatusConciliacao.CONCILIADO
        assert resultado.transacao_pix_id == transacao.id


class TestRelatoriosConciliacao:
    """Testes para relatórios de conciliação"""

    async def test_gerar_relatorio_periodo(
        self, conciliacao_service: ConciliacaoService
    ):
        """Testa geração de relatório de conciliação por período"""
        # Importar lançamentos
        csv_content = """data,descricao,documento,valor,tipo
2024-01-15,PIX RECEBIDO,E12345678202401151200ABC123456789,150.00,C
2024-01-16,BOLETO PAGO,00012345678901234567,500.00,C
2024-01-17,TARIFA BANCARIA,,5.00,D
"""
        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=csv_content
        )
        await conciliacao_service.importar_extrato_csv(import_data)

        # Gerar relatório
        relatorio = await conciliacao_service.gerar_relatorio(
            banco_codigo="001",
            conta="12345-6",
            data_inicio=date(2024, 1, 1),
            data_fim=date(2024, 1, 31)
        )

        assert relatorio["total_lancamentos"] >= 3
        assert relatorio["total_creditos"] > 0
        assert relatorio["total_debitos"] > 0
        assert relatorio["saldo_periodo"] > 0
        assert "pendentes" in relatorio
        assert "conciliados" in relatorio

    async def test_estatisticas_conciliacao(
        self, conciliacao_service: ConciliacaoService
    ):
        """Testa geração de estatísticas de conciliação"""
        # Importar lançamentos
        csv_content = """data,descricao,documento,valor,tipo
2024-01-15,PIX 1,E001,100.00,C
2024-01-16,PIX 2,E002,200.00,C
2024-01-17,PIX 3,E003,300.00,C
2024-01-18,BOLETO 1,B001,400.00,C
2024-01-19,TARIFA,T001,10.00,D
"""
        import_data = ImportCSVRequest(
            banco_codigo="001",
            agencia="1234",
            conta="12345-6",
            conteudo_csv=csv_content
        )
        await conciliacao_service.importar_extrato_csv(import_data)

        # Gerar estatísticas
        stats = await conciliacao_service.obter_estatisticas(
            banco_codigo="001",
            conta="12345-6",
            data_inicio=date(2024, 1, 1),
            data_fim=date(2024, 1, 31)
        )

        assert stats["total_lancamentos"] >= 5
        assert stats["percentual_conciliado"] >= 0
        assert stats["percentual_pendente"] > 0
        assert "total_creditos" in stats
        assert "total_debitos" in stats
