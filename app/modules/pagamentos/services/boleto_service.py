"""
Service Layer para Boleto Bancário
NOTA: Implementação simplificada. Para produção, integrar com biblioteca python-boleto
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.core.logging import get_logger, log_business_event
from app.core.exceptions import NotFoundException, BusinessException
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
            status=StatusBoleto.ABERTO
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
        """
        Marca boleto como pago (processamento de CNAB retorno)

        Calcula automaticamente juros e multa se boleto pago após vencimento
        """
        # Buscar boleto com configuração
        result = await self.db.execute(
            select(Boleto)
            .options(selectinload(Boleto.configuracao))
            .where(Boleto.id == boleto_id)
        )
        boleto = result.scalar_one_or_none()

        if not boleto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Boleto não encontrado"
            )

        # Calcular juros e multa se pagamento após vencimento
        valor_juros = Decimal(0)
        valor_multa = Decimal(0)

        if data_pagamento > boleto.data_vencimento:
            dias_atraso = (data_pagamento - boleto.data_vencimento).days
            config = boleto.configuracao

            # Multa (cobrada uma vez)
            if config.percentual_multa > 0:
                valor_multa = (boleto.valor * config.percentual_multa) / 100

            # Juros (proporcional aos dias de atraso)
            if config.percentual_juros > 0:
                # Juros ao dia = (juros ao mês / 30)
                juros_dia = config.percentual_juros / 30
                valor_juros = (boleto.valor * juros_dia * dias_atraso) / 100

        # Atualizar boleto
        boleto.status = StatusBoleto.PAGO
        boleto.valor_pago = valor_pago
        boleto.valor_juros = valor_juros
        boleto.valor_multa = valor_multa
        boleto.data_pagamento = data_pagamento

        await self.db.commit()
        await self.db.refresh(boleto)

        logger.info(f"Boleto marcado como pago: {boleto.nosso_numero}, valor_pago={valor_pago}, juros={valor_juros}, multa={valor_multa}")
        log_business_event(
            event_name="boleto_pago",
            nosso_numero=boleto.nosso_numero,
            valor_pago=float(valor_pago),
            valor_juros=float(valor_juros),
            valor_multa=float(valor_multa)
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
        Gera código de barras FAKE para demonstração (44 dígitos)
        PRODUÇÃO: Usar biblioteca python-boleto com cálculo real do DV

        Formato padrão: 44 dígitos
        - Posições 1-3: Código do banco (3)
        - Posição 4: Código da moeda (1)
        - Posição 5: Dígito verificador (1)
        - Posições 6-19: Valor com fator de vencimento (14)
        - Posições 20-44: Campo livre (25)
        """
        banco = config.banco_codigo  # 3 dígitos
        moeda = "9"  # Real (1 dígito)
        dv = "0"  # Dígito verificador fake (1 dígito)
        valor = str(int(boleto.valor * 100)).zfill(10)  # 10 dígitos
        fator = "0000"  # Fator de vencimento fake (4 dígitos)
        campo_livre = "0" * 25  # 25 dígitos

        # Total: 3 + 1 + 1 + 10 + 4 + 25 = 44 dígitos
        codigo = f"{banco}{moeda}{dv}{valor}{fator}{campo_livre}"
        return codigo

    def _gerar_linha_digitavel_fake(self, codigo_barras: str) -> str:
        """
        Gera linha digitável FAKE para demonstração (47 caracteres)
        PRODUÇÃO: Usar biblioteca python-boleto com cálculo real dos DVs

        Formato: AAAAA.AAAAA BBBBB.BBBBBB CCCCC.CCCCCC DDDDDDDDD
        Total: 11 + 1 + 12 + 1 + 12 + 1 + 9 = 47 caracteres
        """
        # Campo 1: 5.5 (11 chars)
        campo1 = f"{codigo_barras[0:5]}.{codigo_barras[5:10]}"

        # Campo 2: 5.6 (12 chars)
        campo2 = f"{codigo_barras[10:15]}.{codigo_barras[15:21]}"

        # Campo 3: 5.6 (12 chars)
        campo3 = f"{codigo_barras[21:26]}.{codigo_barras[26:32]}"

        # Campo 4: 9 dígitos (DV + Fator + parte do valor)
        campo4 = codigo_barras[32:41]

        return f"{campo1} {campo2} {campo3} {campo4}"

    # =========================================================================
    # Métodos adicionais para testes
    # =========================================================================

    async def buscar_por_id(self, boleto_id: int) -> Optional[Boleto]:
        """
        Busca boleto por ID (alias para consultar_boleto)

        Args:
            boleto_id: ID do boleto

        Returns:
            Boleto encontrado ou None
        """
        return await self.consultar_boleto(boleto_id)

    async def buscar_por_nosso_numero(self, nosso_numero: str) -> Optional[Boleto]:
        """
        Busca boleto por nosso número

        Args:
            nosso_numero: Nosso número do boleto (único)

        Returns:
            Boleto encontrado ou None
        """
        if not nosso_numero:
            return None

        result = await self.db.execute(
            select(Boleto)
            .options(selectinload(Boleto.configuracao))
            .where(Boleto.nosso_numero == nosso_numero)
        )
        return result.scalar_one_or_none()

    async def listar_configuracoes(
        self,
        ativas_apenas: bool = True
    ) -> List[ConfiguracaoBoleto]:
        """
        Lista configurações de boleto cadastradas

        Args:
            ativas_apenas: Se True, retorna apenas configurações ativas

        Returns:
            Lista de ConfiguracaoBoleto
        """
        query = select(ConfiguracaoBoleto)

        if ativas_apenas:
            query = query.where(ConfiguracaoBoleto.ativa == True)

        query = query.order_by(
            ConfiguracaoBoleto.banco_codigo,
            ConfiguracaoBoleto.agencia
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def listar_vencidos(self, dias_atraso: int = 0) -> List[Boleto]:
        """
        Lista boletos vencidos e não pagos

        Args:
            dias_atraso: Dias de atraso mínimo (0 = qualquer atraso)

        Returns:
            Lista de boletos vencidos
        """
        data_limite = date.today()

        if dias_atraso > 0:
            data_limite = date.today() - timedelta(days=dias_atraso)

        query = (
            select(Boleto)
            .options(selectinload(Boleto.configuracao))
            .where(
                Boleto.status.in_([StatusBoleto.REGISTRADO, StatusBoleto.ABERTO]),
                Boleto.data_vencimento < data_limite
            )
            .order_by(Boleto.data_vencimento.asc())
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def cancelar_boleto(self, boleto_id: int) -> Boleto:
        """
        Cancela um boleto registrado

        Args:
            boleto_id: ID do boleto a ser cancelado

        Returns:
            Boleto cancelado

        Raises:
            NotFoundException: Se boleto não encontrado
            BusinessException: Se boleto não pode ser cancelado
        """
        boleto = await self.consultar_boleto(boleto_id)

        if not boleto:
            raise NotFoundException(f"Boleto {boleto_id} não encontrado")

        # Validar se pode cancelar
        if boleto.status == StatusBoleto.PAGO:
            raise BusinessException(
                "Não é possível cancelar boleto já pago"
            )

        if boleto.status == StatusBoleto.CANCELADO:
            # Idempotência - já está cancelado
            logger.info(f"Boleto {boleto.nosso_numero} já estava cancelado")
            return boleto

        # Apenas boletos em aberto ou registrados podem ser cancelados
        if boleto.status not in [StatusBoleto.ABERTO, StatusBoleto.REGISTRADO]:
            raise BusinessException(
                f"Boleto com status {boleto.status.value} não pode ser cancelado"
            )

        # Cancelar
        boleto.status = StatusBoleto.CANCELADO
        await self.db.commit()
        await self.db.refresh(boleto)

        logger.info(f"Boleto cancelado: {boleto.nosso_numero}")
        log_business_event(
            event_name="boleto_cancelado",
            nosso_numero=boleto.nosso_numero,
            boleto_id=boleto_id
        )

        return boleto
