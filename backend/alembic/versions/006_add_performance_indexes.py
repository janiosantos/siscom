"""add_performance_indexes

Revision ID: 006
Revises: 005
Create Date: 2025-11-23

Adiciona índices compostos otimizados para melhorar performance de queries
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Criar índices de performance"""

    # Índices para Vendas (queries do dashboard)
    op.create_index(
        'idx_vendas_data_status',
        'vendas',
        ['data_venda', 'status'],
        unique=False
    )

    op.create_index(
        'idx_vendas_vendedor_data',
        'vendas',
        ['vendedor_id', 'data_venda'],
        unique=False
    )

    op.create_index(
        'idx_vendas_cliente_data',
        'vendas',
        ['cliente_id', 'data_venda'],
        unique=False
    )

    # Índices para Itens de Venda (produtos mais vendidos)
    op.create_index(
        'idx_item_venda_produto',
        'itens_venda',
        ['produto_id', 'quantidade'],
        unique=False
    )

    # Índices para Produtos (queries frequentes)
    op.create_index(
        'idx_produtos_categoria_ativo',
        'produtos',
        ['categoria_id', 'ativo'],
        unique=False
    )

    op.create_index(
        'idx_produtos_codigo_ativo',
        'produtos',
        ['codigo', 'ativo'],
        unique=False
    )

    # Índices para Orçamentos (filtros frequentes)
    op.create_index(
        'idx_orcamentos_data_status',
        'orcamentos',
        ['data_orcamento', 'status'],
        unique=False
    )

    op.create_index(
        'idx_orcamentos_cliente_status',
        'orcamentos',
        ['cliente_id', 'status'],
        unique=False
    )

    # Índices para Estoque (movimentações)
    op.create_index(
        'idx_estoque_movimentacao_produto_data',
        'estoque_movimentacoes',
        ['produto_id', 'data_movimentacao'],
        unique=False
    )

    op.create_index(
        'idx_estoque_movimentacao_tipo',
        'estoque_movimentacoes',
        ['tipo_movimentacao', 'data_movimentacao'],
        unique=False
    )

    # Índices para Clientes (busca frequente)
    op.create_index(
        'idx_clientes_cpf_cnpj',
        'clientes',
        ['cpf_cnpj'],
        unique=False
    )

    op.create_index(
        'idx_clientes_nome',
        'clientes',
        ['nome'],
        unique=False
    )

    # Índices para Contas a Receber (financeiro)
    op.create_index(
        'idx_contas_receber_vencimento_status',
        'contas_receber',
        ['data_vencimento', 'status'],
        unique=False
    )

    # Índices para Contas a Pagar (financeiro)
    op.create_index(
        'idx_contas_pagar_vencimento_status',
        'contas_pagar',
        ['data_vencimento', 'status'],
        unique=False
    )


def downgrade() -> None:
    """Remover índices de performance"""

    # Vendas
    op.drop_index('idx_vendas_data_status', table_name='vendas')
    op.drop_index('idx_vendas_vendedor_data', table_name='vendas')
    op.drop_index('idx_vendas_cliente_data', table_name='vendas')

    # Itens de Venda
    op.drop_index('idx_item_venda_produto', table_name='itens_venda')

    # Produtos
    op.drop_index('idx_produtos_categoria_ativo', table_name='produtos')
    op.drop_index('idx_produtos_codigo_ativo', table_name='produtos')

    # Orçamentos
    op.drop_index('idx_orcamentos_data_status', table_name='orcamentos')
    op.drop_index('idx_orcamentos_cliente_status', table_name='orcamentos')

    # Estoque
    op.drop_index('idx_estoque_movimentacao_produto_data', table_name='estoque_movimentacoes')
    op.drop_index('idx_estoque_movimentacao_tipo', table_name='estoque_movimentacoes')

    # Clientes
    op.drop_index('idx_clientes_cpf_cnpj', table_name='clientes')
    op.drop_index('idx_clientes_nome', table_name='clientes')

    # Contas a Receber
    op.drop_index('idx_contas_receber_vencimento_status', table_name='contas_receber')

    # Contas a Pagar
    op.drop_index('idx_contas_pagar_vencimento_status', table_name='contas_pagar')
