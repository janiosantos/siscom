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
from sqlalchemy import select, and_, func, case
from fastapi import HTTPException, status

from app.core.logging import get_logger, log_business_event
from app.core.exceptions import NotFoundException, BusinessException
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

    # =========================================================================
    # Métodos adicionais para testes
    # =========================================================================

    async def obter_estatisticas(
        self,
        banco_codigo: str,
        conta: str,
        data_inicio: date,
        data_fim: date
    ) -> Dict[str, Any]:
        """
        Retorna estatísticas de conciliação

        Args:
            banco_codigo: Código do banco
            conta: Número da conta
            data_inicio: Data inicial
            data_fim: Data final

        Returns:
            Dict com estatísticas de conciliação
        """
        # Query para totalizadores
        result = await self.db.execute(
            select(
                func.count(ExtratoBancario.id).label('total'),
                func.sum(case((ExtratoBancario.conciliado == True, 1), else_=0)).label('conciliados'),
                func.sum(case((ExtratoBancario.conciliado == False, 1), else_=0)).label('pendentes'),
                func.coalesce(
                    func.sum(case((ExtratoBancario.conciliado == True, ExtratoBancario.valor), else_=0)),
                    0
                ).label('valor_conciliado'),
                func.coalesce(
                    func.sum(case((ExtratoBancario.conciliado == False, ExtratoBancario.valor), else_=0)),
                    0
                ).label('valor_pendente')
            ).where(
                ExtratoBancario.banco_codigo == banco_codigo,
                ExtratoBancario.conta == conta,
                ExtratoBancario.data >= data_inicio,
                ExtratoBancario.data <= data_fim
            )
        )

        row = result.one()

        total = row.total or 0
        conciliados = row.conciliados or 0
        pendentes = row.pendentes or 0
        taxa_conciliacao = (conciliados / total * 100) if total > 0 else 0.0

        return {
            "total_lancamentos": total,
            "conciliados": conciliados,
            "pendentes": pendentes,
            "taxa_conciliacao": round(taxa_conciliacao, 2),
            "valor_total_conciliado": float(row.valor_conciliado or 0),
            "valor_total_pendente": float(row.valor_pendente or 0)
        }

    async def gerar_relatorio(
        self,
        banco_codigo: str,
        conta: str,
        data_inicio: date,
        data_fim: date
    ) -> Dict[str, Any]:
        """
        Gera relatório completo de conciliação

        Args:
            banco_codigo: Código do banco
            conta: Número da conta
            data_inicio: Data inicial
            data_fim: Data final

        Returns:
            Dict com relatório completo
        """
        # Obter estatísticas
        estatisticas = await self.obter_estatisticas(
            banco_codigo, conta, data_inicio, data_fim
        )

        # Listar lançamentos pendentes
        pendentes = await self.listar_pendentes(
            banco_codigo, conta, data_inicio, data_fim
        )

        # Buscar conciliações com diferença
        result = await self.db.execute(
            select(ConciliacaoBancaria)
            .join(ExtratoBancario, ExtratoBancario.conciliacao_id == ConciliacaoBancaria.id)
            .where(
                ExtratoBancario.banco_codigo == banco_codigo,
                ExtratoBancario.conta == conta,
                ExtratoBancario.data >= data_inicio,
                ExtratoBancario.data <= data_fim,
                ConciliacaoBancaria.diferenca != 0
            )
        )
        diferencas = list(result.scalars().all())

        return {
            "periodo": {
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat()
            },
            "conta": {
                "banco_codigo": banco_codigo,
                "conta": conta
            },
            "estatisticas": estatisticas,
            "lancamentos_pendentes": [
                {
                    "id": p.id,
                    "data": p.data.isoformat(),
                    "descricao": p.descricao,
                    "valor": float(p.valor)
                }
                for p in pendentes
            ],
            "diferencas": [
                {
                    "id": d.id,
                    "diferenca": float(d.diferenca),
                    "valor_extrato": float(d.valor_extrato),
                    "valor_sistema": float(d.valor_sistema)
                }
                for d in diferencas
            ]
        }

    async def conciliar_manualmente(
        self,
        extrato_id: int,
        transacao_tipo: str,
        transacao_id: int,
        observacoes: Optional[str] = None
    ) -> ConciliacaoBancaria:
        """
        Cria conciliação manual entre extrato e transação

        Args:
            extrato_id: ID do lançamento de extrato
            transacao_tipo: Tipo de transação ('pix' ou 'boleto')
            transacao_id: ID da transação PIX ou boleto
            observacoes: Observações da conciliação manual

        Returns:
            ConciliacaoBancaria criada

        Raises:
            NotFoundException: Se extrato ou transação não encontrados
            BusinessException: Se extrato já conciliado
        """
        # Buscar lançamento de extrato
        result_extrato = await self.db.execute(
            select(ExtratoBancario).where(ExtratoBancario.id == extrato_id)
        )
        extrato = result_extrato.scalar_one_or_none()

        if not extrato:
            raise NotFoundException(f"Lançamento de extrato {extrato_id} não encontrado")

        if extrato.conciliado:
            raise BusinessException("Lançamento já está conciliado")

        # Buscar transação conforme tipo
        if transacao_tipo == 'pix':
            result_trans = await self.db.execute(
                select(TransacaoPix).where(TransacaoPix.id == transacao_id)
            )
            transacao = result_trans.scalar_one_or_none()
            if not transacao:
                raise NotFoundException(f"Transação PIX {transacao_id} não encontrada")
            valor_sistema = transacao.valor
            pix_id = transacao_id
            boleto_id = None

        elif transacao_tipo == 'boleto':
            result_trans = await self.db.execute(
                select(Boleto).where(Boleto.id == transacao_id)
            )
            transacao = result_trans.scalar_one_or_none()
            if not transacao:
                raise NotFoundException(f"Boleto {transacao_id} não encontrado")
            valor_sistema = transacao.valor
            pix_id = None
            boleto_id = transacao_id

        else:
            raise BusinessException(f"Tipo de transação inválido: {transacao_tipo}")

        # Calcular diferença
        diferenca = extrato.valor - valor_sistema

        # Criar conciliação MANUAL
        conciliacao = ConciliacaoBancaria(
            tipo=transacao_tipo,
            transacao_pix_id=pix_id,
            boleto_id=boleto_id,
            valor_sistema=valor_sistema,
            valor_extrato=extrato.valor,
            diferenca=diferenca,
            automatica=False,  # MANUAL
            observacoes=observacoes
        )

        self.db.add(conciliacao)

        # Marcar lançamento como conciliado
        extrato.conciliado = True
        extrato.data_conciliacao = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(conciliacao)

        logger.info(
            f"Conciliação manual criada: extrato {extrato_id} → "
            f"{transacao_tipo} {transacao_id}, diferença: {diferenca}"
        )
        log_business_event(
            event_name="conciliacao_manual",
            extrato_id=extrato_id,
            transacao_tipo=transacao_tipo,
            transacao_id=transacao_id,
            diferenca=float(diferenca)
        )

        return conciliacao
