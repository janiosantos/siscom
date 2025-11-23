"""add pedidos venda tables

Revision ID: 004_pedidos_venda
Revises: 003
Create Date: 2025-11-23 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '004_pedidos_venda'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create pedidos_venda and itens_pedido_venda tables"""

    # Pedidos de Venda
    op.create_table(
        'pedidos_venda',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('numero_pedido', sa.String(20), nullable=False, unique=True),
        sa.Column('orcamento_id', sa.Integer(), nullable=True),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('vendedor_id', sa.Integer(), nullable=False),
        sa.Column('data_pedido', sa.Date(), nullable=False),
        sa.Column('data_entrega_prevista', sa.Date(), nullable=False),
        sa.Column('data_entrega_real', sa.Date(), nullable=True),
        sa.Column('tipo_entrega', sa.Enum('RETIRADA', 'ENTREGA', 'TRANSPORTADORA', name='tipoentrega'), nullable=False, server_default='RETIRADA'),
        sa.Column('endereco_entrega', sa.String(500), nullable=True),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('desconto', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('valor_frete', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('outras_despesas', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('valor_total', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('status', sa.Enum('RASCUNHO', 'CONFIRMADO', 'EM_SEPARACAO', 'SEPARADO', 'EM_ENTREGA', 'ENTREGUE', 'FATURADO', 'CANCELADO', name='statuspedidovenda'), nullable=False, server_default='RASCUNHO'),
        sa.Column('condicao_pagamento_id', sa.Integer(), nullable=True),
        sa.Column('forma_pagamento', sa.String(50), nullable=True),
        sa.Column('observacoes', sa.String(500), nullable=True),
        sa.Column('observacoes_internas', sa.Text(), nullable=True),
        sa.Column('venda_id', sa.Integer(), nullable=True),
        sa.Column('usuario_separacao_id', sa.Integer(), nullable=True),
        sa.Column('data_separacao', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['orcamento_id'], ['orcamentos.id']),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id']),
        sa.ForeignKeyConstraint(['vendedor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['condicao_pagamento_id'], ['condicoes_pagamento.id']),
        sa.ForeignKeyConstraint(['venda_id'], ['vendas.id']),
        sa.ForeignKeyConstraint(['usuario_separacao_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pedidos_venda_numero_pedido', 'pedidos_venda', ['numero_pedido'], unique=True)
    op.create_index('idx_pedidos_venda_orcamento_id', 'pedidos_venda', ['orcamento_id'])
    op.create_index('idx_pedidos_venda_cliente_id', 'pedidos_venda', ['cliente_id'])
    op.create_index('idx_pedidos_venda_vendedor_id', 'pedidos_venda', ['vendedor_id'])
    op.create_index('idx_pedidos_venda_data_pedido', 'pedidos_venda', ['data_pedido'])
    op.create_index('idx_pedidos_venda_status', 'pedidos_venda', ['status'])
    op.create_index('idx_pedidos_venda_data_entrega_prevista', 'pedidos_venda', ['data_entrega_prevista'])

    # Itens de Pedido de Venda
    op.create_table(
        'itens_pedido_venda',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('produto_id', sa.Integer(), nullable=False),
        sa.Column('quantidade', sa.Numeric(10, 2), nullable=False),
        sa.Column('quantidade_separada', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('preco_unitario', sa.Numeric(10, 2), nullable=False),
        sa.Column('desconto_item', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('total_item', sa.Numeric(10, 2), nullable=False, server_default='0.0'),
        sa.Column('observacao_item', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos_venda.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['produto_id'], ['produtos.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_itens_pedido_venda_pedido_id', 'itens_pedido_venda', ['pedido_id'])
    op.create_index('idx_itens_pedido_venda_produto_id', 'itens_pedido_venda', ['produto_id'])


def downgrade() -> None:
    """Drop pedidos_venda and itens_pedido_venda tables"""

    # Drop itens_pedido_venda
    op.drop_index('idx_itens_pedido_venda_produto_id', table_name='itens_pedido_venda')
    op.drop_index('idx_itens_pedido_venda_pedido_id', table_name='itens_pedido_venda')
    op.drop_table('itens_pedido_venda')

    # Drop pedidos_venda
    op.drop_index('idx_pedidos_venda_data_entrega_prevista', table_name='pedidos_venda')
    op.drop_index('idx_pedidos_venda_status', table_name='pedidos_venda')
    op.drop_index('idx_pedidos_venda_data_pedido', table_name='pedidos_venda')
    op.drop_index('idx_pedidos_venda_vendedor_id', table_name='pedidos_venda')
    op.drop_index('idx_pedidos_venda_cliente_id', table_name='pedidos_venda')
    op.drop_index('idx_pedidos_venda_orcamento_id', table_name='pedidos_venda')
    op.drop_index('idx_pedidos_venda_numero_pedido', table_name='pedidos_venda')
    op.drop_table('pedidos_venda')

    # Drop enums
    sa.Enum(name='tipoentrega').drop(op.get_bind())
    sa.Enum(name='statuspedidovenda').drop(op.get_bind())
