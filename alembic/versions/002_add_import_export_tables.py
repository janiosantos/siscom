"""add import export tables

Revision ID: 002_import_export
Revises: 001_add_integration_fields_to_transacao_pix
Create Date: 2025-11-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_import_export'
down_revision = '001_add_integration_fields_to_transacao_pix'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create import/export tables"""

    # Import Logs
    op.create_table(
        'import_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('format', sa.Enum('csv', 'excel', 'json', name='importformat'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('status', sa.Enum('pending', 'validating', 'validated', 'importing', 'completed', 'failed', 'rolled_back', name='importstatus'), nullable=False),
        sa.Column('total_rows', sa.Integer(), default=0),
        sa.Column('processed_rows', sa.Integer(), default=0),
        sa.Column('success_rows', sa.Integer(), default=0),
        sa.Column('failed_rows', sa.Integer(), default=0),
        sa.Column('validation_errors', sa.Text(), nullable=True),
        sa.Column('import_errors', sa.Text(), nullable=True),
        sa.Column('preview_data', sa.Text(), nullable=True),
        sa.Column('mapping', sa.Text(), nullable=True),
        sa.Column('can_rollback', sa.Boolean(), default=True),
        sa.Column('rollback_data', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_import_logs_module', 'import_logs', ['module'])
    op.create_index('idx_import_logs_status', 'import_logs', ['status'])
    op.create_index('idx_import_logs_user_id', 'import_logs', ['user_id'])
    op.create_index('idx_import_logs_created_at', 'import_logs', ['created_at'])

    # Export Logs
    op.create_table(
        'export_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('format', sa.Enum('csv', 'excel', 'json', 'pdf', name='exportformat'), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='exportstatus'), nullable=False),
        sa.Column('total_records', sa.Integer(), default=0),
        sa.Column('filters', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_export_logs_module', 'export_logs', ['module'])
    op.create_index('idx_export_logs_status', 'export_logs', ['status'])
    op.create_index('idx_export_logs_user_id', 'export_logs', ['user_id'])

    # Import Templates
    op.create_table(
        'import_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('module', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('format', sa.Enum('csv', 'excel', 'json', name='importformat_template'), nullable=False),
        sa.Column('column_mapping', sa.Text(), nullable=False),
        sa.Column('required_columns', sa.Text(), nullable=False),
        sa.Column('validation_rules', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_import_templates_module', 'import_templates', ['module'])
    op.create_index('idx_import_templates_is_active', 'import_templates', ['is_active'])
    op.create_index('idx_import_templates_name_module', 'import_templates', ['name', 'module'], unique=True)


def downgrade() -> None:
    """Drop import/export tables"""

    op.drop_index('idx_import_templates_name_module', table_name='import_templates')
    op.drop_index('idx_import_templates_is_active', table_name='import_templates')
    op.drop_index('idx_import_templates_module', table_name='import_templates')
    op.drop_table('import_templates')

    op.drop_index('idx_export_logs_user_id', table_name='export_logs')
    op.drop_index('idx_export_logs_status', table_name='export_logs')
    op.drop_index('idx_export_logs_module', table_name='export_logs')
    op.drop_table('export_logs')

    op.drop_index('idx_import_logs_created_at', table_name='import_logs')
    op.drop_index('idx_import_logs_user_id', table_name='import_logs')
    op.drop_index('idx_import_logs_status', table_name='import_logs')
    op.drop_index('idx_import_logs_module', table_name='import_logs')
    op.drop_table('import_logs')

    # Drop enums
    sa.Enum(name='importformat').drop(op.get_bind())
    sa.Enum(name='exportformat').drop(op.get_bind())
    sa.Enum(name='importstatus').drop(op.get_bind())
    sa.Enum(name='exportstatus').drop(op.get_bind())
    sa.Enum(name='importformat_template').drop(op.get_bind())
