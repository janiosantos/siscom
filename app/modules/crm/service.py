"""
Service para CRM e Análise RFM
"""
from datetime import datetime, date, timedelta
from typing import List
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crm.schemas import (
    ClienteRFM,
    AnaliseRFMResponse,
    SegmentoClientes,
    RelatorioSegmentosResponse,
    ClienteDetalhado,
    TopClientesResponse,
)
from app.modules.vendas.models import Venda
from app.modules.clientes.models import Cliente


class CRMService:
    """Service para CRM e análise de clientes"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def analise_rfm(
        self, data_inicio: date = None, data_fim: date = None
    ) -> AnaliseRFMResponse:
        """
        Análise RFM (Recência, Frequência, Monetário)

        RFM Score:
        - Recência (R): Dias desde última compra (menor = melhor)
        - Frequência (F): Total de compras (maior = melhor)
        - Monetário (M): Valor total gasto (maior = melhor)

        Cada dimensão recebe score de 1 a 5
        """
        if not data_fim:
            data_fim = date.today()
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=365)  # Último ano

        hoje = datetime.utcnow()

        # Query para dados RFM
        query = (
            select(
                Cliente.id,
                Cliente.nome,
                func.max(Venda.data_venda).label("ultima_compra"),
                func.count(Venda.id).label("frequencia"),
                func.sum(Venda.valor_total).label("monetario"),
                func.avg(Venda.valor_total).label("ticket_medio"),
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .where(
                and_(
                    Venda.data_venda >= data_inicio,
                    Venda.data_venda <= data_fim,
                    Venda.ativo == True,
                    Cliente.ativo == True,
                )
            )
            .group_by(Cliente.id, Cliente.nome)
        )

        result = await self.session.execute(query)
        rows = result.all()

        if not rows:
            return AnaliseRFMResponse(
                data_analise=datetime.utcnow(),
                total_clientes=0,
                clientes=[],
            )

        # Calcula recência em dias
        clientes_data = []
        for row in rows:
            recencia_dias = (hoje - row.ultima_compra).days if row.ultima_compra else 999
            clientes_data.append({
                "cliente_id": row.id,
                "cliente_nome": row.nome,
                "ultima_compra": row.ultima_compra,
                "recencia_dias": recencia_dias,
                "frequencia": row.frequencia,
                "monetario": float(row.monetario),
                "ticket_medio": float(row.ticket_medio),
            })

        # Calcula quartis para scoring
        recencias = sorted([c["recencia_dias"] for c in clientes_data])
        frequencias = sorted([c["frequencia"] for c in clientes_data], reverse=True)
        monetarios = sorted([c["monetario"] for c in clientes_data], reverse=True)

        # Calcula scores RFM
        clientes_rfm = []
        for c in clientes_data:
            score_r = self._calcular_score(c["recencia_dias"], recencias, reverse=False)
            score_f = self._calcular_score(c["frequencia"], frequencias, reverse=True)
            score_m = self._calcular_score(c["monetario"], monetarios, reverse=True)

            segmento = self._classificar_segmento_rfm(score_r, score_f, score_m)

            clientes_rfm.append(
                ClienteRFM(
                    **c,
                    score_r=score_r,
                    score_f=score_f,
                    score_m=score_m,
                    segmento_rfm=segmento,
                )
            )

        # Ordena por valor total (monetário)
        clientes_rfm.sort(key=lambda x: x.monetario, reverse=True)

        return AnaliseRFMResponse(
            data_analise=datetime.utcnow(),
            total_clientes=len(clientes_rfm),
            clientes=clientes_rfm,
        )

    def _calcular_score(self, valor, lista_valores, reverse=False):
        """Calcula score de 1 a 5 baseado em quartis"""
        n = len(lista_valores)
        if n == 0:
            return 3

        # Encontra posição do valor na lista ordenada
        pos = sorted(lista_valores).index(valor) if valor in lista_valores else 0

        # Calcula percentil
        percentil = (pos / n) * 100

        # Atribui score baseado em quintis
        if reverse:
            percentil = 100 - percentil

        if percentil >= 80:
            return 5
        elif percentil >= 60:
            return 4
        elif percentil >= 40:
            return 3
        elif percentil >= 20:
            return 2
        else:
            return 1

    def _classificar_segmento_rfm(self, r, f, m):
        """Classifica cliente em segmento baseado em scores RFM"""
        score_total = r + f + m

        if r >= 4 and f >= 4 and m >= 4:
            return "CAMPEÕES"
        elif r >= 3 and f >= 3 and m >= 3:
            return "CLIENTES FIÉIS"
        elif r >= 4 and f <= 2:
            return "NOVOS CLIENTES"
        elif r <= 2 and f >= 3 and m >= 3:
            return "EM RISCO"
        elif r <= 2 and f <= 2:
            return "PERDIDOS"
        elif m >= 4:
            return "ALTO VALOR"
        else:
            return "POTENCIAL"

    async def relatorio_segmentos(
        self, data_inicio: date = None, data_fim: date = None
    ) -> RelatorioSegmentosResponse:
        """Relatório de clientes por segmento RFM"""
        analise = await self.analise_rfm(data_inicio, data_fim)

        # Agrupa por segmento
        segmentos_map = {}
        for cliente in analise.clientes:
            seg = cliente.segmento_rfm
            if seg not in segmentos_map:
                segmentos_map[seg] = {
                    "segmento": seg,
                    "clientes": 0,
                    "valor_total": 0,
                }

            segmentos_map[seg]["clientes"] += 1
            segmentos_map[seg]["valor_total"] += cliente.monetario

        # Calcula percentuais
        total_clientes = analise.total_clientes
        valor_total = sum(c.monetario for c in analise.clientes)

        segmentos = []
        for seg_data in segmentos_map.values():
            desc = self._descricao_segmento(seg_data["segmento"])
            perc_clientes = (seg_data["clientes"] / total_clientes * 100) if total_clientes > 0 else 0
            perc_valor = (seg_data["valor_total"] / valor_total * 100) if valor_total > 0 else 0

            segmentos.append(
                SegmentoClientes(
                    segmento=seg_data["segmento"],
                    descricao=desc,
                    total_clientes=seg_data["clientes"],
                    valor_total=round(seg_data["valor_total"], 2),
                    percentual_clientes=round(perc_clientes, 2),
                    percentual_valor=round(perc_valor, 2),
                )
            )

        # Ordena por valor
        segmentos.sort(key=lambda x: x.valor_total, reverse=True)

        return RelatorioSegmentosResponse(
            data_analise=datetime.utcnow(),
            total_clientes=total_clientes,
            valor_total=round(valor_total, 2),
            segmentos=segmentos,
        )

    def _descricao_segmento(self, segmento: str) -> str:
        """Retorna descrição do segmento"""
        descricoes = {
            "CAMPEÕES": "Melhores clientes - alta recência, frequência e valor",
            "CLIENTES FIÉIS": "Clientes regulares e consistentes",
            "NOVOS CLIENTES": "Compraram recentemente mas com baixa frequência",
            "EM RISCO": "Não compram há algum tempo, mas eram bons clientes",
            "PERDIDOS": "Não compram há muito tempo",
            "ALTO VALOR": "Gastam muito, mas não compram frequentemente",
            "POTENCIAL": "Clientes com potencial de crescimento",
        }
        return descricoes.get(segmento, "Outros clientes")

    async def top_clientes(
        self, limit: int = 20, data_inicio: date = None, data_fim: date = None
    ) -> TopClientesResponse:
        """Top clientes por valor gasto"""
        if not data_fim:
            data_fim = date.today()
        if not data_inicio:
            data_inicio = data_fim - timedelta(days=365)

        query = (
            select(
                Cliente.id,
                Cliente.nome,
                Cliente.email,
                Cliente.telefone,
                Cliente.cpf,
                Cliente.cnpj,
                func.count(Venda.id).label("total_compras"),
                func.sum(Venda.valor_total).label("valor_total"),
                func.avg(Venda.valor_total).label("ticket_medio"),
                func.max(Venda.data_venda).label("ultima_compra"),
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .where(
                and_(
                    Venda.data_venda >= data_inicio,
                    Venda.data_venda <= data_fim,
                    Venda.ativo == True,
                    Cliente.ativo == True,
                )
            )
            .group_by(Cliente.id, Cliente.nome, Cliente.email, Cliente.telefone, Cliente.cpf, Cliente.cnpj)
            .order_by(desc(func.sum(Venda.valor_total)))
            .limit(limit)
        )

        result = await self.session.execute(query)
        rows = result.all()

        hoje = datetime.utcnow()
        clientes = []
        for row in rows:
            dias_ultima = (hoje - row.ultima_compra).days if row.ultima_compra else None
            cpf_cnpj = row.cpf or row.cnpj

            clientes.append(
                ClienteDetalhado(
                    cliente_id=row.id,
                    nome=row.nome,
                    email=row.email,
                    telefone=row.telefone,
                    cpf_cnpj=cpf_cnpj,
                    total_compras=row.total_compras,
                    valor_total_comprado=round(float(row.valor_total), 2),
                    ticket_medio=round(float(row.ticket_medio), 2),
                    ultima_compra=row.ultima_compra,
                    dias_desde_ultima_compra=dias_ultima,
                )
            )

        return TopClientesResponse(
            periodo_inicio=data_inicio,
            periodo_fim=data_fim,
            clientes=clientes,
            total_clientes=len(clientes),
        )
