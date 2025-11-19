"""
Service Layer para Análise de Curva ABC
"""
from typing import List
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.estoque.schemas import (
    CurvaABCResponse,
    CurvaABCItem,
    ClassificacaoABC,
)
from app.modules.vendas.models import Venda, ItemVenda, StatusVenda
from app.modules.produtos.models import Produto


class CurvaABCService:
    """Service para análise de Curva ABC de produtos"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def calcular_curva_abc(
        self, periodo_meses: int = 6
    ) -> CurvaABCResponse:
        """
        Calcula a Curva ABC de produtos baseada nas vendas dos últimos N meses

        Classificação:
        - Classe A: Produtos que representam 80% do faturamento (aproximadamente 20% dos produtos)
        - Classe B: Produtos que representam os próximos 15% do faturamento (aproximadamente 30% dos produtos)
        - Classe C: Produtos que representam os últimos 5% do faturamento (aproximadamente 50% dos produtos)

        Args:
            periodo_meses: Número de meses para análise (padrão: 6)

        Returns:
            CurvaABCResponse com análise completa
        """
        # Calcula período de análise
        data_fim = date.today()
        data_inicio = data_fim - timedelta(days=periodo_meses * 30)

        # Query para buscar vendas do período
        # Agrupa por produto e soma quantidade vendida e valor total
        query = (
            select(
                ItemVenda.produto_id,
                Produto.descricao,
                Produto.codigo_barras,
                func.sum(ItemVenda.quantidade).label("quantidade_vendida"),
                func.sum(ItemVenda.total_item).label("valor_total_vendido"),
            )
            .join(Venda, ItemVenda.venda_id == Venda.id)
            .join(Produto, ItemVenda.produto_id == Produto.id)
            .where(
                Venda.data_venda >= data_inicio,
                Venda.data_venda <= data_fim,
                Venda.status == StatusVenda.FINALIZADA,
            )
            .group_by(
                ItemVenda.produto_id,
                Produto.descricao,
                Produto.codigo_barras,
            )
            .order_by(func.sum(ItemVenda.total_item).desc())
        )

        result = await self.session.execute(query)
        vendas_por_produto = result.all()

        # Se não houver vendas, retorna vazio
        if not vendas_por_produto:
            return CurvaABCResponse(
                periodo_meses=periodo_meses,
                data_inicio=data_inicio,
                data_fim=data_fim,
                faturamento_total=0.0,
                total_produtos=0,
                produtos_classe_a=0,
                produtos_classe_b=0,
                produtos_classe_c=0,
                items=[],
            )

        # Calcula faturamento total
        faturamento_total = sum(float(v.valor_total_vendido) for v in vendas_por_produto)

        # Cria lista de itens com percentuais
        items: List[CurvaABCItem] = []
        percentual_acumulado = 0.0

        for posicao, venda in enumerate(vendas_por_produto, start=1):
            valor_vendido = float(venda.valor_total_vendido)
            percentual_faturamento = (
                (valor_vendido / faturamento_total * 100) if faturamento_total > 0 else 0.0
            )
            percentual_acumulado += percentual_faturamento

            # Determina classificação ABC baseada no percentual acumulado
            if percentual_acumulado <= 80.0:
                classificacao = ClassificacaoABC.A
            elif percentual_acumulado <= 95.0:
                classificacao = ClassificacaoABC.B
            else:
                classificacao = ClassificacaoABC.C

            item = CurvaABCItem(
                produto_id=venda.produto_id,
                produto_descricao=venda.descricao,
                codigo_barras=venda.codigo_barras,
                quantidade_vendida=float(venda.quantidade_vendida),
                valor_total_vendido=round(valor_vendido, 2),
                percentual_faturamento=round(percentual_faturamento, 2),
                percentual_acumulado=round(percentual_acumulado, 2),
                classificacao=classificacao,
                posicao_ranking=posicao,
            )
            items.append(item)

        # Conta produtos por classificação
        produtos_classe_a = sum(1 for item in items if item.classificacao == ClassificacaoABC.A)
        produtos_classe_b = sum(1 for item in items if item.classificacao == ClassificacaoABC.B)
        produtos_classe_c = sum(1 for item in items if item.classificacao == ClassificacaoABC.C)

        return CurvaABCResponse(
            periodo_meses=periodo_meses,
            data_inicio=data_inicio,
            data_fim=data_fim,
            faturamento_total=round(faturamento_total, 2),
            total_produtos=len(items),
            produtos_classe_a=produtos_classe_a,
            produtos_classe_b=produtos_classe_b,
            produtos_classe_c=produtos_classe_c,
            items=items,
        )

    async def get_produtos_curva_a(
        self, periodo_meses: int = 6
    ) -> List[CurvaABCItem]:
        """
        Retorna apenas produtos da classe A

        Args:
            periodo_meses: Número de meses para análise (padrão: 6)

        Returns:
            Lista de produtos classe A
        """
        curva_abc = await self.calcular_curva_abc(periodo_meses)
        return [item for item in curva_abc.items if item.classificacao == ClassificacaoABC.A]

    async def get_produtos_curva_b(
        self, periodo_meses: int = 6
    ) -> List[CurvaABCItem]:
        """
        Retorna apenas produtos da classe B

        Args:
            periodo_meses: Número de meses para análise (padrão: 6)

        Returns:
            Lista de produtos classe B
        """
        curva_abc = await self.calcular_curva_abc(periodo_meses)
        return [item for item in curva_abc.items if item.classificacao == ClassificacaoABC.B]

    async def get_produtos_curva_c(
        self, periodo_meses: int = 6
    ) -> List[CurvaABCItem]:
        """
        Retorna apenas produtos da classe C

        Args:
            periodo_meses: Número de meses para análise (padrão: 6)

        Returns:
            Lista de produtos classe C
        """
        curva_abc = await self.calcular_curva_abc(periodo_meses)
        return [item for item in curva_abc.items if item.classificacao == ClassificacaoABC.C]
