"""
Configuração global do Pytest
Fixtures compartilhadas entre todos os testes
"""
from __future__ import annotations

import pytest
import asyncio
from typing import AsyncGenerator, Generator, Optional
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.modules.auth.models import User, Role, Permission
from app.modules.auth.security import get_password_hash, create_access_token
from main import app

# Import all models to register them with Base.metadata
import app.models  # noqa: F401


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Cria event loop para toda a sessão de testes
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_db_engine():
    """
    Cria engine de banco de dados de teste (SQLite in-memory)
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False
    )

    # Cria todas as tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def async_db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Cria sessão de banco de dados de teste
    """
    async_session_maker = async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def db_session(async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Alias para async_db_session para compatibilidade com testes existentes
    """
    async_session_maker = async_sessionmaker(
        async_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def override_get_db(async_db_session: AsyncSession):
    """
    Override da dependency get_db para usar banco de teste
    """
    async def _get_test_db():
        yield async_db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture(scope="function")
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP assíncrono para testes de API
    Usa override_get_db para garantir que os testes usem o banco de teste
    """
    # override_get_db já configurou app.dependency_overrides
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Auth Fixtures
# ============================================================================

@pytest.fixture(scope="function")
async def test_user(async_db_session: AsyncSession) -> User:
    """
    Cria usuário de teste
    """
    user = User(
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("Test123!"),
        is_active=True,
        is_superuser=False
    )

    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)

    return user


@pytest.fixture(scope="function")
async def test_superuser(async_db_session: AsyncSession) -> User:
    """
    Cria superuser de teste
    """
    superuser = User(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("Admin123!"),
        is_active=True,
        is_superuser=True
    )

    async_db_session.add(superuser)
    await async_db_session.commit()
    await async_db_session.refresh(superuser)

    return superuser


@pytest.fixture(scope="function")
async def test_permission(async_db_session: AsyncSession) -> Permission:
    """
    Cria permissão de teste
    """
    permission = Permission(
        name="produtos:read",
        description="Ler produtos",
        resource="produtos",
        action="read"
    )

    async_db_session.add(permission)
    await async_db_session.commit()
    await async_db_session.refresh(permission)

    return permission


@pytest.fixture(scope="function")
async def test_role(async_db_session: AsyncSession, test_permission: Permission) -> Role:
    """
    Cria role de teste com permissão
    """
    role = Role(
        name="Vendedor",
        description="Vendedor de loja"
    )
    role.permissions = [test_permission]

    async_db_session.add(role)
    await async_db_session.commit()
    await async_db_session.refresh(role)

    return role


@pytest.fixture(scope="function")
async def user_token(test_user: User) -> str:
    """
    Gera token JWT para usuário de teste
    """
    return create_access_token(
        subject=str(test_user.id),
        permissions=[]
    )


@pytest.fixture(scope="function")
async def superuser_token(test_superuser: User) -> str:
    """
    Gera token JWT para superuser de teste
    """
    return create_access_token(
        subject=str(test_superuser.id),
        permissions=[]
    )


@pytest.fixture(scope="function")
async def auth_headers(user_token: str) -> dict:
    """
    Headers de autenticação para requisições
    """
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture(scope="function")
async def admin_headers(superuser_token: str) -> dict:
    """
    Headers de autenticação para superuser
    """
    return {"Authorization": f"Bearer {superuser_token}"}
