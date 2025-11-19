"""
Service para Relatórios e Dashboard
"""
from datetime import date, datetime, timedelta
from typing import List
from decimal import Decimal
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.relatorios.schemas import (
    DashboardVendasResponse,
    DashboardResponse,
    KPICard,
    VendedorDesempenho,
    RelatorioVendedoresResponse,
    ProdutoVendido,
    RelatorioVendasResponse,
    FluxoCaixaDia,
    RelatorioFluxoCaixaResponse,
    EstoqueBaixo,
    RelatorioEstoqueBaixoResponse,
)
from app.modules.vendas.models import Venda, ItemVenda
from app.modules.produtos.models import Produto
from app.modules.financeiro.models import ContaPagar, ContaReceber


class RelatoriosService:
    """Service para relatórios e dashboard"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== DASHBOARD ====================

    async def get_dashboard(
        self, data_inicio: date, data_fim: date
    ) -> DashboardResponse:
        """
        Gera dashboard com principais KPIs

        Métricas incluídas:
        - Total de vendas e faturamento
        - Ticket médio
        - Variação vs período anterior
        - Produtos mais vendidos
        - Alertas de estoque
        - Contas a receber
        """
        vendas_data = await self.get_dashboard_vendas(data_inicio, data_fim)

        # Calcula KPIs
        kpis = [
            KPICard(
                titulo="Faturamento Total",
                valor=vendas_data.valor_total_vendas,
                unidade="R$",
                variacao_percentual=vendas_data.variacao_valor_percentual,
                icone="money",
            ),
            KPICard(
                titulo="Total de Vendas",
                valor=float(vendas_data.total_vendas),
                unidade="vendas",
                variacao_percentual=vendas_data.variacao_vendas_percentual,
                icone="cart",
            ),
            KPICard(
                titulo="Ticket Médio",
                valor=vendas_data.ticket_medio,
                unidade="R$",
                icone="receipt",
            ),
            KPICard(
                titulo="Produtos Abaixo do Mínimo",
                valor=float(vendas_data.total_produtos_abaixo_minimo),
                unidade="produtos",
                icone="alert",
            ),
            KPICard(
                titulo="Contas Vencidas",
                valor=vendas_data.total_contas_vencidas,
                unidade="R$",
                icone="warning",
            ),
        ]

        periodo_str = f"{data_inicio.strftime('%d/%m/%Y')} - {data_fim.strftime('%d/%m/%Y')}"

        return DashboardResponse(
            periodo=periodo_str,
            data_atualizacao=datetime.utcnow(),
            kpis=kpis,
            vendas=vendas_data,
        )

    async def get_dashboard_vendas(
        self, data_inicio: date, data_fim: date
    ) -> DashboardVendasResponse:
        """Gera dados de vendas para dashboard"""
        # Vendas do período
        query_vendas = select(
            func.count(Venda.id).label("total_vendas"),
            func.sum(Venda.valor_total).label("valor_total"),
        ).where(
            and_(
                Venda.data_venda >= data_inicio,
                Venda.data_venda <= data_fim,
                Venda.ativo == True,
            )
        )

        result = await self.session.execute(query_vendas)
        row = result.one()

        total_vendas = row.total_vendas or 0
        valor_total = float(row.valor_total or 0)
        ticket_medio = valor_total / total_vendas if total_vendas > 0 else 0

        # Período anterior (para comparação)
        dias_periodo = (data_fim - data_inicio).days + 1
        data_inicio_anterior = data_inicio - timedelta(days=dias_periodo)
        data_fim_anterior = data_inicio - timedelta(days=1)

        query_anterior = select(
            func.count(Venda.id).label("total_vendas"),
            func.sum(Venda.valor_total).label("valor_total"),
        ).where(
            and_(
                Venda.data_venda >= data_inicio_anterior,
                Venda.data_venda <= data_fim_anterior,
                Venda.ativo == True,
            )
        )

        result_anterior = await self.session.execute(query_anterior)
        row_anterior = result_anterior.one()

        total_vendas_anterior = row_anterior.total_vendas or 0
        valor_total_anterior = float(row_anterior.valor_total or 0)

        # Calcula variações
        variacao_vendas = 0.0
        if total_vendas_anterior > 0:
            variacao_vendas = ((total_vendas - total_vendas_anterior) / total_vendas_anterior) * 100

        variacao_valor = 0.0
        if valor_total_anterior > 0:
            variacao_valor = ((valor_total - valor_total_anterior) / valor_total_anterior) * 100

        # Produto mais vendido
        query_produto = (
            select(
                Produto.descricao,
                func.sum(ItemVenda.quantidade).label("total_quantidade"),
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(
                and_(
                    Venda.data_venda >= data_inicio,
                    Venda.data_venda <= data_fim,
                    Venda.ativo == True,
                )
            )
            .group_by(Produto.id, Produto.descricao)
            .order_by(func.sum(ItemVenda.quantidade).desc())
            .limit(1)
        )

        result_produto = await self.session.execute(query_produto)
        row_produto = result_produto.first()

        produto_mais_vendido = None
        qtd_mais_vendido = None
        if row_produto:
            produto_mais_vendido = row_produto.descricao
            qtd_mais_vendido = float(row_produto.total_quantidade)

        # Produtos em estoque
        query_estoque = select(func.count(Produto.id)).where(Produto.ativo == True)
        result_estoque = await self.session.execute(query_estoque)
        total_produtos = result_estoque.scalar() or 0

        # Produtos abaixo do mínimo
        query_abaixo = select(func.count(Produto.id)).where(
            and_(
                Produto.ativo == True,
                Produto.estoque_atual < Produto.estoque_minimo,
            )
        )
        result_abaixo = await self.session.execute(query_abaixo)
        total_abaixo_minimo = result_abaixo.scalar() or 0

        # Contas a receber
        query_receber = select(func.sum(ContaReceber.valor)).where(
            and_(
                ContaReceber.ativo == True,
                ContaReceber.data_pagamento.is_(None),
            )
        )
        result_receber = await self.session.execute(query_receber)
        total_receber = float(result_receber.scalar() or 0)

        # Contas vencidas
        query_vencidas = select(func.sum(ContaReceber.valor)).where(
            and_(
                ContaReceber.ativo == True,
                ContaReceber.data_pagamento.is_(None),
                ContaReceber.data_vencimento < date.today(),
            )
        )
        result_vencidas = await self.session.execute(query_vencidas)
        total_vencidas = float(result_vencidas.scalar() or 0)

        return DashboardVendasResponse(
            data_inicio=data_inicio,
            data_fim=data_fim,
            total_vendas=total_vendas,
            valor_total_vendas=round(valor_total, 2),
            ticket_medio=round(ticket_medio, 2),
            variacao_vendas_percentual=round(variacao_vendas, 2),
            variacao_valor_percentual=round(variacao_valor, 2),
            produto_mais_vendido=produto_mais_vendido,
            quantidade_produto_mais_vendido=qtd_mais_vendido,
            total_produtos_estoque=total_produtos,
            total_produtos_abaixo_minimo=total_abaixo_minimo,
            total_contas_receber=round(total_receber, 2),
            total_contas_vencidas=round(total_vencidas, 2),
        )

    # ==================== RELATÓRIOS ====================

    async def relatorio_vendedores(
        self, data_inicio: date, data_fim: date
    ) -> RelatorioVendedoresResponse:
        """
        Relatório de desempenho de vendedores

        Nota: Este é um exemplo simplificado.
        Assumindo que Venda tem campo vendedor_id (não implementado ainda).
        """
        # Simulação: retorna dados agregados
        return RelatorioVendedoresResponse(
            data_inicio=data_inicio,
            data_fim=data_fim,
            vendedores=[],
            total_geral=0,
        )

    async def relatorio_vendas(
        self, data_inicio: date, data_fim: date
    ) -> RelatorioVendasResponse:
        """Relatório de produtos vendidos no período"""
        query = (
            select(
                Produto.id,
                Produto.descricao,
                Produto.codigo_barras,
                func.sum(ItemVenda.quantidade).label("quantidade"),
                func.sum(ItemVenda.preco_total).label("valor_total"),
                func.count(Venda.id).label("numero_vendas"),
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(
                and_(
                    Venda.data_venda >= data_inicio,
                    Venda.data_venda <= data_fim,
                    Venda.ativo == True,
                )
            )
            .group_by(Produto.id, Produto.descricao, Produto.codigo_barras)
            .order_by(func.sum(ItemVenda.preco_total).desc())
        )

        result = await self.session.execute(query)
        rows = result.all()

        produtos = [
            ProdutoVendido(
                produto_id=row.id,
                produto_nome=row.descricao,
                codigo_barras=row.codigo_barras,
                quantidade_vendida=float(row.quantidade),
                valor_total=float(row.valor_total),
                quantidade_vendas=row.numero_vendas,
            )
            for row in rows
        ]

        total_quantidade = sum(p.quantidade_vendida for p in produtos)
        total_valor = sum(p.valor_total for p in produtos)

        return RelatorioVendasResponse(
            data_inicio=data_inicio,
            data_fim=data_fim,
            produtos=produtos,
            total_quantidade=round(total_quantidade, 2),
            total_valor=round(total_valor, 2),
        )

    async def relatorio_estoque_baixo(self) -> RelatorioEstoqueBaixoResponse:
        """Relatório de produtos com estoque abaixo do mínimo"""
        query = select(Produto).where(
            and_(
                Produto.ativo == True,
                Produto.estoque_atual < Produto.estoque_minimo,
            )
        ).order_by((Produto.estoque_minimo - Produto.estoque_atual).desc())

        result = await self.session.execute(query)
        produtos_obj = result.scalars().all()

        produtos = []
        for produto in produtos_obj:
            deficit = float(produto.estoque_minimo - produto.estoque_atual)
            valor_reposicao = deficit * float(produto.preco_custo)

            produtos.append(
                EstoqueBaixo(
                    produto_id=produto.id,
                    produto_nome=produto.descricao,
                    codigo_barras=produto.codigo_barras,
                    estoque_atual=float(produto.estoque_atual),
                    estoque_minimo=float(produto.estoque_minimo),
                    deficit=deficit,
                    valor_reposicao_estimado=round(valor_reposicao, 2),
                )
            )

        valor_total = sum(p.valor_reposicao_estimado for p in produtos)

        return RelatorioEstoqueBaixoResponse(
            produtos=produtos,
            total_produtos=len(produtos),
            valor_total_reposicao=round(valor_total, 2),
        )
