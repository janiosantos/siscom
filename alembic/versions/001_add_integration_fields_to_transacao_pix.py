"""Add integration fields to transacoes_pix

Revision ID: 001
Revises:
Create Date: 2025-11-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add integration fields for external payment providers (Mercado Pago, PagSeguro, etc)"""

    # Add integration_id column
    op.add_column('transacoes_pix',
        sa.Column('integration_id', sa.String(length=100), nullable=True)
    )

    # Add integration_provider column
    op.add_column('transacoes_pix',
        sa.Column('integration_provider', sa.String(length=50), nullable=True)
    )

    # Add integration_data column (JSON with provider data)
    op.add_column('transacoes_pix',
        sa.Column('integration_data', sa.Text(), nullable=True)
    )

    # Create index on integration_id for faster lookups
    op.create_index(
        'ix_transacoes_pix_integration_id',
        'transacoes_pix',
        ['integration_id'],
        unique=False
    )


def downgrade() -> None:
    """Remove integration fields"""

    # Drop index
    op.drop_index('ix_transacoes_pix_integration_id', table_name='transacoes_pix')

    # Drop columns
    op.drop_column('transacoes_pix', 'integration_data')
    op.drop_column('transacoes_pix', 'integration_provider')
    op.drop_column('transacoes_pix', 'integration_id')
