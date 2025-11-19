"""
Service Layer para Autenticação e Autorização
"""
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import HTTPException, status

from app.core.logging import get_logger, log_business_event
from app.modules.auth.models import User, Role, Permission, AuditLog, RefreshToken
from app.modules.auth.schemas import (
    UserCreate, UserUpdate, RoleCreate, RoleUpdate,
    PermissionCreate, Token, AuditLogCreate
)
from app.modules.auth.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    decode_token, validate_token_type
)

logger = get_logger(__name__)


class AuthService:
    """Service para operações de autenticação"""

    @staticmethod
    async def authenticate_user(
        db: AsyncSession,
        username: str,
        password: str
    ) -> Optional[User]:
        """
        Autentica um usuário

        Args:
            db: Sessão do banco de dados
            username: Username ou email
            password: Senha

        Returns:
            User se autenticado, None caso contrário
        """
        # Busca por username ou email
        result = await db.execute(
            select(User).where(
                or_(User.username == username, User.email == username)
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Tentativa de login com username inexistente: {username}")
            return None

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Tentativa de login com senha incorreta: {username}")
            return None

        if not user.is_active:
            logger.warning(f"Tentativa de login de usuário inativo: {username}")
            return None

        # Atualiza last_login
        user.last_login = datetime.utcnow()
        await db.commit()

        logger.info(f"Usuário autenticado com sucesso: {user.username}")
        return user

    @staticmethod
    async def create_tokens(user: User) -> Token:
        """
        Cria access token e refresh token para um usuário

        Args:
            user: Usuário

        Returns:
            Token com access_token e refresh_token
        """
        # Extrai permissões do usuário
        permissions = []
        for role in user.roles:
            for permission in role.permissions:
                permissions.append(permission.name)

        # Remove duplicatas
        permissions = list(set(permissions))

        # Cria access token
        access_token = create_access_token(
            subject=str(user.id),
            permissions=permissions
        )

        # Cria refresh token
        refresh_token = create_refresh_token(subject=str(user.id))

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutos em segundos
        )

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str
    ) -> Token:
        """
        Renova um access token usando refresh token

        Args:
            db: Sessão do banco de dados
            refresh_token: Refresh token

        Returns:
            Novo Token

        Raises:
            HTTPException: Se refresh token inválido
        """
        # Valida o refresh token
        if not validate_token_type(refresh_token, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )

        # Decodifica o token
        payload = decode_token(refresh_token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado"
            )

        # Extrai user_id
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )

        # Busca usuário
        result = await db.execute(
            select(User).where(User.id == int(user_id))
        )
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inválido ou inativo"
            )

        # Cria novos tokens
        return await AuthService.create_tokens(user)


class UserService:
    """Service para operações de usuários"""

    @staticmethod
    async def create_user(
        db: AsyncSession,
        user_data: UserCreate,
        created_by: Optional[int] = None
    ) -> User:
        """
        Cria um novo usuário

        Args:
            db: Sessão do banco de dados
            user_data: Dados do usuário
            created_by: ID do usuário que criou

        Returns:
            User criado

        Raises:
            HTTPException: Se username ou email já existe
        """
        # Verifica se username já existe
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username já está em uso"
            )

        # Verifica se email já existe
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já está em uso"
            )

        # Cria usuário
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=get_password_hash(user_data.password),
            is_active=True,
            is_superuser=False
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Usuário criado: {user.username} (ID: {user.id})")
        log_business_event(
            event_name="user_created",
            user_id=created_by,
            new_user_id=user.id,
            username=user.username
        )

        return user

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Busca usuário por ID

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário

        Returns:
            User ou None
        """
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_users(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Lista usuários com paginação

        Args:
            db: Sessão do banco de dados
            skip: Offset
            limit: Limite

        Returns:
            Lista de Users
        """
        result = await db.execute(
            select(User).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: int,
        user_data: UserUpdate,
        updated_by: Optional[int] = None
    ) -> User:
        """
        Atualiza um usuário

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            user_data: Dados para atualização
            updated_by: ID do usuário que atualizou

        Returns:
            User atualizado

        Raises:
            HTTPException: Se usuário não encontrado
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Atualiza campos
        if user_data.email is not None:
            # Verifica se email já está em uso
            result = await db.execute(
                select(User).where(User.email == user_data.email, User.id != user_id)
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email já está em uso"
                )
            user.email = user_data.email

        if user_data.full_name is not None:
            user.full_name = user_data.full_name

        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        await db.commit()
        await db.refresh(user)

        logger.info(f"Usuário atualizado: {user.username} (ID: {user.id})")
        log_business_event(
            event_name="user_updated",
            user_id=updated_by,
            target_user_id=user.id
        )

        return user

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user_id: int,
        deleted_by: Optional[int] = None
    ) -> None:
        """
        Deleta um usuário

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            deleted_by: ID do usuário que deletou

        Raises:
            HTTPException: Se usuário não encontrado
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        await db.delete(user)
        await db.commit()

        logger.info(f"Usuário deletado: {user.username} (ID: {user.id})")
        log_business_event(
            event_name="user_deleted",
            user_id=deleted_by,
            target_user_id=user.id,
            username=user.username
        )

    @staticmethod
    async def assign_roles_to_user(
        db: AsyncSession,
        user_id: int,
        role_ids: List[int],
        assigned_by: Optional[int] = None
    ) -> User:
        """
        Atribui roles a um usuário

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            role_ids: IDs dos roles
            assigned_by: ID do usuário que atribuiu

        Returns:
            User atualizado

        Raises:
            HTTPException: Se usuário ou roles não encontrados
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        # Busca roles
        result = await db.execute(
            select(Role).where(Role.id.in_(role_ids))
        )
        roles = list(result.scalars().all())

        if len(roles) != len(role_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Um ou mais roles não encontrados"
            )

        # Atribui roles
        user.roles = roles
        await db.commit()
        await db.refresh(user)

        logger.info(f"Roles atribuídos ao usuário {user.username}: {[r.name for r in roles]}")
        log_business_event(
            event_name="roles_assigned",
            user_id=assigned_by,
            target_user_id=user.id,
            role_ids=role_ids
        )

        return user


class RoleService:
    """Service para operações de roles"""

    @staticmethod
    async def create_role(
        db: AsyncSession,
        role_data: RoleCreate,
        created_by: Optional[int] = None
    ) -> Role:
        """
        Cria um novo role

        Args:
            db: Sessão do banco de dados
            role_data: Dados do role
            created_by: ID do usuário que criou

        Returns:
            Role criado

        Raises:
            HTTPException: Se nome já existe
        """
        # Verifica se nome já existe
        result = await db.execute(
            select(Role).where(Role.name == role_data.name)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role com este nome já existe"
            )

        # Cria role
        role = Role(
            name=role_data.name,
            description=role_data.description
        )

        # Atribui permissões se fornecidas
        if role_data.permission_ids:
            result = await db.execute(
                select(Permission).where(Permission.id.in_(role_data.permission_ids))
            )
            permissions = list(result.scalars().all())
            role.permissions = permissions

        db.add(role)
        await db.commit()
        await db.refresh(role)

        logger.info(f"Role criado: {role.name} (ID: {role.id})")
        log_business_event(
            event_name="role_created",
            user_id=created_by,
            role_id=role.id,
            role_name=role.name
        )

        return role

    @staticmethod
    async def get_roles(db: AsyncSession) -> List[Role]:
        """
        Lista todos os roles

        Args:
            db: Sessão do banco de dados

        Returns:
            Lista de Roles
        """
        result = await db.execute(select(Role))
        return list(result.scalars().all())

    @staticmethod
    async def get_role_by_id(db: AsyncSession, role_id: int) -> Optional[Role]:
        """
        Busca role por ID

        Args:
            db: Sessão do banco de dados
            role_id: ID do role

        Returns:
            Role ou None
        """
        result = await db.execute(
            select(Role).where(Role.id == role_id)
        )
        return result.scalar_one_or_none()


class PermissionService:
    """Service para operações de permissões"""

    @staticmethod
    async def create_permission(
        db: AsyncSession,
        permission_data: PermissionCreate,
        created_by: Optional[int] = None
    ) -> Permission:
        """
        Cria uma nova permissão

        Args:
            db: Sessão do banco de dados
            permission_data: Dados da permissão
            created_by: ID do usuário que criou

        Returns:
            Permission criada

        Raises:
            HTTPException: Se nome já existe
        """
        # Verifica se nome já existe
        result = await db.execute(
            select(Permission).where(Permission.name == permission_data.name)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permissão com este nome já existe"
            )

        # Cria permissão
        permission = Permission(
            name=permission_data.name,
            description=permission_data.description,
            resource=permission_data.resource,
            action=permission_data.action
        )

        db.add(permission)
        await db.commit()
        await db.refresh(permission)

        logger.info(f"Permissão criada: {permission.name} (ID: {permission.id})")

        return permission

    @staticmethod
    async def get_permissions(db: AsyncSession) -> List[Permission]:
        """
        Lista todas as permissões

        Args:
            db: Sessão do banco de dados

        Returns:
            Lista de Permissions
        """
        result = await db.execute(select(Permission))
        return list(result.scalars().all())


class AuditService:
    """Service para operações de auditoria"""

    @staticmethod
    async def create_audit_log(
        db: AsyncSession,
        audit_data: AuditLogCreate
    ) -> AuditLog:
        """
        Cria um registro de auditoria

        Args:
            db: Sessão do banco de dados
            audit_data: Dados do log

        Returns:
            AuditLog criado
        """
        audit_log = AuditLog(**audit_data.dict())
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        return audit_log

    @staticmethod
    async def get_audit_logs(
        db: AsyncSession,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Lista logs de auditoria com filtros

        Args:
            db: Sessão do banco de dados
            user_id: Filtrar por usuário
            action: Filtrar por ação
            resource: Filtrar por recurso
            skip: Offset
            limit: Limite

        Returns:
            Lista de AuditLogs
        """
        query = select(AuditLog)

        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if action:
            query = query.where(AuditLog.action == action)
        if resource:
            query = query.where(AuditLog.resource == resource)

        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())
