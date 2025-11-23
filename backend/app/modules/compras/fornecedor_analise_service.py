"""
Service para Análise de Desempenho de Fornecedores
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.compras.models import PedidoCompra, StatusPedidoCompra
from app.modules.fornecedores.models import Fornecedor


class FornecedorAnaliseService:
    """Service para análise de desempenho de fornecedores"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def analisar_desempenho_fornecedor(
        self, fornecedor_id: int, periodo_dias: int = 180
    ) -> Dict[str, Any]:
        """
        Analisa o desempenho de um fornecedor

        Métricas:
        - Total de pedidos
        - Total de valor comprado
        - Taxa de entrega no prazo
        - Média de dias de atraso
        - Taxa de pedidos recebidos completos
        - Ticket médio

        Args:
            fornecedor_id: ID do fornecedor
            periodo_dias: Período de análise em dias (padrão 180)

        Returns:
            Dicionário com métricas de desempenho
        """
        data_inicio = datetime.utcnow() - timedelta(days=periodo_dias)

        # Busca pedidos do fornecedor no período
        query = select(PedidoCompra).where(
            PedidoCompra.fornecedor_id == fornecedor_id,
            PedidoCompra.data_pedido >= data_inicio,
        )
        result = await self.session.execute(query)
        pedidos = list(result.scalars().all())

        if not pedidos:
            return {
                "fornecedor_id": fornecedor_id,
                "periodo_dias": periodo_dias,
                "total_pedidos": 0,
                "valor_total_comprado": 0,
                "ticket_medio": 0,
                "taxa_entrega_no_prazo": 0,
                "media_dias_atraso": 0,
                "taxa_recebimento_completo": 0,
                "classificacao": "SEM DADOS",
            }

        # Calcula métricas
        total_pedidos = len(pedidos)
        valor_total = sum(p.valor_total for p in pedidos)
        ticket_medio = valor_total / total_pedidos if total_pedidos > 0 else 0

        # Pedidos com entrega realizada
        pedidos_entregues = [
            p for p in pedidos if p.data_entrega_real is not None
        ]

        # Taxa de entrega no prazo
        if pedidos_entregues:
            entregas_no_prazo = sum(
                1
                for p in pedidos_entregues
                if p.data_entrega_real <= p.data_entrega_prevista
            )
            taxa_entrega_prazo = (entregas_no_prazo / len(pedidos_entregues)) * 100
        else:
            taxa_entrega_prazo = 0

        # Média de dias de atraso
        atrasos = []
        for pedido in pedidos_entregues:
            if pedido.data_entrega_real > pedido.data_entrega_prevista:
                dias_atraso = (
                    pedido.data_entrega_real - pedido.data_entrega_prevista
                ).days
                atrasos.append(dias_atraso)

        media_atraso = sum(atrasos) / len(atrasos) if atrasos else 0

        # Taxa de recebimento completo
        pedidos_recebidos = [
            p
            for p in pedidos
            if p.status
            in [StatusPedidoCompra.RECEBIDO, StatusPedidoCompra.RECEBIDO_PARCIAL]
        ]

        if pedidos_recebidos:
            recebimentos_completos = sum(
                1 for p in pedidos_recebidos if p.status == StatusPedidoCompra.RECEBIDO
            )
            taxa_recebimento_completo = (
                recebimentos_completos / len(pedidos_recebidos)
            ) * 100
        else:
            taxa_recebimento_completo = 0

        # Classificação do fornecedor
        classificacao = self._classificar_fornecedor(
            taxa_entrega_prazo, media_atraso, taxa_recebimento_completo
        )

        return {
            "fornecedor_id": fornecedor_id,
            "periodo_dias": periodo_dias,
            "data_inicio_analise": data_inicio.isoformat(),
            "total_pedidos": total_pedidos,
            "valor_total_comprado": float(valor_total),
            "ticket_medio": float(ticket_medio),
            "taxa_entrega_no_prazo": round(taxa_entrega_prazo, 2),
            "media_dias_atraso": round(media_atraso, 2),
            "taxa_recebimento_completo": round(taxa_recebimento_completo, 2),
            "total_pedidos_entregues": len(pedidos_entregues),
            "total_pedidos_atrasados": len(atrasos),
            "classificacao": classificacao,
        }

    def _classificar_fornecedor(
        self, taxa_prazo: float, media_atraso: float, taxa_completo: float
    ) -> str:
        """
        Classifica fornecedor com base nas métricas

        Critérios:
        - EXCELENTE: >90% prazo, <2 dias atraso, >95% completo
        - BOM: >75% prazo, <5 dias atraso, >85% completo
        - REGULAR: >60% prazo, <10 dias atraso, >70% completo
        - RUIM: abaixo dos critérios acima
        """
        if taxa_prazo >= 90 and media_atraso < 2 and taxa_completo >= 95:
            return "EXCELENTE"
        elif taxa_prazo >= 75 and media_atraso < 5 and taxa_completo >= 85:
            return "BOM"
        elif taxa_prazo >= 60 and media_atraso < 10 and taxa_completo >= 70:
            return "REGULAR"
        else:
            return "RUIM"

    async def ranking_fornecedores(self, periodo_dias: int = 180) -> List[Dict[str, Any]]:
        """
        Cria ranking de fornecedores por desempenho

        Args:
            periodo_dias: Período de análise

        Returns:
            Lista de fornecedores ordenada por classificação e taxa de entrega
        """
        # Busca todos os fornecedores ativos
        query = select(Fornecedor).where(Fornecedor.ativo == True)
        result = await self.session.execute(query)
        fornecedores = list(result.scalars().all())

        ranking = []
        for fornecedor in fornecedores:
            analise = await self.analisar_desempenho_fornecedor(
                fornecedor.id, periodo_dias
            )

            if analise["total_pedidos"] > 0:
                ranking.append(
                    {
                        "fornecedor_id": fornecedor.id,
                        "razao_social": fornecedor.razao_social,
                        "cnpj": fornecedor.cnpj,
                        **analise,
                    }
                )

        # Ordena por classificação e taxa de entrega no prazo
        ordem_classificacao = {"EXCELENTE": 4, "BOM": 3, "REGULAR": 2, "RUIM": 1}

        ranking.sort(
            key=lambda x: (
                ordem_classificacao.get(x["classificacao"], 0),
                x["taxa_entrega_no_prazo"],
            ),
            reverse=True,
        )

        return ranking

    async def comparar_fornecedores(
        self, fornecedor_ids: List[int], periodo_dias: int = 180
    ) -> List[Dict[str, Any]]:
        """
        Compara o desempenho de múltiplos fornecedores

        Args:
            fornecedor_ids: Lista de IDs de fornecedores para comparar
            periodo_dias: Período de análise

        Returns:
            Lista com análise comparativa
        """
        comparacao = []

        for fornecedor_id in fornecedor_ids:
            # Busca dados do fornecedor
            query = select(Fornecedor).where(Fornecedor.id == fornecedor_id)
            result = await self.session.execute(query)
            fornecedor = result.scalar_one_or_none()

            if fornecedor:
                analise = await self.analisar_desempenho_fornecedor(
                    fornecedor_id, periodo_dias
                )
                comparacao.append(
                    {
                        "fornecedor_id": fornecedor.id,
                        "razao_social": fornecedor.razao_social,
                        "cnpj": fornecedor.cnpj,
                        **analise,
                    }
                )

        return comparacao
