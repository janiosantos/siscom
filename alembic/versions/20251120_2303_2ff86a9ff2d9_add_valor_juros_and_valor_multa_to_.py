"""Add valor_juros and valor_multa to boleto table

Revision ID: 2ff86a9ff2d9
Revises: 003
Create Date: 2025-11-20 23:03:31.353306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ff86a9ff2d9'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add valor_juros and valor_multa columns to boletos table"""
    op.add_column('boletos', sa.Column('valor_juros', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'))
    op.add_column('boletos', sa.Column('valor_multa', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'))


def downgrade() -> None:
    """Remove valor_juros and valor_multa columns from boletos table"""
    op.drop_column('boletos', 'valor_multa')
    op.drop_column('boletos', 'valor_juros')
