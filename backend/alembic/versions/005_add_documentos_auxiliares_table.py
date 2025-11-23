"""add documentos auxiliares table

Revision ID: 005_documentos_auxiliares
Revises: 004_pedidos_venda
Create Date: 2025-11-23 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '005_documentos_auxiliares'
down_revision = '004_pedidos_venda'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create documentos_auxiliares table"""

    op.create_table(
        'documentos_auxiliares',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tipo_documento', sa.Enum('PEDIDO_VENDA', 'ORCAMENTO', 'NOTA_ENTREGA', 'ROMANEIO', 'COMPROVANTE_ENTREGA', 'RECIBO', 'PEDIDO_COMPRA', name='tipodocumento'), nullable=False),
        sa.Column('referencia_tipo', sa.String(50), nullable=False),
        sa.Column('referencia_id', sa.Integer(), nullable=False),
        sa.Column('numero_documento', sa.String(50), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=True),
        sa.Column('arquivo_pdf', sa.String(500), nullable=True),
        sa.Column('conteudo_html', sa.Text(), nullable=True),
        sa.Column('metadados', sa.Text(), nullable=True),
        sa.Column('gerado_por_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id']),
        sa.ForeignKeyConstraint(['gerado_por_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documentos_auxiliares_tipo', 'documentos_auxiliares', ['tipo_documento'])
    op.create_index('idx_documentos_auxiliares_numero', 'documentos_auxiliares', ['numero_documento'])
    op.create_index('idx_documentos_auxiliares_cliente_id', 'documentos_auxiliares', ['cliente_id'])
    op.create_index('idx_documentos_auxiliares_gerado_por', 'documentos_auxiliares', ['gerado_por_id'])
    op.create_index('idx_documentos_auxiliares_created_at', 'documentos_auxiliares', ['created_at'])
    op.create_index('idx_documentos_auxiliares_referencia', 'documentos_auxiliares', ['referencia_tipo', 'referencia_id'])


def downgrade() -> None:
    """Drop documentos_auxiliares table"""

    op.drop_index('idx_documentos_auxiliares_referencia', table_name='documentos_auxiliares')
    op.drop_index('idx_documentos_auxiliares_created_at', table_name='documentos_auxiliares')
    op.drop_index('idx_documentos_auxiliares_gerado_por', table_name='documentos_auxiliares')
    op.drop_index('idx_documentos_auxiliares_cliente_id', table_name='documentos_auxiliares')
    op.drop_index('idx_documentos_auxiliares_numero', table_name='documentos_auxiliares')
    op.drop_index('idx_documentos_auxiliares_tipo', table_name='documentos_auxiliares')
    op.drop_table('documentos_auxiliares')

    # Drop enum
    sa.Enum(name='tipodocumento').drop(op.get_bind())
