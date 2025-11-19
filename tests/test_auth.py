"""
Testes para Autenticação e Autorização
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.auth.security import verify_password


@pytest.mark.auth
@pytest.mark.asyncio
class TestAuth Endpoints:
    """Testes dos endpoints de autenticação"""

    async def test_register_user(self, client: AsyncClient):
        """Teste de registro de usuário"""
        response = await client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "NewPass123!"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "hashed_password" not in data  # Senha não deve ser retornada

    async def test_register_duplicate_username(self, client: AsyncClient, test_user: User):
        """Teste de registro com username duplicado"""
        response = await client.post("/api/v1/auth/register", json={
            "username": test_user.username,
            "email": "different@example.com",
            "full_name": "Different User",
            "password": "Pass123!"
        })

        assert response.status_code == 400
        assert "já está em uso" in response.json()["detail"]

    async def test_register_weak_password(self, client: AsyncClient):
        """Teste de registro com senha fraca"""
        response = await client.post("/api/v1/auth/register", json={
            "username": "weakpass",
            "email": "weak@example.com",
            "full_name": "Weak User",
            "password": "123"  # Senha muito fraca
        })

        assert response.status_code == 422  # Validation error

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Teste de login com sucesso"""
        response = await client.post("/api/v1/auth/login", json={
            "username": test_user.username,
            "password": "Test123!"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Teste de login com senha incorreta"""
        response = await client.post("/api/v1/auth/login", json={
            "username": test_user.username,
            "password": "WrongPassword123!"
        })

        assert response.status_code == 401
        assert "incorretos" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Teste de login com usuário inexistente"""
        response = await client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "Pass123!"
        })

        assert response.status_code == 401

    async def test_get_current_user(self, client: AsyncClient, test_user: User, auth_headers: dict):
        """Teste de obtenção de usuário atual"""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Teste de acesso sem autenticação"""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 403  # Forbidden (sem token)


@pytest.mark.unit
@pytest.mark.asyncio
class TestPasswordSecurity:
    """Testes de segurança de senhas"""

    def test_password_hashing(self):
        """Teste de hash de senha"""
        from app.modules.auth.security import get_password_hash

        password = "MyPassword123!"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hash é longo

    def test_password_verification(self):
        """Teste de verificação de senha"""
        from app.modules.auth.security import get_password_hash, verify_password

        password = "MyPassword123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestJWT:
    """Testes de JWT"""

    def test_create_access_token(self):
        """Teste de criação de access token"""
        from app.modules.auth.security import create_access_token, decode_token

        user_id = "123"
        permissions = ["produtos:read", "vendas:create"]

        token = create_access_token(subject=user_id, permissions=permissions)

        assert isinstance(token, str)
        assert len(token) > 50

        # Decodifica e valida
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["permissions"] == permissions

    def test_decode_invalid_token(self):
        """Teste de decodificação de token inválido"""
        from app.modules.auth.security import decode_token

        invalid_token = "invalid.token.here"
        payload = decode_token(invalid_token)

        assert payload is None


@pytest.mark.integration
@pytest.mark.asyncio
class TestUserManagement:
    """Testes de gerenciamento de usuários"""

    async def test_list_users_as_superuser(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User
    ):
        """Teste de listagem de usuários (apenas superuser)"""
        response = await client.get("/api/v1/auth/users", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # Pelo menos o test_user

    async def test_list_users_as_regular_user(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Teste de listagem de usuários como usuário regular (deve falhar)"""
        response = await client.get("/api/v1/auth/users", headers=auth_headers)

        assert response.status_code == 403  # Forbidden

    async def test_update_user(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User
    ):
        """Teste de atualização de usuário"""
        response = await client.put(
            f"/api/v1/auth/users/{test_user.id}",
            headers=admin_headers,
            json={
                "full_name": "Updated Name",
                "email": "updated@example.com"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"


@pytest.mark.integration
@pytest.mark.asyncio
class TestRBAC:
    """Testes de Role-Based Access Control"""

    async def test_create_permission(
        self,
        client: AsyncClient,
        admin_headers: dict
    ):
        """Teste de criação de permissão"""
        response = await client.post(
            "/api/v1/auth/permissions",
            headers=admin_headers,
            json={
                "name": "produtos:create",
                "description": "Criar produtos",
                "resource": "produtos",
                "action": "create"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "produtos:create"
        assert data["resource"] == "produtos"
        assert data["action"] == "create"

    async def test_create_role(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_permission
    ):
        """Teste de criação de role"""
        response = await client.post(
            "/api/v1/auth/roles",
            headers=admin_headers,
            json={
                "name": "Gerente",
                "description": "Gerente de loja",
                "permission_ids": [test_permission.id]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Gerente"
        assert len(data["permissions"]) == 1
        assert data["permissions"][0]["id"] == test_permission.id

    async def test_assign_role_to_user(
        self,
        client: AsyncClient,
        admin_headers: dict,
        test_user: User,
        test_role
    ):
        """Teste de atribuição de role a usuário"""
        response = await client.post(
            f"/api/v1/auth/users/{test_user.id}/roles",
            headers=admin_headers,
            json={
                "user_id": test_user.id,
                "role_ids": [test_role.id]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["roles"]) == 1
        assert data["roles"][0]["name"] == test_role.name
