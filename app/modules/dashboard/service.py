"""
Dashboard Service - Business logic for dashboard endpoints
"""
from datetime import date, datetime, timedelta
from typing import List
from sqlalchemy import select, func, and_, or_, case, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.schemas import (
    DashboardStats,
    VendasPorDia,
    ProdutoMaisVendido,
    VendasPorVendedor,
    StatusPedidos,
)
from app.modules.pedidos_venda.models import PedidoVenda, ItemPedidoVenda, StatusPedidoVenda
from app.modules.vendas.models import Venda, ItemVenda
from app.modules.produtos.models import Produto
from app.modules.auth.models import User
from app.core.cache import cached


class DashboardService:
    """Service for dashboard data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self) -> DashboardStats:
        """
        Get main dashboard statistics

        Returns:
            DashboardStats with KPIs
        """
        hoje = date.today()
        inicio_mes = date(hoje.year, hoje.month, 1)

        # Calcula início do mês anterior para comparação
        if hoje.month == 1:
            inicio_mes_anterior = date(hoje.year - 1, 12, 1)
            fim_mes_anterior = date(hoje.year, 1, 1) - timedelta(days=1)
        else:
            inicio_mes_anterior = date(hoje.year, hoje.month - 1, 1)
            # Último dia do mês anterior
            fim_mes_anterior = inicio_mes - timedelta(days=1)

        # Vendas hoje (usando Venda model)
        query_hoje = select(func.count(Venda.id)).where(
            cast(Venda.data_venda, Date) == hoje
        )
        result_hoje = await self.db.execute(query_hoje)
        vendas_hoje = result_hoje.scalar() or 0

        # Vendas do mês
        query_mes = select(
            func.count(Venda.id),
            func.coalesce(func.sum(Venda.valor_total), 0.0),
        ).where(
            and_(
                cast(Venda.data_venda, Date) >= inicio_mes,
                cast(Venda.data_venda, Date) <= hoje,
            )
        )
        result_mes = await self.db.execute(query_mes)
        row_mes = result_mes.one()
        vendas_mes = row_mes[0] or 0
        faturamento_mes = float(row_mes[1] or 0.0)

        # Vendas do mês anterior para calcular crescimento
        query_mes_anterior = select(
            func.coalesce(func.sum(Venda.valor_total), 0.0)
        ).where(
            and_(
                cast(Venda.data_venda, Date) >= inicio_mes_anterior,
                cast(Venda.data_venda, Date) <= fim_mes_anterior,
            )
        )
        result_mes_anterior = await self.db.execute(query_mes_anterior)
        faturamento_mes_anterior = float(result_mes_anterior.scalar() or 0.0)

        # Calcula crescimento
        crescimento_mes = 0.0
        if faturamento_mes_anterior > 0:
            crescimento_mes = ((faturamento_mes - faturamento_mes_anterior) / faturamento_mes_anterior) * 100

        # Ticket médio
        ticket_medio = 0.0
        if vendas_mes > 0:
            ticket_medio = faturamento_mes / vendas_mes

        # Pedidos em aberto (status != FATURADO, CANCELADO, ENTREGUE)
        query_abertos = select(func.count(PedidoVenda.id)).where(
            PedidoVenda.status.not_in([
                StatusPedidoVenda.FATURADO,
                StatusPedidoVenda.CANCELADO,
                StatusPedidoVenda.ENTREGUE,
            ])
        )
        result_abertos = await self.db.execute(query_abertos)
        pedidos_abertos = result_abertos.scalar() or 0

        # Pedidos atrasados (data_entrega_prevista < hoje e status não finalizado)
        query_atrasados = select(func.count(PedidoVenda.id)).where(
            and_(
                PedidoVenda.data_entrega_prevista < hoje,
                PedidoVenda.status.not_in([
                    StatusPedidoVenda.FATURADO,
                    StatusPedidoVenda.CANCELADO,
                    StatusPedidoVenda.ENTREGUE,
                ])
            )
        )
        result_atrasados = await self.db.execute(query_atrasados)
        pedidos_atrasados = result_atrasados.scalar() or 0

        # Meta do mês (pode ser configurável, por enquanto hardcoded)
        meta_mes = faturamento_mes_anterior * 1.1  # 10% acima do mês anterior

        return DashboardStats(
            vendas_hoje=vendas_hoje,
            vendas_mes=vendas_mes,
            pedidos_abertos=pedidos_abertos,
            pedidos_atrasados=pedidos_atrasados,
            ticket_medio=round(ticket_medio, 2),
            faturamento_mes=round(faturamento_mes, 2),
            crescimento_mes=round(crescimento_mes, 2),
            meta_mes=round(meta_mes, 2),
        )

    async def get_vendas_por_dia(self, dias: int = 30) -> List[VendasPorDia]:
        """
        Get sales grouped by day for the last N days

        Args:
            dias: Number of days to look back

        Returns:
            List of VendasPorDia
        """
        data_inicio = date.today() - timedelta(days=dias)
        data_fim = date.today()

        query = (
            select(
                cast(Venda.data_venda, Date).label("data"),
                func.count(Venda.id).label("vendas"),
                func.coalesce(func.sum(Venda.valor_total), 0.0).label("faturamento"),
            )
            .where(
                and_(
                    cast(Venda.data_venda, Date) >= data_inicio,
                    cast(Venda.data_venda, Date) <= data_fim,
                )
            )
            .group_by(cast(Venda.data_venda, Date))
            .order_by(cast(Venda.data_venda, Date))
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Cria mapa de vendas por dia
        vendas_map = {
            row.data: VendasPorDia(
                data=row.data.isoformat(),
                vendas=row.vendas,
                faturamento=round(float(row.faturamento), 2),
            )
            for row in rows
        }

        # Preenche dias sem vendas com zero
        vendas_lista = []
        current_date = data_inicio
        while current_date <= data_fim:
            if current_date in vendas_map:
                vendas_lista.append(vendas_map[current_date])
            else:
                vendas_lista.append(
                    VendasPorDia(
                        data=current_date.isoformat(),
                        vendas=0,
                        faturamento=0.0,
                    )
                )
            current_date += timedelta(days=1)

        return vendas_lista

    async def get_produtos_mais_vendidos(self, limit: int = 10) -> List[ProdutoMaisVendido]:
        """
        Get top selling products for the current month

        Args:
            limit: Number of products to return

        Returns:
            List of ProdutoMaisVendido
        """
        hoje = date.today()
        inicio_mes = date(hoje.year, hoje.month, 1)

        query = (
            select(
                Produto.id,
                Produto.descricao,
                func.sum(ItemVenda.quantidade).label("quantidade"),
                func.sum(ItemVenda.total_item).label("faturamento"),
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(
                and_(
                    cast(Venda.data_venda, Date) >= inicio_mes,
                    cast(Venda.data_venda, Date) <= hoje,
                )
            )
            .group_by(Produto.id, Produto.descricao)
            .order_by(func.sum(ItemVenda.quantidade).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            ProdutoMaisVendido(
                produto_id=row.id,
                produto_nome=row.descricao,
                quantidade=round(float(row.quantidade), 2),
                faturamento=round(float(row.faturamento), 2),
            )
            for row in rows
        ]

    async def get_vendas_por_vendedor(self) -> List[VendasPorVendedor]:
        """
        Get sales grouped by seller for the current month

        Returns:
            List of VendasPorVendedor
        """
        hoje = date.today()
        inicio_mes = date(hoje.year, hoje.month, 1)

        query = (
            select(
                User.id,
                User.nome,
                func.count(Venda.id).label("total_vendas"),
                func.coalesce(func.avg(Venda.valor_total), 0.0).label("ticket_medio"),
            )
            .join(Venda, Venda.vendedor_id == User.id)
            .where(
                and_(
                    cast(Venda.data_venda, Date) >= inicio_mes,
                    cast(Venda.data_venda, Date) <= hoje,
                )
            )
            .group_by(User.id, User.nome)
            .order_by(func.count(Venda.id).desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            VendasPorVendedor(
                vendedor_id=row.id,
                vendedor_nome=row.nome,
                total_vendas=row.total_vendas,
                ticket_medio=round(float(row.ticket_medio), 2),
            )
            for row in rows
        ]

    async def get_status_pedidos(self) -> List[StatusPedidos]:
        """
        Get orders grouped by status

        Returns:
            List of StatusPedidos
        """
        query = (
            select(
                PedidoVenda.status,
                func.count(PedidoVenda.id).label("quantidade"),
                func.coalesce(func.sum(PedidoVenda.valor_total), 0.0).label("valor_total"),
            )
            .group_by(PedidoVenda.status)
            .order_by(PedidoVenda.status)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            StatusPedidos(
                status=row.status.value,
                quantidade=row.quantidade,
                valor_total=round(float(row.valor_total), 2),
            )
            for row in rows
        ]
