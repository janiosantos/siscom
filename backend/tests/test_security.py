"""
Testes do módulo core/security.py

Testa funções de:
- Hashing de senhas (bcrypt)
- Verificação de senhas
- Criação de tokens JWT
- Decodificação de tokens JWT
"""
import pytest
from datetime import timedelta, datetime
from unittest.mock import patch
from jose import jwt

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    pwd_context
)
from app.core.config import settings


class TestPasswordHashing:
    """Testes de hashing e verificação de senhas"""

    def test_get_password_hash_creates_hash(self):
        """Deve criar hash de senha"""
        password = "minha_senha_secreta_123"
        hashed = get_password_hash(password)

        # Hash deve ser diferente da senha original
        assert hashed != password

        # Hash deve começar com $2b$ (bcrypt)
        assert hashed.startswith("$2b$")

        # Hash deve ter tamanho adequado (bcrypt ~60 chars)
        assert len(hashed) > 50

    def test_get_password_hash_different_for_same_password(self):
        """Deve gerar hashes diferentes para a mesma senha (salt)"""
        password = "senha123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Mesmo com senha igual, hashes devem ser diferentes (bcrypt usa salt)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Deve verificar senha correta com sucesso"""
        password = "senha_correta_789"
        hashed = get_password_hash(password)

        # Verificação deve retornar True
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Deve rejeitar senha incorreta"""
        password = "senha_correta"
        wrong_password = "senha_errada"
        hashed = get_password_hash(password)

        # Verificação deve retornar False
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Deve lidar com senha vazia"""
        password = "senha123"
        hashed = get_password_hash(password)

        # Senha vazia não deve passar
        assert verify_password("", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Verificação deve ser case-sensitive"""
        password = "SenhaComMaiusculas"
        hashed = get_password_hash(password)

        # Case diferente deve falhar
        assert verify_password("senhacommaiusculas", hashed) is False
        assert verify_password("SENHACOMMAIUSCULAS", hashed) is False

    def test_verify_password_with_special_chars(self):
        """Deve funcionar com caracteres especiais"""
        password = "S3nh@!#$%^&*()_+-=[]{}|;:',.<>?/`~"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_unicode(self):
        """Deve funcionar com caracteres unicode"""
        password = "SenhaComÇedilhaEAcentuação123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_pwd_context_uses_bcrypt(self):
        """Deve usar bcrypt como algoritmo"""
        assert "bcrypt" in pwd_context.schemes()


class TestJWTTokenCreation:
    """Testes de criação de tokens JWT"""

    def test_create_access_token_basic(self):
        """Deve criar token JWT básico"""
        data = {"sub": "user@email.com", "user_id": 123}
        token = create_access_token(data)

        # Token deve ser string não vazia
        assert isinstance(token, str)
        assert len(token) > 0

        # Token JWT tem 3 partes separadas por ponto
        parts = token.split(".")
        assert len(parts) == 3

    def test_create_access_token_includes_data(self):
        """Token deve conter os dados fornecidos"""
        data = {
            "sub": "joao@email.com",
            "user_id": 456,
            "role": "admin"
        }
        token = create_access_token(data)

        # Decodificar token para verificar dados
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        assert payload["sub"] == "joao@email.com"
        assert payload["user_id"] == 456
        assert payload["role"] == "admin"

    def test_create_access_token_includes_expiration(self):
        """Token deve incluir tempo de expiração"""
        data = {"sub": "user@test.com"}
        token = create_access_token(data)

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Deve ter campo 'exp' (expiration)
        assert "exp" in payload

        # Expiration deve ser timestamp futuro
        assert payload["exp"] > datetime.utcnow().timestamp()

    def test_create_access_token_default_expiration(self):
        """Token deve usar expiração padrão do settings"""
        data = {"sub": "user@test.com"}

        before_creation = datetime.utcnow()
        token = create_access_token(data)
        after_creation = datetime.utcnow()

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Calcular expiração esperada (remover microsegundos para comparação)
        expected_exp_min = (before_creation + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )).replace(microsecond=0)
        expected_exp_max = (after_creation + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )).replace(microsecond=0) + timedelta(seconds=1)

        token_exp = datetime.fromtimestamp(payload["exp"]).replace(microsecond=0)

        # Verificar que está dentro do range esperado
        assert expected_exp_min <= token_exp <= expected_exp_max

    def test_create_access_token_custom_expiration(self):
        """Deve aceitar expiração customizada"""
        data = {"sub": "user@test.com"}
        custom_delta = timedelta(hours=2)

        before_creation = datetime.utcnow()
        token = create_access_token(data, expires_delta=custom_delta)
        after_creation = datetime.utcnow()

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Verificar expiração customizada (remover microsegundos para comparação)
        expected_exp_min = (before_creation + custom_delta).replace(microsecond=0)
        expected_exp_max = (after_creation + custom_delta).replace(microsecond=0) + timedelta(seconds=1)

        token_exp = datetime.fromtimestamp(payload["exp"]).replace(microsecond=0)

        assert expected_exp_min <= token_exp <= expected_exp_max

    def test_create_access_token_short_expiration(self):
        """Deve aceitar expiração muito curta"""
        data = {"sub": "user@test.com"}
        short_delta = timedelta(seconds=30)

        token = create_access_token(data, expires_delta=short_delta)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Verificar que expira em ~30 segundos
        token_exp = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        diff = (token_exp - now).total_seconds()

        assert 25 <= diff <= 35  # Margem de 5 segundos

    def test_create_access_token_does_not_modify_input(self):
        """Não deve modificar o dicionário de entrada"""
        data = {"sub": "user@test.com", "role": "user"}
        original_data = data.copy()

        create_access_token(data)

        # Data original não deve ter 'exp' adicionado
        assert data == original_data
        assert "exp" not in data


class TestJWTTokenDecoding:
    """Testes de decodificação de tokens JWT"""

    def test_decode_access_token_valid(self):
        """Deve decodificar token válido"""
        data = {
            "sub": "maria@email.com",
            "user_id": 789,
            "permissions": ["read", "write"]
        }
        token = create_access_token(data)

        # Decodificar
        decoded = decode_access_token(token)

        # Deve retornar payload com dados originais
        assert decoded is not None
        assert decoded["sub"] == "maria@email.com"
        assert decoded["user_id"] == 789
        assert decoded["permissions"] == ["read", "write"]
        assert "exp" in decoded

    def test_decode_access_token_invalid_signature(self):
        """Deve rejeitar token com assinatura inválida"""
        # Criar token com secret diferente
        data = {"sub": "user@test.com"}
        fake_token = jwt.encode(
            data,
            "wrong-secret-key",
            algorithm=settings.ALGORITHM
        )

        # Decodificar deve retornar None
        decoded = decode_access_token(fake_token)
        assert decoded is None

    def test_decode_access_token_expired(self):
        """Deve rejeitar token expirado"""
        data = {"sub": "user@test.com"}
        # Token que expira em 1 segundo
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        # Decodificar token expirado deve retornar None
        decoded = decode_access_token(token)
        assert decoded is None

    def test_decode_access_token_malformed(self):
        """Deve rejeitar token malformado"""
        malformed_tokens = [
            "not.a.jwt",
            "only-one-part",
            "two.parts",
            "invalid..format",
            "",
            "abc123",
            "Bearer token123"
        ]

        for bad_token in malformed_tokens:
            decoded = decode_access_token(bad_token)
            assert decoded is None, f"Token '{bad_token}' deveria ser rejeitado"

    def test_decode_access_token_wrong_algorithm(self):
        """Deve rejeitar token com algoritmo diferente"""
        data = {"sub": "user@test.com"}
        # Criar token com algoritmo diferente
        token = jwt.encode(data, settings.SECRET_KEY, algorithm="HS512")

        # Decodificar deve falhar
        decoded = decode_access_token(token)
        assert decoded is None

    def test_decode_access_token_missing_claims(self):
        """Deve decodificar mesmo com claims faltando"""
        # Token sem 'sub' mas com 'exp'
        data = {"user_id": 123}
        token = create_access_token(data)

        decoded = decode_access_token(token)

        # Deve decodificar normalmente
        assert decoded is not None
        assert decoded["user_id"] == 123


class TestSecurityIntegration:
    """Testes de integração entre funções"""

    def test_full_password_cycle(self):
        """Ciclo completo: hash -> verificar -> mudar senha"""
        # Senha original
        password1 = "senha_inicial_123"
        hash1 = get_password_hash(password1)

        # Verificar senha correta
        assert verify_password(password1, hash1) is True

        # Mudar senha
        password2 = "senha_nova_456"
        hash2 = get_password_hash(password2)

        # Nova senha não deve passar com hash antigo
        assert verify_password(password2, hash1) is False

        # Senha antiga não deve passar com novo hash
        assert verify_password(password1, hash2) is False

        # Nova senha deve passar com novo hash
        assert verify_password(password2, hash2) is True

    def test_full_jwt_cycle(self):
        """Ciclo completo: criar token -> decodificar -> validar"""
        # Dados do usuário
        user_data = {
            "sub": "pedro@email.com",
            "user_id": 999,
            "role": "manager",
            "permissions": ["create", "read", "update"]
        }

        # Criar token
        token = create_access_token(user_data, expires_delta=timedelta(hours=1))

        # Decodificar
        decoded = decode_access_token(token)

        # Validar todos os campos
        assert decoded is not None
        assert decoded["sub"] == user_data["sub"]
        assert decoded["user_id"] == user_data["user_id"]
        assert decoded["role"] == user_data["role"]
        assert decoded["permissions"] == user_data["permissions"]
        assert "exp" in decoded

    def test_multiple_users_tokens(self):
        """Deve criar tokens únicos para múltiplos usuários"""
        users = [
            {"sub": f"user{i}@test.com", "user_id": i}
            for i in range(5)
        ]

        tokens = []
        for user in users:
            token = create_access_token(user)
            tokens.append(token)

            # Cada token deve decodificar com dados corretos
            decoded = decode_access_token(token)
            assert decoded["sub"] == user["sub"]
            assert decoded["user_id"] == user["user_id"]

        # Todos os tokens devem ser diferentes
        assert len(set(tokens)) == 5


class TestEdgeCases:
    """Testes de edge cases e limites"""

    def test_password_very_long(self):
        """Deve lidar com senhas muito longas"""
        long_password = "a" * 1000
        hashed = get_password_hash(long_password)

        assert verify_password(long_password, hashed) is True

    def test_password_very_short(self):
        """Deve lidar com senhas muito curtas"""
        short_password = "a"
        hashed = get_password_hash(short_password)

        assert verify_password(short_password, hashed) is True

    def test_token_with_empty_data(self):
        """Deve criar token mesmo com dados vazios"""
        token = create_access_token({})
        decoded = decode_access_token(token)

        # Deve ter pelo menos 'exp'
        assert decoded is not None
        assert "exp" in decoded

    def test_token_with_large_payload(self):
        """Deve lidar com payload grande"""
        large_data = {
            "sub": "user@test.com",
            "permissions": [f"perm_{i}" for i in range(100)],
            "metadata": {"key_" + str(i): f"value_{i}" for i in range(50)}
        }

        token = create_access_token(large_data)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert len(decoded["permissions"]) == 100
        assert len(decoded["metadata"]) == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
