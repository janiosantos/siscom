"""
Utilitários de Segurança e JWT
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Contexto de criptografia de senhas
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__default_rounds=12,
    bcrypt__min_rounds=4,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha corresponde ao hash

    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash da senha

    Returns:
        True se a senha corresponde, False caso contrário
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Erro ao verificar senha: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Gera hash de uma senha

    Args:
        password: Senha em texto plano

    Returns:
        Hash da senha
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    permissions: List[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Cria um Access Token JWT

    Args:
        subject: Subject do token (geralmente user_id)
        permissions: Lista de permissões do usuário
        expires_delta: Tempo até expiração

    Returns:
        Token JWT
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "sub": str(subject),
        "permissions": permissions or []
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def create_refresh_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um Refresh Token JWT

    Args:
        subject: Subject do token (geralmente user_id)
        expires_delta: Tempo até expiração (padrão: 7 dias)

    Returns:
        Refresh Token JWT
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # Refresh token válido por 7 dias

    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "sub": str(subject),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica e valida um token JWT

    Args:
        token: Token JWT

    Returns:
        Payload do token ou None se inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"Erro ao decodificar token: {e}")
        return None


def extract_user_id_from_token(token: str) -> Optional[int]:
    """
    Extrai o user_id de um token JWT

    Args:
        token: Token JWT

    Returns:
        User ID ou None se inválido
    """
    payload = decode_token(token)
    if payload is None:
        return None

    user_id: str = payload.get("sub")
    if user_id is None:
        return None

    try:
        return int(user_id)
    except (ValueError, TypeError):
        return None


def extract_permissions_from_token(token: str) -> List[str]:
    """
    Extrai as permissões de um token JWT

    Args:
        token: Token JWT

    Returns:
        Lista de permissões
    """
    payload = decode_token(token)
    if payload is None:
        return []

    permissions: List[str] = payload.get("permissions", [])
    return permissions


def validate_token_type(token: str, expected_type: str = "access") -> bool:
    """
    Valida o tipo de token (access ou refresh)

    Args:
        token: Token JWT
        expected_type: Tipo esperado ("access" ou "refresh")

    Returns:
        True se o tipo corresponde, False caso contrário
    """
    payload = decode_token(token)
    if payload is None:
        return False

    token_type = payload.get("type", "access")  # Access token não tem campo "type"
    return token_type == expected_type or (expected_type == "access" and "type" not in payload)
