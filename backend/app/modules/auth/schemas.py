"""
Schemas Pydantic para Autenticação e Autorização
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Schema base para User"""
    username: str = Field(..., min_length=3, max_length=50, description="Nome de usuário único")
    email: EmailStr = Field(..., description="Email do usuário")
    full_name: str = Field(..., min_length=3, max_length=255, description="Nome completo")


class UserCreate(UserBase):
    """Schema para criação de User"""
    password: str = Field(..., min_length=8, max_length=100, description="Senha do usuário")

    @validator('password')
    def validate_password_strength(cls, v):
        """Valida força da senha"""
        if len(v) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter pelo menos um número')
        return v


class UserUpdate(BaseModel):
    """Schema para atualização de User"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=3, max_length=255)
    is_active: Optional[bool] = None


class UserPasswordChange(BaseModel):
    """Schema para mudança de senha"""
    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(..., min_length=8, max_length=100, description="Nova senha")

    @validator('new_password')
    def validate_password_strength(cls, v):
        """Valida força da senha"""
        if len(v) < 8:
            raise ValueError('Senha deve ter no mínimo 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        if not any(c.islower() for c in v):
            raise ValueError('Senha deve conter pelo menos uma letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('Senha deve conter pelo menos um número')
        return v


class RoleInResponse(BaseModel):
    """Schema de Role em resposta"""
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class PermissionInResponse(BaseModel):
    """Schema de Permission em resposta"""
    id: int
    name: str
    description: Optional[str] = None
    resource: str
    action: str

    class Config:
        from_attributes = True


class UserInResponse(UserBase):
    """Schema de User em resposta"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    roles: List[RoleInResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# Role Schemas
# ============================================================================

class RoleBase(BaseModel):
    """Schema base para Role"""
    name: str = Field(..., min_length=3, max_length=50, description="Nome do papel")
    description: Optional[str] = Field(None, description="Descrição do papel")


class RoleCreate(RoleBase):
    """Schema para criação de Role"""
    permission_ids: List[int] = Field(default=[], description="IDs das permissões")


class RoleUpdate(BaseModel):
    """Schema para atualização de Role"""
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class RoleWithPermissions(RoleBase):
    """Schema de Role com permissões"""
    id: int
    created_at: datetime
    permissions: List[PermissionInResponse] = []

    class Config:
        from_attributes = True


# ============================================================================
# Permission Schemas
# ============================================================================

class PermissionBase(BaseModel):
    """Schema base para Permission"""
    name: str = Field(..., min_length=3, max_length=100, description="Nome da permissão (ex: vendas:create)")
    description: Optional[str] = Field(None, description="Descrição da permissão")
    resource: str = Field(..., min_length=2, max_length=50, description="Recurso (ex: vendas)")
    action: str = Field(..., min_length=2, max_length=20, description="Ação (ex: create, read, update, delete)")


class PermissionCreate(PermissionBase):
    """Schema para criação de Permission"""
    pass


class PermissionUpdate(BaseModel):
    """Schema para atualização de Permission"""
    description: Optional[str] = None


# ============================================================================
# Auth Schemas
# ============================================================================

class Token(BaseModel):
    """Schema de Token JWT"""
    access_token: str = Field(..., description="Access token JWT")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field(default="bearer", description="Tipo do token")
    expires_in: int = Field(..., description="Tempo de expiração em segundos")


class TokenPayload(BaseModel):
    """Schema do payload do token"""
    sub: str = Field(..., description="Subject (user_id)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at")
    permissions: List[str] = Field(default=[], description="Lista de permissões do usuário")


class LoginRequest(BaseModel):
    """Schema para requisição de login"""
    username: str = Field(..., description="Username ou email")
    password: str = Field(..., description="Senha")


class RefreshTokenRequest(BaseModel):
    """Schema para requisição de refresh token"""
    refresh_token: str = Field(..., description="Refresh token")


class UserRoleAssignment(BaseModel):
    """Schema para atribuição de roles a usuário"""
    user_id: int = Field(..., description="ID do usuário")
    role_ids: List[int] = Field(..., description="IDs dos roles a atribuir")


# ============================================================================
# Audit Log Schemas
# ============================================================================

class AuditLogCreate(BaseModel):
    """Schema para criação de Audit Log"""
    user_id: Optional[int] = None
    action: str = Field(..., description="Ação realizada")
    resource: Optional[str] = None
    resource_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None


class AuditLogInResponse(BaseModel):
    """Schema de Audit Log em resposta"""
    id: int
    user_id: Optional[int]
    action: str
    resource: Optional[str]
    resource_id: Optional[int]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
