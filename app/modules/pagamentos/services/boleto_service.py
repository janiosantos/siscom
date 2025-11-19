"""
Service Layer para Boleto Bancário
NOTA: Implementação simplificada. Para produção, integrar com biblioteca python-boleto
"""
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.core.logging import get_logger, log_business_event
from app.modules.pagamentos.models import (
    ConfiguracaoBoleto, Boleto, StatusBoleto
)
from app.modules.pagamentos.schemas import (
    ConfiguracaoBoletoCreate, BoletoCreate
)

logger = get_logger(__name__)


class BoletoService:
    """Service para operações de Boleto"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def criar_configuracao(
        self,
        config_data: ConfiguracaoBoletoCreate
    ) -> ConfiguracaoBoleto:
        """Cria configuração de boleto para um banco"""
        config = ConfiguracaoBoleto(**config_data.dict())
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)

        logger.info(f"Configuração de boleto criada: Banco {config.banco_codigo}")
        return config

    async def gerar_boleto(self, boleto_data: BoletoCreate) -> Boleto:
        """
        Gera um novo boleto

        NOTA: Implementação simplificada
        Para produção, usar biblioteca python-boleto ou similar
        """
        # Busca configuração
        result = await self.db.execute(
            select(ConfiguracaoBoleto).where(
                ConfiguracaoBoleto.id == boleto_data.configuracao_id,
                ConfiguracaoBoleto.ativa == True
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuração de boleto não encontrada"
            )

        # Gera nosso número (simplificado)
        nosso_numero = await self._gerar_nosso_numero(config)

        # Cria boleto
        boleto = Boleto(
            configuracao_id=config.id,
            nosso_numero=nosso_numero,
            numero_documento=str(boleto_data.valor),  # Simplificado
            valor=boleto_data.valor,
            valor_desconto=boleto_data.valor_desconto,
            data_vencimento=boleto_data.data_vencimento,
            sacado_nome=boleto_data.sacado_nome,
            sacado_documento=boleto_data.sacado_documento,
            sacado_endereco=boleto_data.sacado_endereco,
            sacado_cep=boleto_data.sacado_cep,
            sacado_cidade=boleto_data.sacado_cidade,
            sacado_uf=boleto_data.sacado_uf,
            instrucoes=boleto_data.instrucoes,
            demonstrativo=boleto_data.demonstrativo,
            status=StatusBoleto.REGISTRADO
        )

        # Gera código de barras e linha digitável (simplificado)
        # PRODUÇÃO: Usar biblioteca python-boleto
        boleto.codigo_barras = self._gerar_codigo_barras_fake(config, boleto)
        boleto.linha_digitavel = self._gerar_linha_digitavel_fake(boleto.codigo_barras)

        self.db.add(boleto)
        await self.db.commit()
        await self.db.refresh(boleto)

        logger.info(f"Boleto gerado: {nosso_numero}, valor: {boleto_data.valor}")
        log_business_event(
            event_name="boleto_gerado",
            nosso_numero=nosso_numero,
            valor=float(boleto_data.valor),
            banco=config.banco_codigo
        )

        return boleto

    async def consultar_boleto(self, boleto_id: int) -> Optional[Boleto]:
        """Consulta um boleto por ID"""
        result = await self.db.execute(
            select(Boleto).where(Boleto.id == boleto_id)
        )
        return result.scalar_one_or_none()

    async def marcar_como_pago(
        self,
        boleto_id: int,
        valor_pago: Decimal,
        data_pagamento: date
    ) -> Boleto:
        """Marca boleto como pago (processamento de CNAB retorno)"""
        boleto = await self.consultar_boleto(boleto_id)

        if not boleto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Boleto não encontrado"
            )

        boleto.status = StatusBoleto.PAGO
        boleto.valor_pago = valor_pago
        boleto.data_pagamento = data_pagamento

        await self.db.commit()
        await self.db.refresh(boleto)

        logger.info(f"Boleto marcado como pago: {boleto.nosso_numero}")
        log_business_event(
            event_name="boleto_pago",
            nosso_numero=boleto.nosso_numero,
            valor_pago=float(valor_pago)
        )

        return boleto

    async def _gerar_nosso_numero(self, config: ConfiguracaoBoleto) -> str:
        """Gera nosso número sequencial"""
        # Busca último nosso número
        result = await self.db.execute(
            select(Boleto).where(
                Boleto.configuracao_id == config.id
            ).order_by(Boleto.id.desc()).limit(1)
        )
        ultimo = result.scalar_one_or_none()

        if ultimo:
            proximo = int(ultimo.nosso_numero) + 1
        else:
            proximo = 1

        # Formata com zeros à esquerda (11 dígitos)
        return str(proximo).zfill(11)

    def _gerar_codigo_barras_fake(self, config: ConfiguracaoBoleto, boleto: Boleto) -> str:
        """
        Gera código de barras FAKE para demonstração
        PRODUÇÃO: Usar biblioteca python-boleto com cálculo real do DV
        """
        banco = config.banco_codigo
        moeda = "9"  # Real
        valor = str(int(boleto.valor * 100)).zfill(10)
        # Simplificado - não é um código real
        return f"{banco}{moeda}000000000000000{valor}0000000000000"

    def _gerar_linha_digitavel_fake(self, codigo_barras: str) -> str:
        """
        Gera linha digitável FAKE
        PRODUÇÃO: Usar biblioteca python-boleto
        """
        # Simplificado
        return f"{codigo_barras[:5]}.{codigo_barras[5:10]} {codigo_barras[10:20]} {codigo_barras[20:30]} {codigo_barras[30:44]}"
