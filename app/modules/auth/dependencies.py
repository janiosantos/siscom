"""
Dependencies para Autenticação e Autorização
"""
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.core.logging import get_logger
from app.modules.auth.models import User, Permission
from app.modules.auth.security import decode_token, extract_permissions_from_token

logger = get_logger(__name__)

# Security scheme para Bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Dependency que retorna o usuário atual autenticado

    Args:
        credentials: Credenciais HTTP Bearer
        db: Sessão do banco de dados

    Returns:
        User autenticado

    Raises:
        HTTPException: Se token inválido ou usuário não encontrado
    """
    token = credentials.credentials

    # Decodifica o token
    payload = decode_token(token)
    if payload is None:
        logger.warning("Token inválido ou expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extrai user_id
    user_id: str = payload.get("sub")
    if user_id is None:
        logger.warning("Token sem subject (user_id)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Busca usuário no banco
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(f"Usuário não encontrado: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(f"Usuário inativo tentou acessar: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency que retorna usuário ativo

    Args:
        current_user: Usuário atual

    Returns:
        User ativo

    Raises:
        HTTPException: Se usuário inativo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency que retorna usuário superuser

    Args:
        current_user: Usuário atual

    Returns:
        User superuser

    Raises:
        HTTPException: Se não for superuser
    """
    if not current_user.is_superuser:
        logger.warning(f"Usuário não-superuser tentou acessar recurso restrito: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissões insuficientes"
        )
    return current_user


class PermissionChecker:
    """
    Dependency class para verificar permissões específicas

    Uso:
        @app.get("/vendas", dependencies=[Depends(PermissionChecker(["vendas:read"]))])
    """

    def __init__(self, required_permissions: List[str]):
        """
        Inicializa o verificador de permissões

        Args:
            required_permissions: Lista de permissões necessárias (ex: ["vendas:read", "vendas:create"])
        """
        self.required_permissions = required_permissions

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Verifica se o usuário tem as permissões necessárias

        Args:
            credentials: Credenciais HTTP Bearer
            current_user: Usuário atual

        Returns:
            User se tiver permissões

        Raises:
            HTTPException: Se não tiver permissões
        """
        # Superuser tem todas as permissões
        if current_user.is_superuser:
            return current_user

        # Extrai permissões do token
        token = credentials.credentials
        user_permissions = extract_permissions_from_token(token)

        # Verifica se tem todas as permissões necessárias
        missing_permissions = set(self.required_permissions) - set(user_permissions)

        if missing_permissions:
            logger.warning(
                f"Usuário {current_user.id} sem permissões necessárias. "
                f"Faltando: {missing_permissions}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissões insuficientes. Necessário: {', '.join(missing_permissions)}"
            )

        return current_user


def require_permission(permission: str):
    """
    Decorator factory para exigir permissão específica

    Args:
        permission: Permissão necessária (ex: "vendas:create")

    Returns:
        Dependency
    """
    return PermissionChecker([permission])


def require_permissions(*permissions: str):
    """
    Decorator factory para exigir múltiplas permissões

    Args:
        permissions: Permissões necessárias

    Returns:
        Dependency
    """
    return PermissionChecker(list(permissions))


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """
    Dependency que retorna o usuário atual se autenticado, ou None

    Útil para endpoints que podem ser acessados com ou sem autenticação

    Args:
        credentials: Credenciais HTTP Bearer (opcional)
        db: Sessão do banco de dados

    Returns:
        User autenticado ou None
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)
        if payload is None:
            return None

        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        result = await db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if user and user.is_active:
            return user

        return None

    except Exception as e:
        logger.error(f"Erro ao obter usuário opcional: {e}")
        return None
