"""Rename metadata to extra_metadata in transacoes_pix

Revision ID: 003
Revises: 002
Create Date: 2025-11-20 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename metadata column to extra_metadata to avoid SQLAlchemy reserved word conflict"""

    # Rename column from 'metadata' to 'extra_metadata'
    # This is required because 'metadata' is a reserved attribute in SQLAlchemy 2.0 DeclarativeBase
    op.alter_column('transacoes_pix', 'metadata', new_column_name='extra_metadata')


def downgrade() -> None:
    """Revert column name from extra_metadata back to metadata"""

    # Rename column back to 'metadata'
    op.alter_column('transacoes_pix', 'extra_metadata', new_column_name='metadata')
