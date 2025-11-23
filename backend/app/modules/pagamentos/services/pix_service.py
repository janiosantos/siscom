"""
Service Layer para PIX
Gerencia toda a lógica de negócio do PIX
"""
from __future__ import annotations

import uuid
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.logging import get_logger, log_business_event
from app.core.exceptions import NotFoundException, BusinessException
from app.modules.pagamentos.models import (
    ChavePix, TransacaoPix, StatusPagamento
)
from app.modules.pagamentos.schemas import (
    ChavePixCreate, TransacaoPixCreate, WebhookPixPayload
)
from sqlalchemy import func

logger = get_logger(__name__)


class PixService:
    """Service para operações PIX"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def criar_chave_pix(self, chave_data: ChavePixCreate) -> ChavePix:
        """
        Cria uma nova chave PIX

        Args:
            chave_data: Dados da chave PIX

        Returns:
            ChavePix criada

        Raises:
            HTTPException: Se chave já existe
        """
        # Verifica se chave já existe
        result = await self.db.execute(
            select(ChavePix).where(ChavePix.chave == chave_data.chave)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chave PIX já cadastrada"
            )

        chave = ChavePix(**chave_data.dict())
        self.db.add(chave)
        await self.db.commit()
        await self.db.refresh(chave)

        logger.info(f"Chave PIX criada: {chave.chave} ({chave.tipo})")
        return chave

    async def listar_chaves_pix(
        self,
        ativa: Optional[bool] = None
    ) -> List[ChavePix]:
        """
        Lista chaves PIX

        Args:
            ativa: Filtrar por ativas/inativas

        Returns:
            Lista de ChavePix
        """
        query = select(ChavePix)

        if ativa is not None:
            query = query.where(ChavePix.ativa == ativa)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def criar_cobranca_pix(
        self,
        cobranca_data: TransacaoPixCreate
    ) -> TransacaoPix:
        """
        Cria uma cobrança PIX

        Args:
            cobranca_data: Dados da cobrança

        Returns:
            TransacaoPix criada com QR Code

        Raises:
            HTTPException: Se chave PIX não encontrada
        """
        # Busca chave PIX
        result = await self.db.execute(
            select(ChavePix).where(
                ChavePix.id == cobranca_data.chave_pix_id,
                ChavePix.ativa == True
            )
        )
        chave_pix = result.scalar_one_or_none()

        if not chave_pix:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chave PIX não encontrada ou inativa"
            )

        # Gera TXID único
        txid = str(uuid.uuid4()).replace('-', '')[:35]

        # Cria transação
        transacao = TransacaoPix(
            txid=txid,
            chave_pix_id=chave_pix.id,
            valor=cobranca_data.valor,
            descricao=cobranca_data.descricao,
            pagador_nome=cobranca_data.pagador_nome,
            pagador_documento=cobranca_data.pagador_documento,
            status=StatusPagamento.PENDENTE,
            data_expiracao=cobranca_data.data_expiracao,
            webhook_url=cobranca_data.webhook_url
        )

        # Gera QR Code
        qr_code_texto = self._gerar_pix_copia_cola(
            chave=chave_pix.chave,
            valor=float(cobranca_data.valor),
            txid=txid,
            descricao=cobranca_data.descricao
        )
        transacao.qr_code_texto = qr_code_texto

        # Gera imagem do QR Code
        qr_code_imagem = self._gerar_qr_code_imagem(qr_code_texto)
        transacao.qr_code_imagem = qr_code_imagem

        self.db.add(transacao)
        await self.db.commit()
        await self.db.refresh(transacao)

        logger.info(f"Cobrança PIX criada: {txid}, valor: {cobranca_data.valor}")
        log_business_event(
            event_name="pix_cobranca_criada",
            txid=txid,
            valor=float(cobranca_data.valor),
            chave_pix=chave_pix.chave
        )

        return transacao

    async def consultar_transacao(self, txid: str) -> Optional[TransacaoPix]:
        """
        Consulta uma transação PIX por TXID

        Args:
            txid: Transaction ID

        Returns:
            TransacaoPix ou None
        """
        result = await self.db.execute(
            select(TransacaoPix).where(TransacaoPix.txid == txid)
        )
        return result.scalar_one_or_none()

    async def processar_webhook_pagamento(
        self,
        webhook_data: WebhookPixPayload
    ) -> TransacaoPix:
        """
        Processa webhook de confirmação de pagamento PIX

        Args:
            webhook_data: Dados do webhook

        Returns:
            TransacaoPix atualizada

        Raises:
            HTTPException: Se transação não encontrada
        """
        # Busca transação
        transacao = await self.consultar_transacao(webhook_data.txid)

        if not transacao:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação PIX não encontrada"
            )

        # Atualiza transação
        transacao.e2e_id = webhook_data.e2e_id
        transacao.status = StatusPagamento.APROVADO
        transacao.data_pagamento = webhook_data.data_pagamento
        transacao.pagador_nome = webhook_data.pagador_nome
        transacao.pagador_documento = webhook_data.pagador_documento

        await self.db.commit()
        await self.db.refresh(transacao)

        logger.info(f"PIX pago: {webhook_data.txid}, E2E: {webhook_data.e2e_id}")
        log_business_event(
            event_name="pix_pago",
            txid=webhook_data.txid,
            e2e_id=webhook_data.e2e_id,
            valor=float(webhook_data.valor)
        )

        return transacao

    async def cancelar_cobranca(self, txid: str) -> TransacaoPix:
        """
        Cancela uma cobrança PIX pendente

        Args:
            txid: Transaction ID

        Returns:
            TransacaoPix cancelada

        Raises:
            HTTPException: Se transação não pode ser cancelada
        """
        transacao = await self.consultar_transacao(txid)

        if not transacao:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transação PIX não encontrada"
            )

        if transacao.status != StatusPagamento.PENDENTE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Apenas cobranças pendentes podem ser canceladas"
            )

        transacao.status = StatusPagamento.CANCELADO

        await self.db.commit()
        await self.db.refresh(transacao)

        logger.info(f"Cobrança PIX cancelada: {txid}")
        log_business_event(
            event_name="pix_cancelado",
            txid=txid
        )

        return transacao

    async def verificar_expiradas(self) -> int:
        """
        Verifica e marca cobranças expiradas

        Returns:
            Número de cobranças marcadas como expiradas
        """
        # Busca cobranças pendentes expiradas
        result = await self.db.execute(
            select(TransacaoPix).where(
                TransacaoPix.status == StatusPagamento.PENDENTE,
                TransacaoPix.data_expiracao < datetime.utcnow()
            )
        )
        transacoes = list(result.scalars().all())

        count = 0
        for transacao in transacoes:
            transacao.status = StatusPagamento.EXPIRADO
            count += 1

        if count > 0:
            await self.db.commit()
            logger.info(f"{count} cobranças PIX marcadas como expiradas")

        return count

    def _gerar_pix_copia_cola(
        self,
        chave: str,
        valor: float,
        txid: str,
        descricao: Optional[str] = None
    ) -> str:
        """
        Gera código PIX Copia e Cola (BR Code)

        Implementação simplificada do padrão EMV/QRCPS
        Para produção, usar biblioteca como python-pix ou integração com gateway

        Args:
            chave: Chave PIX
            valor: Valor da cobrança
            txid: Transaction ID
            descricao: Descrição (opcional)

        Returns:
            String PIX Copia e Cola
        """
        # NOTA: Esta é uma implementação simplificada para exemplo
        # Em produção, usar biblioteca como python-pix ou integração com gateway
        # que gera o BR Code completo seguindo o padrão EMV

        # Formato simplificado (não é um BR Code válido real)
        # Para produção real, usar biblioteca ou API do banco/gateway

        pix_code = f"PIX{chave}|{valor:.2f}|{txid}"
        if descricao:
            pix_code += f"|{descricao}"

        logger.warning(
            "Usando geração de PIX simplificada. "
            "Para produção, integrar com API do banco ou gateway (Mercado Pago, PagSeguro)"
        )

        return pix_code

    def _gerar_qr_code_imagem(self, texto: str) -> str:
        """
        Gera imagem QR Code em base64

        Args:
            texto: Texto para gerar QR Code

        Returns:
            Imagem QR Code em base64 (data URI)
        """
        # Gera QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(texto)
        qr.make(fit=True)

        # Cria imagem
        img = qr.make_image(fill_color="black", back_color="white")

        # Converte para base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_base64}"

    # =========================================================================
    # Métodos adicionais para testes
    # =========================================================================

    async def listar_chaves(self, ativas_apenas: bool = True) -> List[ChavePix]:
        """
        Lista chaves PIX (alias para listar_chaves_pix)

        Args:
            ativas_apenas: Se True, retorna apenas chaves ativas

        Returns:
            Lista de ChavePix
        """
        return await self.listar_chaves_pix(ativa=ativas_apenas if ativas_apenas else None)

    async def buscar_por_txid(self, txid: str) -> Optional[TransacaoPix]:
        """
        Busca transação PIX por TXID (alias para consultar_transacao)

        Args:
            txid: Transaction ID

        Returns:
            TransacaoPix ou None
        """
        return await self.consultar_transacao(txid)

    async def expirar_cobrancas_antigas(self) -> int:
        """
        Expira cobranças antigas que não foram pagas (alias para verificar_expiradas)

        Returns:
            Número de cobranças expiradas
        """
        return await self.verificar_expiradas()

    async def desativar_chave(self, chave_id: int) -> ChavePix:
        """
        Desativa uma chave PIX

        Args:
            chave_id: ID da chave PIX

        Returns:
            ChavePix desativada

        Raises:
            NotFoundException: Se chave não encontrada
            BusinessException: Se há transações pendentes
        """
        # Buscar chave PIX
        result = await self.db.execute(
            select(ChavePix).where(ChavePix.id == chave_id)
        )
        chave = result.scalar_one_or_none()

        if not chave:
            raise NotFoundException(f"Chave PIX {chave_id} não encontrada")

        # Verificar transações pendentes
        result_transacoes = await self.db.execute(
            select(func.count(TransacaoPix.id)).where(
                TransacaoPix.chave_pix_id == chave_id,
                TransacaoPix.status == StatusPagamento.PENDENTE
            )
        )
        transacoes_pendentes = result_transacoes.scalar()

        if transacoes_pendentes > 0:
            raise BusinessException(
                f"Não é possível desativar chave com {transacoes_pendentes} transações pendentes"
            )

        # Chave já inativa? Aceitar (idempotência)
        if not chave.ativa:
            logger.info(f"Chave PIX {chave.chave} já estava inativa")
            return chave

        # Desativar chave
        chave.ativa = False
        await self.db.commit()
        await self.db.refresh(chave)

        logger.info(f"Chave PIX desativada: {chave.chave}")
        log_business_event(
            event_name="chave_pix_desativada",
            chave_id=chave_id,
            chave=chave.chave,
            tipo=chave.tipo.value
        )

        return chave
