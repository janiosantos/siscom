"""
Service de Relatórios Avançados
"""
from datetime import date, timedelta
from typing import List
from sqlalchemy import select, func, and_, cast, Date, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.relatorios_avancados.schemas import (
    RelatorioVendasPorPeriodoResponse,
    VendaDiaria,
    RelatorioDesempenhoVendedoresResponse,
    VendedorDesempenho,
    RelatorioProdutosMaisVendidosResponse,
    ProdutoMaisVendido,
    RelatorioCurvaABCResponse,
    ClasseABC,
    ClienteCurvaABC,
    RelatorioMargemLucroResponse,
    MargemCategoria,
)
from app.modules.vendas.models import Venda, ItemVenda
from app.modules.produtos.models import Produto
from app.modules.categorias.models import Categoria
from app.modules.clientes.models import Cliente
from app.modules.auth.models import User


class RelatoriosAvancadosService:
    """Service para relatórios avançados"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def relatorio_vendas_por_periodo(
        self,
        data_inicio: date,
        data_fim: date,
        vendedor_id: int | None = None,
        cliente_id: int | None = None,
    ) -> RelatorioVendasPorPeriodoResponse:
        """
        Gera relatório de vendas por período com comparação vs período anterior

        Args:
            data_inicio: Data início
            data_fim: Data fim
            vendedor_id: Filtro opcional por vendedor
            cliente_id: Filtro opcional por cliente

        Returns:
            RelatorioVendasPorPeriodoResponse
        """
        # Build base query
        filters = [
            cast(Venda.data_venda, Date) >= data_inicio,
            cast(Venda.data_venda, Date) <= data_fim,
        ]

        if vendedor_id:
            filters.append(Venda.vendedor_id == vendedor_id)
        if cliente_id:
            filters.append(Venda.cliente_id == cliente_id)

        # Totais do período
        query_totais = select(
            func.count(Venda.id).label("total_vendas"),
            func.coalesce(func.sum(Venda.valor_total), 0.0).label("faturamento"),
            func.count(distinct(Venda.cliente_id)).label("clientes_unicos"),
        ).where(and_(*filters))

        result_totais = await self.db.execute(query_totais)
        row_totais = result_totais.one()

        total_vendas = row_totais.total_vendas or 0
        faturamento_total = float(row_totais.faturamento or 0.0)
        clientes_atendidos = row_totais.clientes_unicos or 0
        ticket_medio = faturamento_total / total_vendas if total_vendas > 0 else 0.0

        # Período anterior para comparação
        dias_periodo = (data_fim - data_inicio).days + 1
        data_inicio_anterior = data_inicio - timedelta(days=dias_periodo)
        data_fim_anterior = data_inicio - timedelta(days=1)

        filters_anterior = [
            cast(Venda.data_venda, Date) >= data_inicio_anterior,
            cast(Venda.data_venda, Date) <= data_fim_anterior,
        ]
        if vendedor_id:
            filters_anterior.append(Venda.vendedor_id == vendedor_id)
        if cliente_id:
            filters_anterior.append(Venda.cliente_id == cliente_id)

        query_anterior = select(
            func.count(Venda.id).label("total_vendas"),
            func.coalesce(func.sum(Venda.valor_total), 0.0).label("faturamento"),
        ).where(and_(*filters_anterior))

        result_anterior = await self.db.execute(query_anterior)
        row_anterior = result_anterior.one()

        total_vendas_anterior = row_anterior.total_vendas or 0
        faturamento_anterior = float(row_anterior.faturamento or 0.0)

        # Calcular variações
        variacao_vendas = 0.0
        if total_vendas_anterior > 0:
            variacao_vendas = ((total_vendas - total_vendas_anterior) / total_vendas_anterior) * 100

        variacao_faturamento = 0.0
        if faturamento_anterior > 0:
            variacao_faturamento = ((faturamento_total - faturamento_anterior) / faturamento_anterior) * 100

        # Vendas diárias
        query_diarias = (
            select(
                cast(Venda.data_venda, Date).label("data"),
                func.count(Venda.id).label("vendas"),
                func.coalesce(func.sum(Venda.valor_total), 0.0).label("faturamento"),
            )
            .where(and_(*filters))
            .group_by(cast(Venda.data_venda, Date))
            .order_by(cast(Venda.data_venda, Date))
        )

        result_diarias = await self.db.execute(query_diarias)
        rows_diarias = result_diarias.all()

        vendas_diarias_map = {
            row.data: VendaDiaria(
                data=row.data.isoformat(),
                vendas=row.vendas,
                faturamento=round(float(row.faturamento), 2),
                ticket_medio=round(float(row.faturamento) / row.vendas, 2) if row.vendas > 0 else 0.0,
            )
            for row in rows_diarias
        }

        # Preencher dias vazios
        vendas_diarias = []
        current_date = data_inicio
        while current_date <= data_fim:
            if current_date in vendas_diarias_map:
                vendas_diarias.append(vendas_diarias_map[current_date])
            else:
                vendas_diarias.append(
                    VendaDiaria(
                        data=current_date.isoformat(),
                        vendas=0,
                        faturamento=0.0,
                        ticket_medio=0.0,
                    )
                )
            current_date += timedelta(days=1)

        return RelatorioVendasPorPeriodoResponse(
            data_inicio=data_inicio.isoformat(),
            data_fim=data_fim.isoformat(),
            total_vendas=total_vendas,
            faturamento_total=round(faturamento_total, 2),
            ticket_medio=round(ticket_medio, 2),
            clientes_atendidos=clientes_atendidos,
            variacao_vendas_percent=round(variacao_vendas, 2),
            variacao_faturamento_percent=round(variacao_faturamento, 2),
            vendas_diarias=vendas_diarias,
        )

    async def relatorio_desempenho_vendedores(
        self,
        data_inicio: date,
        data_fim: date,
    ) -> RelatorioDesempenhoVendedoresResponse:
        """
        Gera relatório de desempenho de vendedores

        Args:
            data_inicio: Data início
            data_fim: Data fim

        Returns:
            RelatorioDesempenhoVendedoresResponse
        """
        query = (
            select(
                User.id,
                User.nome,
                func.count(Venda.id).label("total_vendas"),
                func.coalesce(func.sum(Venda.valor_total), 0.0).label("faturamento"),
                func.coalesce(func.avg(Venda.valor_total), 0.0).label("ticket_medio"),
            )
            .join(Venda, Venda.vendedor_id == User.id)
            .where(
                and_(
                    cast(Venda.data_venda, Date) >= data_inicio,
                    cast(Venda.data_venda, Date) <= data_fim,
                )
            )
            .group_by(User.id, User.nome)
            .order_by(func.sum(Venda.valor_total).desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        vendedores = [
            VendedorDesempenho(
                vendedor_id=row.id,
                vendedor_nome=row.nome,
                total_vendas=row.total_vendas,
                faturamento_total=round(float(row.faturamento), 2),
                ticket_medio=round(float(row.ticket_medio), 2),
                comissao_estimada=round(float(row.faturamento) * 0.05, 2),  # 5% comissão
            )
            for row in rows
        ]

        total_geral = sum(v.faturamento_total for v in vendedores)

        return RelatorioDesempenhoVendedoresResponse(
            data_inicio=data_inicio.isoformat(),
            data_fim=data_fim.isoformat(),
            vendedores=vendedores,
            total_geral=round(total_geral, 2),
        )

    async def relatorio_produtos_mais_vendidos(
        self,
        data_inicio: date,
        data_fim: date,
        limit: int = 50,
    ) -> RelatorioProdutosMaisVendidosResponse:
        """
        Gera relatório de produtos mais vendidos

        Args:
            data_inicio: Data início
            data_fim: Data fim
            limit: Número máximo de produtos

        Returns:
            RelatorioProdutosMaisVendidosResponse
        """
        query = (
            select(
                Produto.id,
                Produto.descricao,
                Produto.codigo_barras,
                func.sum(ItemVenda.quantidade).label("quantidade"),
                func.sum(ItemVenda.total_item).label("faturamento"),
                func.count(distinct(Venda.id)).label("num_vendas"),
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(
                and_(
                    cast(Venda.data_venda, Date) >= data_inicio,
                    cast(Venda.data_venda, Date) <= data_fim,
                )
            )
            .group_by(Produto.id, Produto.descricao, Produto.codigo_barras)
            .order_by(func.sum(ItemVenda.quantidade).desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        produtos = [
            ProdutoMaisVendido(
                produto_id=row.id,
                produto_nome=row.descricao,
                produto_codigo=row.codigo_barras,
                quantidade_vendida=round(float(row.quantidade), 2),
                faturamento=round(float(row.faturamento), 2),
                quantidade_vendas=row.num_vendas,
            )
            for row in rows
        ]

        total_quantidade = sum(p.quantidade_vendida for p in produtos)
        total_faturamento = sum(p.faturamento for p in produtos)

        return RelatorioProdutosMaisVendidosResponse(
            data_inicio=data_inicio.isoformat(),
            data_fim=data_fim.isoformat(),
            produtos=produtos,
            total_quantidade=round(total_quantidade, 2),
            total_faturamento=round(total_faturamento, 2),
        )

    async def relatorio_curva_abc_clientes(
        self,
        data_inicio: date,
        data_fim: date,
    ) -> RelatorioCurvaABCResponse:
        """
        Gera relatório de Curva ABC de clientes

        Classificação:
        - Classe A: 80% do faturamento (top clientes)
        - Classe B: 15% do faturamento
        - Classe C: 5% do faturamento

        Args:
            data_inicio: Data início
            data_fim: Data fim

        Returns:
            RelatorioCurvaABCResponse
        """
        # Query para obter faturamento por cliente
        query = (
            select(
                Cliente.id,
                Cliente.nome,
                func.coalesce(func.sum(Venda.valor_total), 0.0).label("faturamento"),
                func.count(Venda.id).label("quantidade_compras"),
            )
            .join(Venda, Venda.cliente_id == Cliente.id)
            .where(
                and_(
                    cast(Venda.data_venda, Date) >= data_inicio,
                    cast(Venda.data_venda, Date) <= data_fim,
                )
            )
            .group_by(Cliente.id, Cliente.nome)
            .order_by(func.sum(Venda.valor_total).desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        # Calcular faturamento total
        faturamento_total = sum(float(row.faturamento) for row in rows)

        # Classificar clientes em ABC
        clientes_classificados = []
        acumulado = 0.0

        for row in rows:
            faturamento_cliente = float(row.faturamento)
            acumulado += faturamento_cliente
            percentual_acumulado = (acumulado / faturamento_total * 100) if faturamento_total > 0 else 0

            # Determinar classe
            if percentual_acumulado <= 80:
                classe = "A"
            elif percentual_acumulado <= 95:
                classe = "B"
            else:
                classe = "C"

            ticket_medio = faturamento_cliente / row.quantidade_compras if row.quantidade_compras > 0 else 0

            clientes_classificados.append(
                ClienteCurvaABC(
                    cliente_id=row.id,
                    cliente_nome=row.nome,
                    classe=classe,
                    faturamento=round(faturamento_cliente, 2),
                    quantidade_compras=row.quantidade_compras,
                    ticket_medio=round(ticket_medio, 2),
                )
            )

        # Agrupar por classe
        classe_a_clientes = [c for c in clientes_classificados if c.classe == "A"]
        classe_b_clientes = [c for c in clientes_classificados if c.classe == "B"]
        classe_c_clientes = [c for c in clientes_classificados if c.classe == "C"]

        faturamento_a = sum(c.faturamento for c in classe_a_clientes)
        faturamento_b = sum(c.faturamento for c in classe_b_clientes)
        faturamento_c = sum(c.faturamento for c in classe_c_clientes)

        classe_a = ClasseABC(
            classe="A",
            quantidade_clientes=len(classe_a_clientes),
            faturamento_total=round(faturamento_a, 2),
            percentual_faturamento=round((faturamento_a / faturamento_total * 100) if faturamento_total > 0 else 0, 2),
        )

        classe_b = ClasseABC(
            classe="B",
            quantidade_clientes=len(classe_b_clientes),
            faturamento_total=round(faturamento_b, 2),
            percentual_faturamento=round((faturamento_b / faturamento_total * 100) if faturamento_total > 0 else 0, 2),
        )

        classe_c = ClasseABC(
            classe="C",
            quantidade_clientes=len(classe_c_clientes),
            faturamento_total=round(faturamento_c, 2),
            percentual_faturamento=round((faturamento_c / faturamento_total * 100) if faturamento_total > 0 else 0, 2),
        )

        return RelatorioCurvaABCResponse(
            data_inicio=data_inicio.isoformat(),
            data_fim=data_fim.isoformat(),
            classe_a=classe_a,
            classe_b=classe_b,
            classe_c=classe_c,
            clientes=clientes_classificados,
        )

    async def relatorio_margem_lucro(
        self,
        data_inicio: date,
        data_fim: date,
    ) -> RelatorioMargemLucroResponse:
        """
        Gera relatório de análise de margem de lucro por categoria

        Args:
            data_inicio: Data início
            data_fim: Data fim

        Returns:
            RelatorioMargemLucroResponse
        """
        query = (
            select(
                Categoria.id,
                Categoria.descricao,
                func.sum(ItemVenda.total_item).label("faturamento"),
                func.sum(ItemVenda.quantidade * Produto.preco_custo).label("custo"),
            )
            .join(Produto, Produto.categoria_id == Categoria.id)
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(
                and_(
                    cast(Venda.data_venda, Date) >= data_inicio,
                    cast(Venda.data_venda, Date) <= data_fim,
                )
            )
            .group_by(Categoria.id, Categoria.descricao)
            .order_by(func.sum(ItemVenda.total_item).desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        categorias = []
        faturamento_total = 0.0
        custo_total = 0.0

        for row in rows:
            faturamento_cat = float(row.faturamento or 0.0)
            custo_cat = float(row.custo or 0.0)
            lucro_cat = faturamento_cat - custo_cat
            margem_cat = (lucro_cat / faturamento_cat * 100) if faturamento_cat > 0 else 0.0

            categorias.append(
                MargemCategoria(
                    categoria_id=row.id,
                    categoria_nome=row.descricao,
                    faturamento=round(faturamento_cat, 2),
                    custo_total=round(custo_cat, 2),
                    lucro_bruto=round(lucro_cat, 2),
                    margem_percentual=round(margem_cat, 2),
                )
            )

            faturamento_total += faturamento_cat
            custo_total += custo_cat

        lucro_bruto = faturamento_total - custo_total
        margem_media = (lucro_bruto / faturamento_total * 100) if faturamento_total > 0 else 0.0

        return RelatorioMargemLucroResponse(
            data_inicio=data_inicio.isoformat(),
            data_fim=data_fim.isoformat(),
            faturamento_total=round(faturamento_total, 2),
            custo_total=round(custo_total, 2),
            lucro_bruto=round(lucro_bruto, 2),
            margem_media=round(margem_media, 2),
            categorias=categorias,
        )
