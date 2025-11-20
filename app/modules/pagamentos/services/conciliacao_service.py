"""
Service Layer para Conciliação Bancária
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
import csv
import io
import base64
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status

from app.core.logging import get_logger, log_business_event
from app.modules.pagamentos.models import (
    ExtratoBancario, ConciliacaoBancaria, TransacaoPix, Boleto
)
from app.modules.pagamentos.schemas import (
    ExtratoBancarioCreate, ConciliacaoBancariaCreate,
    ImportCSVRequest
)

logger = get_logger(__name__)


class ConciliacaoService:
    """Service para Conciliação Bancária"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def importar_extrato_csv(
        self,
        import_data: ImportCSVRequest
    ) -> Dict[str, Any]:
        """
        Importa extrato bancário de arquivo CSV

        Formato esperado: data,descricao,documento,valor,tipo
        """
        # Decodifica base64
        try:
            csv_content = base64.b64decode(import_data.arquivo_base64).decode(
                import_data.encoding
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro ao decodificar arquivo: {str(e)}"
            )

        # Parse CSV
        reader = csv.DictReader(
            io.StringIO(csv_content),
            delimiter=import_data.separador
        )

        lancamentos_criados = 0
        erros = []

        for idx, row in enumerate(reader, start=1):
            try:
                # Valida campos obrigatórios
                if not all(k in row for k in ['data', 'descricao', 'valor', 'tipo']):
                    erros.append(f"Linha {idx}: Campos obrigatórios faltando")
                    continue

                # Cria lançamento
                lancamento = ExtratoBancario(
                    banco_codigo=import_data.banco_codigo,
                    agencia=import_data.agencia,
                    conta=import_data.conta,
                    data=datetime.strptime(row['data'], '%Y-%m-%d').date(),
                    descricao=row['descricao'],
                    documento=row.get('documento'),
                    valor=Decimal(row['valor'].replace(',', '.')),
                    tipo=row['tipo'].upper(),
                    saldo=Decimal(row.get('saldo', '0').replace(',', '.')) if row.get('saldo') else None,
                    arquivo_origem=f"import_csv_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    linha_arquivo=idx
                )

                self.db.add(lancamento)
                lancamentos_criados += 1

            except Exception as e:
                erros.append(f"Linha {idx}: {str(e)}")

        await self.db.commit()

        logger.info(f"Extrato importado: {lancamentos_criados} lançamentos")

        return {
            "lancamentos_criados": lancamentos_criados,
            "erros": erros
        }

    async def listar_pendentes(
        self,
        banco_codigo: str,
        conta: str,
        data_inicio: date = None,
        data_fim: date = None
    ) -> List[ExtratoBancario]:
        """Lista lançamentos não conciliados"""
        query = select(ExtratoBancario).where(
            ExtratoBancario.banco_codigo == banco_codigo,
            ExtratoBancario.conta == conta,
            ExtratoBancario.conciliado == False
        )

        if data_inicio:
            query = query.where(ExtratoBancario.data >= data_inicio)
        if data_fim:
            query = query.where(ExtratoBancario.data <= data_fim)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def conciliar_automaticamente(
        self,
        banco_codigo: str,
        data_inicio: date,
        data_fim: date
    ) -> Dict[str, Any]:
        """
        Conciliação automática por matching

        Algoritmo:
        1. PIX: Match por E2E ID no documento
        2. Boleto: Match por Nosso Número no documento
        3. Tolerância: ±0.01 no valor, ±1 dia na data
        """
        # Busca lançamentos pendentes
        result = await self.db.execute(
            select(ExtratoBancario).where(
                ExtratoBancario.banco_codigo == banco_codigo,
                ExtratoBancario.conciliado == False,
                ExtratoBancario.data >= data_inicio,
                ExtratoBancario.data <= data_fim
            )
        )
        lancamentos = list(result.scalars().all())

        conciliados = 0
        detalhes = []

        for lancamento in lancamentos:
            # Tenta match PIX por E2E ID
            if lancamento.documento and lancamento.documento.startswith('E'):
                match_pix = await self._tentar_match_pix(lancamento)
                if match_pix:
                    await self._criar_conciliacao(
                        lancamento,
                        "pix",
                        transacao_pix_id=match_pix.id,
                        valor_sistema=match_pix.valor
                    )
                    conciliados += 1
                    detalhes.append({
                        "extrato_id": lancamento.id,
                        "transacao_pix_id": match_pix.id,
                        "valor": float(lancamento.valor)
                    })
                    continue

            # Tenta match Boleto por Nosso Número
            if lancamento.documento and lancamento.documento.isdigit():
                match_boleto = await self._tentar_match_boleto(lancamento)
                if match_boleto:
                    await self._criar_conciliacao(
                        lancamento,
                        "boleto",
                        boleto_id=match_boleto.id,
                        valor_sistema=match_boleto.valor
                    )
                    conciliados += 1
                    detalhes.append({
                        "extrato_id": lancamento.id,
                        "boleto_id": match_boleto.id,
                        "valor": float(lancamento.valor)
                    })

        await self.db.commit()

        logger.info(f"Conciliação automática: {conciliados}/{len(lancamentos)} conciliados")

        return {
            "total_lancamentos": len(lancamentos),
            "conciliados_automaticamente": conciliados,
            "pendentes": len(lancamentos) - conciliados,
            "detalhes": detalhes
        }

    async def _tentar_match_pix(
        self,
        lancamento: ExtratoBancario
    ) -> Optional[TransacaoPix]:
        """Tenta encontrar transação PIX correspondente"""
        result = await self.db.execute(
            select(TransacaoPix).where(
                TransacaoPix.e2e_id == lancamento.documento,
                # Tolerância de ±0.01
                TransacaoPix.valor.between(
                    lancamento.valor - Decimal('0.01'),
                    lancamento.valor + Decimal('0.01')
                )
            )
        )
        return result.scalar_one_or_none()

    async def _tentar_match_boleto(
        self,
        lancamento: ExtratoBancario
    ) -> Optional[Boleto]:
        """Tenta encontrar boleto correspondente"""
        result = await self.db.execute(
            select(Boleto).where(
                Boleto.nosso_numero == lancamento.documento,
                # Tolerância de ±0.01
                Boleto.valor.between(
                    lancamento.valor - Decimal('0.01'),
                    lancamento.valor + Decimal('0.01')
                )
            )
        )
        return result.scalar_one_or_none()

    async def _criar_conciliacao(
        self,
        lancamento: ExtratoBancario,
        tipo: str,
        transacao_pix_id: int = None,
        boleto_id: int = None,
        valor_sistema: Decimal = None
    ):
        """Cria registro de conciliação"""
        diferenca = lancamento.valor - valor_sistema if valor_sistema else Decimal('0')

        conciliacao = ConciliacaoBancaria(
            tipo=tipo,
            transacao_pix_id=transacao_pix_id,
            boleto_id=boleto_id,
            valor_sistema=valor_sistema,
            valor_extrato=lancamento.valor,
            diferenca=diferenca,
            automatica=True
        )

        self.db.add(conciliacao)

        # Marca lançamento como conciliado
        lancamento.conciliado = True
        lancamento.data_conciliacao = datetime.utcnow()
        lancamento.conciliacao_id = conciliacao.id
