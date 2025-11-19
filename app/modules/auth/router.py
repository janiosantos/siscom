"""
Router para Autenticação e Autorização
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.logging import get_logger, log_business_event
from app.middleware.correlation import get_correlation_id
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    UserCreate, UserInResponse, UserUpdate, UserPasswordChange,
    Token, LoginRequest, RefreshTokenRequest, UserRoleAssignment,
    RoleCreate, RoleWithPermissions, RoleUpdate,
    PermissionCreate, PermissionInResponse,
    AuditLogInResponse
)
from app.modules.auth.service import (
    AuthService, UserService, RoleService,
    PermissionService, AuditService
)
from app.modules.auth.dependencies import (
    get_current_user, get_current_superuser,
    require_permission
)
from app.modules.auth.security import verify_password, get_password_hash

logger = get_logger(__name__)
router = APIRouter()


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/register", response_model=UserInResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Registra um novo usuário

    - **username**: Nome de usuário único (3-50 caracteres)
    - **email**: Email único
    - **full_name**: Nome completo
    - **password**: Senha (mínimo 8 caracteres, com maiúscula, minúscula e número)
    """
    correlation_id = get_correlation_id()

    user = await UserService.create_user(db, user_data)

    log_business_event(
        event_name="user_registered",
        correlation_id=correlation_id,
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host if request.client else None
    )

    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Autentica um usuário e retorna tokens

    - **username**: Username ou email
    - **password**: Senha

    Retorna:
    - **access_token**: Token JWT para acesso (válido por 30 minutos)
    - **refresh_token**: Token para renovação (válido por 7 dias)
    """
    correlation_id = get_correlation_id()

    user = await AuthService.authenticate_user(
        db,
        login_data.username,
        login_data.password
    )

    if not user:
        logger.warning(
            "Tentativa de login falhou",
            extra={
                "correlation_id": correlation_id,
                "username": login_data.username,
                "ip_address": request.client.host if request.client else None
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username ou senha incorretos"
        )

    tokens = await AuthService.create_tokens(user)

    log_business_event(
        event_name="user_login",
        correlation_id=correlation_id,
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host if request.client else None
    )

    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Renova o access token usando refresh token

    - **refresh_token**: Refresh token válido

    Retorna novos access_token e refresh_token
    """
    return await AuthService.refresh_access_token(db, refresh_data.refresh_token)


@router.get("/me", response_model=UserInResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Retorna informações do usuário autenticado atual
    """
    return current_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Altera a senha do usuário autenticado

    - **current_password**: Senha atual
    - **new_password**: Nova senha (mínimo 8 caracteres, com maiúscula, minúscula e número)
    """
    correlation_id = get_correlation_id()

    # Verifica senha atual
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )

    # Atualiza senha
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()

    logger.info(f"Senha alterada para usuário: {current_user.username}")
    log_business_event(
        event_name="password_changed",
        correlation_id=correlation_id,
        user_id=current_user.id
    )


# ============================================================================
# User Management Endpoints (Admin only)
# ============================================================================

@router.get("/users", response_model=List[UserInResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Lista todos os usuários (apenas superuser)

    - **skip**: Offset para paginação
    - **limit**: Limite de resultados (máx: 100)
    """
    return await UserService.get_users(db, skip, limit)


@router.get("/users/{user_id}", response_model=UserInResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Busca um usuário por ID (apenas superuser)
    """
    user = await UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    return user


@router.put("/users/{user_id}", response_model=UserInResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Atualiza um usuário (apenas superuser)
    """
    return await UserService.update_user(db, user_id, user_data, current_user.id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Deleta um usuário (apenas superuser)
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode deletar sua própria conta"
        )

    await UserService.delete_user(db, user_id, current_user.id)


@router.post("/users/{user_id}/roles", response_model=UserInResponse)
async def assign_roles_to_user(
    user_id: int,
    role_assignment: UserRoleAssignment,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Atribui roles a um usuário (apenas superuser)

    - **role_ids**: Lista de IDs dos roles a atribuir
    """
    return await UserService.assign_roles_to_user(
        db,
        user_id,
        role_assignment.role_ids,
        current_user.id
    )


# ============================================================================
# Role Management Endpoints (Admin only)
# ============================================================================

@router.post("/roles", response_model=RoleWithPermissions, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cria um novo role (apenas superuser)

    - **name**: Nome do role (único)
    - **description**: Descrição (opcional)
    - **permission_ids**: IDs das permissões a atribuir (opcional)
    """
    return await RoleService.create_role(db, role_data, current_user.id)


@router.get("/roles", response_model=List[RoleWithPermissions])
async def list_roles(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Lista todos os roles (apenas superuser)
    """
    return await RoleService.get_roles(db)


@router.get("/roles/{role_id}", response_model=RoleWithPermissions)
async def get_role(
    role_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Busca um role por ID (apenas superuser)
    """
    role = await RoleService.get_role_by_id(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role não encontrado"
        )
    return role


# ============================================================================
# Permission Management Endpoints (Admin only)
# ============================================================================

@router.post("/permissions", response_model=PermissionInResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cria uma nova permissão (apenas superuser)

    - **name**: Nome da permissão (ex: "vendas:create")
    - **description**: Descrição (opcional)
    - **resource**: Recurso (ex: "vendas")
    - **action**: Ação (ex: "create", "read", "update", "delete")
    """
    return await PermissionService.create_permission(db, permission_data, current_user.id)


@router.get("/permissions", response_model=List[PermissionInResponse])
async def list_permissions(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Lista todas as permissões (apenas superuser)
    """
    return await PermissionService.get_permissions(db)


# ============================================================================
# Audit Log Endpoints (Admin only)
# ============================================================================

@router.get("/audit-logs", response_model=List[AuditLogInResponse])
async def list_audit_logs(
    user_id: int = None,
    action: str = None,
    resource: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Lista logs de auditoria (apenas superuser)

    - **user_id**: Filtrar por usuário (opcional)
    - **action**: Filtrar por ação (opcional)
    - **resource**: Filtrar por recurso (opcional)
    - **skip**: Offset para paginação
    - **limit**: Limite de resultados (máx: 100)
    """
    return await AuditService.get_audit_logs(
        db,
        user_id=user_id,
        action=action,
        resource=resource,
        skip=skip,
        limit=limit
    )
