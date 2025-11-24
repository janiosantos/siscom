"""
Dashboards pré-configurados para Metabase
Queries SQL prontas para análise de dados do ERP
"""

# ============================================================================
# DASHBOARD 1: VISÃO GERAL - KPIs PRINCIPAIS
# ============================================================================

DASHBOARD_OVERVIEW = {
    "name": "📊 Visão Geral - KPIs Principais",
    "description": "Métricas principais do negócio em tempo real",
    "cards": [
        {
            "name": "Faturamento Mensal",
            "query": """
                SELECT
                    DATE_TRUNC('month', data_venda) as mes,
                    SUM(valor_total) as faturamento
                FROM vendas
                WHERE data_venda >= CURRENT_DATE - INTERVAL '12 months'
                    AND status != 'CANCELADA'
                GROUP BY mes
                ORDER BY mes DESC
            """,
            "visualization": "line",
            "description": "Evolução do faturamento nos últimos 12 meses"
        },
        {
            "name": "Vendas Hoje",
            "query": """
                SELECT
                    COUNT(*) as total_vendas,
                    SUM(valor_total) as valor_total,
                    AVG(valor_total) as ticket_medio
                FROM vendas
                WHERE DATE(data_venda) = CURRENT_DATE
                    AND status != 'CANCELADA'
            """,
            "visualization": "scalar",
            "description": "Vendas realizadas hoje"
        },
        {
            "name": "Top 10 Produtos Mais Vendidos",
            "query": """
                SELECT
                    p.descricao as produto,
                    SUM(vi.quantidade) as quantidade_vendida,
                    SUM(vi.quantidade * vi.preco_unitario) as faturamento
                FROM vendas_itens vi
                JOIN produtos p ON vi.produto_id = p.id
                JOIN vendas v ON vi.venda_id = v.id
                WHERE v.data_venda >= CURRENT_DATE - INTERVAL '30 days'
                    AND v.status != 'CANCELADA'
                GROUP BY p.id, p.descricao
                ORDER BY quantidade_vendida DESC
                LIMIT 10
            """,
            "visualization": "bar",
            "description": "Produtos mais vendidos nos últimos 30 dias"
        },
        {
            "name": "Novos Clientes por Mês",
            "query": """
                SELECT
                    DATE_TRUNC('month', created_at) as mes,
                    COUNT(*) as novos_clientes
                FROM clientes
                WHERE created_at >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY mes
                ORDER BY mes DESC
            """,
            "visualization": "area",
            "description": "Evolução de novos clientes"
        }
    ]
}

# ============================================================================
# DASHBOARD 2: FINANCEIRO
# ============================================================================

DASHBOARD_FINANCEIRO = {
    "name": "💰 Financeiro - Contas a Pagar e Receber",
    "description": "Análise detalhada do fluxo de caixa",
    "cards": [
        {
            "name": "Contas a Receber - Vencimento",
            "query": """
                SELECT
                    CASE
                        WHEN data_vencimento < CURRENT_DATE THEN 'Vencidas'
                        WHEN data_vencimento = CURRENT_DATE THEN 'Vence Hoje'
                        WHEN data_vencimento <= CURRENT_DATE + INTERVAL '7 days' THEN 'Próximos 7 dias'
                        WHEN data_vencimento <= CURRENT_DATE + INTERVAL '30 days' THEN 'Próximos 30 dias'
                        ELSE 'Futuros'
                    END as periodo,
                    COUNT(*) as quantidade,
                    SUM(valor) as valor_total
                FROM contas_receber
                WHERE status = 'PENDENTE'
                GROUP BY periodo
                ORDER BY
                    CASE periodo
                        WHEN 'Vencidas' THEN 1
                        WHEN 'Vence Hoje' THEN 2
                        WHEN 'Próximos 7 dias' THEN 3
                        WHEN 'Próximos 30 dias' THEN 4
                        ELSE 5
                    END
            """,
            "visualization": "pie",
            "description": "Distribuição de contas a receber por vencimento"
        },
        {
            "name": "Fluxo de Caixa Projetado (30 dias)",
            "query": """
                SELECT
                    data,
                    SUM(entradas) as entradas,
                    SUM(saidas) as saidas,
                    SUM(saldo_acumulado) as saldo
                FROM (
                    SELECT
                        data_vencimento as data,
                        SUM(valor) as entradas,
                        0 as saidas,
                        0 as saldo_acumulado
                    FROM contas_receber
                    WHERE data_vencimento BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
                        AND status = 'PENDENTE'
                    GROUP BY data_vencimento

                    UNION ALL

                    SELECT
                        data_vencimento as data,
                        0 as entradas,
                        SUM(valor) as saidas,
                        0 as saldo_acumulado
                    FROM contas_pagar
                    WHERE data_vencimento BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
                        AND status = 'PENDENTE'
                    GROUP BY data_vencimento
                ) fluxo
                GROUP BY data
                ORDER BY data
            """,
            "visualization": "line",
            "description": "Previsão de entradas e saídas nos próximos 30 dias"
        },
        {
            "name": "Taxa de Inadimplência",
            "query": """
                SELECT
                    DATE_TRUNC('month', data_vencimento) as mes,
                    COUNT(*) FILTER (WHERE data_vencimento < CURRENT_DATE AND status = 'PENDENTE') * 100.0 /
                        NULLIF(COUNT(*), 0) as taxa_inadimplencia
                FROM contas_receber
                WHERE data_vencimento >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY mes
                ORDER BY mes DESC
            """,
            "visualization": "line",
            "description": "Evolução da taxa de inadimplência"
        }
    ]
}

# ============================================================================
# DASHBOARD 3: ESTOQUE
# ============================================================================

DASHBOARD_ESTOQUE = {
    "name": "📦 Estoque - Gestão de Inventário",
    "description": "Análise de estoque, curva ABC e alertas",
    "cards": [
        {
            "name": "Produtos com Estoque Baixo",
            "query": """
                SELECT
                    p.codigo,
                    p.descricao,
                    e.quantidade_atual,
                    e.estoque_minimo,
                    (e.estoque_minimo - e.quantidade_atual) as quantidade_repor
                FROM produtos p
                JOIN estoque e ON p.id = e.produto_id
                WHERE e.quantidade_atual < e.estoque_minimo
                ORDER BY quantidade_repor DESC
                LIMIT 20
            """,
            "visualization": "table",
            "description": "Produtos que precisam de reposição urgente"
        },
        {
            "name": "Curva ABC - Classificação de Produtos",
            "query": """
                WITH vendas_produto AS (
                    SELECT
                        p.id,
                        p.descricao,
                        SUM(vi.quantidade * vi.preco_unitario) as faturamento
                    FROM produtos p
                    LEFT JOIN vendas_itens vi ON p.id = vi.produto_id
                    LEFT JOIN vendas v ON vi.venda_id = v.id
                    WHERE v.data_venda >= CURRENT_DATE - INTERVAL '90 days'
                        AND v.status != 'CANCELADA'
                    GROUP BY p.id, p.descricao
                ),
                ranking AS (
                    SELECT
                        descricao,
                        faturamento,
                        SUM(faturamento) OVER (ORDER BY faturamento DESC) * 100.0 /
                            SUM(faturamento) OVER () as percentual_acumulado
                    FROM vendas_produto
                    WHERE faturamento > 0
                )
                SELECT
                    descricao,
                    faturamento,
                    CASE
                        WHEN percentual_acumulado <= 80 THEN 'A'
                        WHEN percentual_acumulado <= 95 THEN 'B'
                        ELSE 'C'
                    END as classificacao
                FROM ranking
                ORDER BY faturamento DESC
            """,
            "visualization": "table",
            "description": "Classificação ABC dos produtos por faturamento"
        },
        {
            "name": "Valor Total em Estoque por Categoria",
            "query": """
                SELECT
                    c.descricao as categoria,
                    SUM(e.quantidade_atual * p.preco_custo) as valor_estoque
                FROM categorias c
                JOIN produtos p ON c.id = p.categoria_id
                JOIN estoque e ON p.id = e.produto_id
                GROUP BY c.id, c.descricao
                ORDER BY valor_estoque DESC
            """,
            "visualization": "pie",
            "description": "Distribuição do valor em estoque por categoria"
        },
        {
            "name": "Giro de Estoque (últimos 90 dias)",
            "query": """
                SELECT
                    p.descricao,
                    e.quantidade_atual as estoque_atual,
                    COALESCE(SUM(vi.quantidade), 0) as quantidade_vendida,
                    CASE
                        WHEN e.quantidade_atual > 0
                        THEN ROUND((COALESCE(SUM(vi.quantidade), 0) / e.quantidade_atual)::numeric, 2)
                        ELSE 0
                    END as giro
                FROM produtos p
                JOIN estoque e ON p.id = e.produto_id
                LEFT JOIN vendas_itens vi ON p.id = vi.produto_id
                LEFT JOIN vendas v ON vi.venda_id = v.id
                    AND v.data_venda >= CURRENT_DATE - INTERVAL '90 days'
                    AND v.status != 'CANCELADA'
                WHERE e.quantidade_atual > 0
                GROUP BY p.id, p.descricao, e.quantidade_atual
                ORDER BY giro DESC
                LIMIT 50
            """,
            "visualization": "table",
            "description": "Produtos com melhor e pior giro de estoque"
        }
    ]
}

# ============================================================================
# DASHBOARD 4: VENDAS E CLIENTES
# ============================================================================

DASHBOARD_VENDAS = {
    "name": "🛒 Vendas e Clientes",
    "description": "Análise de desempenho de vendas e comportamento de clientes",
    "cards": [
        {
            "name": "Vendas por Dia da Semana",
            "query": """
                SELECT
                    TO_CHAR(data_venda, 'Day') as dia_semana,
                    EXTRACT(DOW FROM data_venda) as ordem,
                    COUNT(*) as total_vendas,
                    SUM(valor_total) as faturamento,
                    AVG(valor_total) as ticket_medio
                FROM vendas
                WHERE data_venda >= CURRENT_DATE - INTERVAL '90 days'
                    AND status != 'CANCELADA'
                GROUP BY dia_semana, ordem
                ORDER BY ordem
            """,
            "visualization": "bar",
            "description": "Padrão de vendas por dia da semana"
        },
        {
            "name": "Top 20 Clientes por Faturamento",
            "query": """
                SELECT
                    c.nome,
                    COUNT(DISTINCT v.id) as total_compras,
                    SUM(v.valor_total) as faturamento_total,
                    AVG(v.valor_total) as ticket_medio,
                    MAX(v.data_venda) as ultima_compra
                FROM clientes c
                JOIN vendas v ON c.id = v.cliente_id
                WHERE v.data_venda >= CURRENT_DATE - INTERVAL '12 months'
                    AND v.status != 'CANCELADA'
                GROUP BY c.id, c.nome
                ORDER BY faturamento_total DESC
                LIMIT 20
            """,
            "visualization": "table",
            "description": "Principais clientes do último ano"
        },
        {
            "name": "Funil de Vendas",
            "query": """
                SELECT
                    'Orçamentos Criados' as etapa,
                    COUNT(*) as quantidade,
                    1 as ordem
                FROM orcamentos
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'

                UNION ALL

                SELECT
                    'Orçamentos Aprovados',
                    COUNT(*),
                    2
                FROM orcamentos
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                    AND status = 'APROVADO'

                UNION ALL

                SELECT
                    'Vendas Finalizadas',
                    COUNT(*),
                    3
                FROM vendas
                WHERE data_venda >= CURRENT_DATE - INTERVAL '30 days'
                    AND status IN ('FINALIZADA', 'PAGA')

                ORDER BY ordem
            """,
            "visualization": "funnel",
            "description": "Conversão de orçamentos em vendas"
        },
        {
            "name": "Taxa de Retenção de Clientes",
            "query": """
                WITH clientes_mes AS (
                    SELECT
                        DATE_TRUNC('month', v.data_venda) as mes,
                        v.cliente_id
                    FROM vendas v
                    WHERE v.data_venda >= CURRENT_DATE - INTERVAL '12 months'
                        AND v.status != 'CANCELADA'
                    GROUP BY mes, v.cliente_id
                ),
                retencao AS (
                    SELECT
                        c1.mes,
                        COUNT(DISTINCT c1.cliente_id) as clientes_mes,
                        COUNT(DISTINCT c2.cliente_id) as clientes_retidos
                    FROM clientes_mes c1
                    LEFT JOIN clientes_mes c2
                        ON c1.cliente_id = c2.cliente_id
                        AND c2.mes = c1.mes + INTERVAL '1 month'
                    GROUP BY c1.mes
                )
                SELECT
                    mes,
                    clientes_mes,
                    clientes_retidos,
                    ROUND((clientes_retidos::numeric / NULLIF(clientes_mes, 0) * 100), 2) as taxa_retencao
                FROM retencao
                ORDER BY mes DESC
            """,
            "visualization": "line",
            "description": "Percentual de clientes que retornaram no mês seguinte"
        }
    ]
}

# ============================================================================
# DASHBOARD 5: COMPRAS E FORNECEDORES
# ============================================================================

DASHBOARD_COMPRAS = {
    "name": "🚚 Compras e Fornecedores",
    "description": "Análise de compras, fornecedores e custos",
    "cards": [
        {
            "name": "Compras por Mês",
            "query": """
                SELECT
                    DATE_TRUNC('month', data_pedido) as mes,
                    COUNT(*) as total_pedidos,
                    SUM(valor_total) as valor_total
                FROM pedidos_compra
                WHERE data_pedido >= CURRENT_DATE - INTERVAL '12 months'
                    AND status != 'CANCELADO'
                GROUP BY mes
                ORDER BY mes DESC
            """,
            "visualization": "line",
            "description": "Evolução de compras nos últimos 12 meses"
        },
        {
            "name": "Top Fornecedores por Volume",
            "query": """
                SELECT
                    f.razao_social,
                    COUNT(DISTINCT pc.id) as total_pedidos,
                    SUM(pc.valor_total) as valor_total,
                    AVG(pc.valor_total) as ticket_medio
                FROM fornecedores f
                JOIN pedidos_compra pc ON f.id = pc.fornecedor_id
                WHERE pc.data_pedido >= CURRENT_DATE - INTERVAL '12 months'
                    AND pc.status != 'CANCELADO'
                GROUP BY f.id, f.razao_social
                ORDER BY valor_total DESC
                LIMIT 10
            """,
            "visualization": "table",
            "description": "Principais fornecedores do último ano"
        },
        {
            "name": "Produtos com Maior Prazo de Entrega",
            "query": """
                SELECT
                    p.descricao as produto,
                    f.razao_social as fornecedor,
                    AVG(EXTRACT(EPOCH FROM (pc.data_entrega - pc.data_pedido)) / 86400)::int as prazo_medio_dias
                FROM pedidos_compra pc
                JOIN pedidos_compra_itens pci ON pc.id = pci.pedido_id
                JOIN produtos p ON pci.produto_id = p.id
                JOIN fornecedores f ON pc.fornecedor_id = f.id
                WHERE pc.data_entrega IS NOT NULL
                    AND pc.data_pedido >= CURRENT_DATE - INTERVAL '6 months'
                GROUP BY p.id, p.descricao, f.razao_social
                HAVING COUNT(*) >= 3
                ORDER BY prazo_medio_dias DESC
                LIMIT 20
            """,
            "visualization": "table",
            "description": "Produtos com maiores prazos de entrega"
        }
    ]
}

# ============================================================================
# TODAS AS DASHBOARDS
# ============================================================================

ALL_DASHBOARDS = [
    DASHBOARD_OVERVIEW,
    DASHBOARD_FINANCEIRO,
    DASHBOARD_ESTOQUE,
    DASHBOARD_VENDAS,
    DASHBOARD_COMPRAS
]
