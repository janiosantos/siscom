"""
Configuração do Alembic para migrações assíncronas
"""
from logging.config import fileConfig
import asyncio

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Importa configurações e modelos
from app.core.config import settings
from app.core.database import Base

# Importa todos os modelos para que o Alembic os reconheça
# Sprint 1
try:
    from app.modules.produtos import models as produtos_models
except ImportError:
    pass

try:
    from app.modules.categorias import models as categorias_models
except ImportError:
    pass

try:
    from app.modules.estoque import models as estoque_models
except ImportError:
    pass

try:
    from app.modules.vendas import models as vendas_models
except ImportError:
    pass

try:
    from app.modules.financeiro import models as financeiro_models
except ImportError:
    pass

# Sprint 2
try:
    from app.modules.orcamentos import models as orcamentos_models
except ImportError:
    pass

# Sprint 3
try:
    from app.modules.compras import models as compras_models
except ImportError:
    pass

try:
    from app.modules.fornecedores import models as fornecedores_models
except ImportError:
    pass

# Sprint 4
try:
    from app.modules.os import models as os_models
except ImportError:
    pass

# Sprint 7
try:
    from app.modules.crm import models as crm_models
except ImportError:
    pass

# this is the Alembic Config object
config = context.config

# Interpreta o arquivo de configuração para logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados do SQLAlchemy
target_metadata = Base.metadata

# Sobrescreve a URL do banco com a do .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace('+asyncpg', ''))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
