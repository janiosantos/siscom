"""
Testes para o módulo de PIX
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.pagamentos.services.pix_service import PixService
from app.modules.pagamentos.models import ChavePix, TransacaoPix, TipoChavePix, StatusPagamento
from app.modules.pagamentos.schemas import (
    ChavePixCreate, TransacaoPixCreate, WebhookPixPayload
)


@pytest.fixture
async def pix_service(db_session: AsyncSession):
    """Fixture para PixService"""
    return PixService(db_session)


@pytest.fixture
async def chave_pix_cadastrada(pix_service: PixService):
    """Fixture para chave PIX já cadastrada"""
    chave_data = ChavePixCreate(
        tipo=TipoChavePix.CNPJ,
        chave="12345678000190",
        banco="001",
        agencia="1234",
        conta="12345-6",
        tipo_conta="CORRENTE",
        nome_titular="EMPRESA TESTE LTDA",
        ativa=True
    )
    return await pix_service.criar_chave_pix(chave_data)


class TestChavePix:
    """Testes para gerenciamento de chaves PIX"""

    async def test_criar_chave_pix_cnpj(self, pix_service: PixService):
        """Testa criação de chave PIX tipo CNPJ"""
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

        assert chave.id is not None
        assert chave.tipo == TipoChavePix.CNPJ
        assert chave.chave == "12345678000190"
        assert chave.banco == "001"
        assert chave.ativa is True

    async def test_criar_chave_pix_email(self, pix_service: PixService):
        """Testa criação de chave PIX tipo email"""
        chave_data = ChavePixCreate(
            tipo=TipoChavePix.EMAIL,
            chave="financeiro@empresa.com.br",
            banco="237",
            agencia="5678",
            conta="98765-4",
            tipo_conta="CORRENTE",
            nome_titular="EMPRESA TESTE LTDA"
        )

        chave = await pix_service.criar_chave_pix(chave_data)

        assert chave.tipo == TipoChavePix.EMAIL
        assert chave.chave == "financeiro@empresa.com.br"
        assert chave.banco == "237"

    async def test_criar_chave_pix_aleatoria(self, pix_service: PixService):
        """Testa criação de chave PIX aleatória"""
        chave_data = ChavePixCreate(
            tipo=TipoChavePix.ALEATORIA,
            chave="",  # Será gerada automaticamente
            banco="104",
            agencia="9999",
            conta="11111-1",
            tipo_conta="CORRENTE",
            nome_titular="EMPRESA TESTE LTDA"
        )

        chave = await pix_service.criar_chave_pix(chave_data)

        assert chave.tipo == TipoChavePix.ALEATORIA
        assert len(chave.chave) == 32  # UUID sem hífens
        assert chave.banco == "104"

    async def test_listar_chaves_pix_ativas(self, pix_service: PixService, chave_pix_cadastrada):
        """Testa listagem de chaves PIX ativas"""
        chaves = await pix_service.listar_chaves(ativas_apenas=True)

        assert len(chaves) > 0
        assert all(chave.ativa for chave in chaves)

    async def test_desativar_chave_pix(self, pix_service: PixService, chave_pix_cadastrada):
        """Testa desativação de chave PIX"""
        chave_id = chave_pix_cadastrada.id

        chave = await pix_service.desativar_chave(chave_id)

        assert chave.ativa is False


class TestCobrancaPix:
    """Testes para cobranças PIX"""

    async def test_criar_cobranca_pix(self, pix_service: PixService, chave_pix_cadastrada):
        """Testa criação de cobrança PIX"""
        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave_pix_cadastrada.id,
            valor=Decimal("150.00"),
            descricao="Venda #1234",
            cliente_id=1,
            venda_id=1234
        )

        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        assert transacao.id is not None
        assert transacao.txid is not None
        assert len(transacao.txid) == 32
        assert transacao.valor == Decimal("150.00")
        assert transacao.status == StatusPagamento.PENDENTE
        assert transacao.qr_code_texto is not None
        assert transacao.qr_code_imagem is not None
        assert transacao.qr_code_imagem.startswith("data:image/png;base64,")

    async def test_qr_code_gerado_valido(self, pix_service: PixService, chave_pix_cadastrada):
        """Testa se QR Code é gerado corretamente"""
        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave_pix_cadastrada.id,
            valor=Decimal("100.00"),
            descricao="Teste QR Code"
        )

        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        # QR Code copia e cola deve conter informações essenciais
        assert transacao.chave_pix_id == chave_pix_cadastrada.id
        assert "12345678000190" in transacao.qr_code_texto or chave_pix_cadastrada.chave in transacao.qr_code_texto

        # QR Code imagem deve ser base64 válido
        assert transacao.qr_code_imagem.startswith("data:image/png;base64,")
        base64_data = transacao.qr_code_imagem.split(",")[1]
        assert len(base64_data) > 100  # Imagem deve ter tamanho razoável

    async def test_buscar_transacao_por_txid(self, pix_service: PixService, chave_pix_cadastrada):
        """Testa busca de transação por TXID"""
        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave_pix_cadastrada.id,
            valor=Decimal("200.00"),
            descricao="Teste busca"
        )

        transacao_criada = await pix_service.criar_cobranca_pix(cobranca_data)
        txid = transacao_criada.txid

        transacao = await pix_service.buscar_por_txid(txid)

        assert transacao is not None
        assert transacao.txid == txid
        assert transacao.valor == Decimal("200.00")


class TestWebhookPix:
    """Testes para processamento de webhooks PIX"""

    async def test_processar_webhook_pagamento_aprovado(
        self, pix_service: PixService, chave_pix_cadastrada
    ):
        """Testa processamento de webhook de pagamento aprovado"""
        # Criar cobrança
        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave_pix_cadastrada.id,
            valor=Decimal("150.00"),
            descricao="Venda #5678"
        )
        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        # Simular webhook de pagamento
        webhook_data = WebhookPixPayload(
            txid=transacao.txid,
            e2e_id="E12345678202301011200ABC123456789",
            valor_pago=Decimal("150.00"),
            data_pagamento=datetime.now(),
            psp="MERCADO_PAGO",
            status="APROVADO"
        )

        transacao_atualizada = await pix_service.processar_webhook_pagamento(webhook_data)

        assert transacao_atualizada.status == StatusPagamento.APROVADO
        assert transacao_atualizada.e2e_id == "E12345678202301011200ABC123456789"
        assert transacao_atualizada.data_pagamento is not None
        assert transacao_atualizada.psp == "MERCADO_PAGO"

    async def test_processar_webhook_pagamento_recusado(
        self, pix_service: PixService, chave_pix_cadastrada
    ):
        """Testa processamento de webhook de pagamento recusado"""
        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave_pix_cadastrada.id,
            valor=Decimal("100.00"),
            descricao="Venda #9999"
        )
        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        webhook_data = WebhookPixPayload(
            txid=transacao.txid,
            e2e_id="E12345678202301011200XYZ987654321",
            valor_pago=Decimal("0.00"),
            data_pagamento=datetime.now(),
            psp="PAGSEGURO",
            status="RECUSADO"
        )

        transacao_atualizada = await pix_service.processar_webhook_pagamento(webhook_data)

        assert transacao_atualizada.status == StatusPagamento.RECUSADO

    async def test_processar_webhook_txid_inexistente(self, pix_service: PixService):
        """Testa processamento de webhook com TXID inexistente"""
        webhook_data = WebhookPixPayload(
            txid="TXID_INVALIDO_123456789012345678",
            e2e_id="E12345678202301011200ABC123456789",
            valor_pago=Decimal("100.00"),
            data_pagamento=datetime.now(),
            psp="MERCADO_PAGO",
            status="APROVADO"
        )

        with pytest.raises(ValueError, match="Transação PIX não encontrada"):
            await pix_service.processar_webhook_pagamento(webhook_data)


class TestCancelarCobrancaPix:
    """Testes para cancelamento de cobranças PIX"""

    async def test_cancelar_cobranca_pendente(
        self, pix_service: PixService, chave_pix_cadastrada
    ):
        """Testa cancelamento de cobrança pendente"""
        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave_pix_cadastrada.id,
            valor=Decimal("50.00"),
            descricao="Venda cancelada"
        )
        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        transacao_cancelada = await pix_service.cancelar_cobranca(transacao.txid)

        assert transacao_cancelada.status == StatusPagamento.CANCELADO

    async def test_cancelar_cobranca_ja_paga(
        self, pix_service: PixService, chave_pix_cadastrada
    ):
        """Testa que não é possível cancelar cobrança já paga"""
        # Criar e pagar
        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave_pix_cadastrada.id,
            valor=Decimal("100.00"),
            descricao="Venda paga"
        )
        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        webhook_data = WebhookPixPayload(
            txid=transacao.txid,
            e2e_id="E12345678202301011200TEST12345678",
            valor_pago=Decimal("100.00"),
            data_pagamento=datetime.now(),
            psp="MERCADO_PAGO",
            status="APROVADO"
        )
        await pix_service.processar_webhook_pagamento(webhook_data)

        # Tentar cancelar
        with pytest.raises(ValueError, match="apenas.*pendente"):
            await pix_service.cancelar_cobranca(transacao.txid)


class TestExpiracaoCobrancaPix:
    """Testes para expiração de cobranças PIX"""

    async def test_expirar_cobranças_antigas(
        self, pix_service: PixService, chave_pix_cadastrada, db_session: AsyncSession
    ):
        """Testa expiração automática de cobranças antigas"""
        # Criar cobrança antiga (simular)
        cobranca_data = TransacaoPixCreate(
            chave_pix_id=chave_pix_cadastrada.id,
            valor=Decimal("100.00"),
            descricao="Cobrança antiga",
            expiracao_em_segundos=1  # 1 segundo
        )
        transacao = await pix_service.criar_cobranca_pix(cobranca_data)

        # Simular passagem do tempo (modificar data_criacao)
        from sqlalchemy import update
        stmt = update(TransacaoPix).where(
            TransacaoPix.id == transacao.id
        ).values(
            data_criacao=datetime.now() - timedelta(hours=25)  # 25 horas atrás
        )
        await db_session.execute(stmt)
        await db_session.commit()

        # Executar processo de expiração
        expiradas = await pix_service.expirar_cobrancas_antigas()

        assert expiradas > 0

        # Verificar que foi expirada
        transacao_atualizada = await pix_service.buscar_por_txid(transacao.txid)
        assert transacao_atualizada.status == StatusPagamento.EXPIRADO
