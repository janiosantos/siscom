# Sistema de Autenticação e Autorização (RBAC)

## Visão Geral

O sistema implementa autenticação baseada em JWT (JSON Web Tokens) e autorização baseada em RBAC (Role-Based Access Control) com permissões granulares.

## Arquitetura

### Componentes

1. **User**: Usuário do sistema
2. **Role**: Papel/função que agrupa permissões
3. **Permission**: Permissão específica (resource:action)
4. **AuditLog**: Log de auditoria de ações
5. **RefreshToken**: Tokens de renovação

### Relacionamentos

- User N:N Role (um usuário pode ter múltiplos roles)
- Role N:N Permission (um role pode ter múltiplas permissões)
- User 1:N AuditLog (histórico de ações do usuário)

## Fluxo de Autenticação

### 1. Registro de Usuário

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "joao.silva",
  "email": "joao.silva@example.com",
  "full_name": "João Silva",
  "password": "SenhaSegura123"
}
```

**Resposta:**
```json
{
  "id": 1,
  "username": "joao.silva",
  "email": "joao.silva@example.com",
  "full_name": "João Silva",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-11-19T12:34:56.789Z",
  "last_login": null,
  "roles": []
}
```

### 2. Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "joao.silva",  # ou email
  "password": "SenhaSegura123"
}
```

**Resposta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Uso do Token

```bash
GET /api/v1/vendas
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 4. Renovação de Token

```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

## Permissões

### Estrutura de Permissões

Permissões seguem o formato: `resource:action`

**Exemplos:**
- `vendas:create` - Criar vendas
- `vendas:read` - Ler vendas
- `vendas:update` - Atualizar vendas
- `vendas:delete` - Deletar vendas
- `vendas:cancel` - Cancelar vendas

### Recursos e Ações Padrão

| Recurso | Ações Disponíveis |
|---------|-------------------|
| vendas | create, read, update, delete, cancel |
| produtos | create, read, update, delete |
| estoque | create, read, update, delete |
| clientes | create, read, update, delete |
| financeiro | create, read, update, delete, pay |
| pdv | open, close, sale |
| nfe | create, read, cancel |
| relatorios | read, export |
| dashboard | read |
| crm | read, manage |

### Permissões Especiais

- **Superuser**: Tem acesso a TODAS as permissões automaticamente
- **is_active**: Usuários inativos não podem fazer login

## Roles Padrão

### 1. Administrador
- **Descrição**: Acesso total ao sistema
- **Permissões**: TODAS
- **Uso**: Administradores do sistema

### 2. Gerente
- **Descrição**: Gerente de loja
- **Permissões**:
  - Produtos: read, create, update
  - Estoque: read, create, update
  - Vendas: read, create, update, cancel
  - PDV: open, close, sale
  - Clientes: read, create, update
  - Relatórios: read, export
  - Dashboard: read

### 3. Vendedor
- **Descrição**: Operador de vendas
- **Permissões**:
  - Produtos: read
  - Vendas: read, create
  - PDV: sale
  - Clientes: read, create
  - Dashboard: read

### 4. Estoquista
- **Descrição**: Controle de estoque
- **Permissões**:
  - Produtos: read
  - Estoque: read, create, update
  - Compras: read

### 5. Financeiro
- **Descrição**: Setor financeiro
- **Permissões**:
  - Financeiro: read, create, update, pay
  - Relatórios: read, export
  - Dashboard: read

## Uso em Código

### Proteção de Endpoints

#### 1. Requer Autenticação

```python
from fastapi import Depends
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

@router.get("/vendas")
async def listar_vendas(
    current_user: User = Depends(get_current_user)
):
    """Endpoint protegido - requer autenticação"""
    # current_user contém o usuário autenticado
    return {"vendas": []}
```

#### 2. Requer Permissão Específica

```python
from app.modules.auth.dependencies import require_permission

@router.post("/vendas", dependencies=[Depends(require_permission("vendas:create"))])
async def criar_venda(venda_data: VendaCreate):
    """Endpoint protegido - requer permissão vendas:create"""
    return {"message": "Venda criada"}
```

#### 3. Requer Múltiplas Permissões

```python
from app.modules.auth.dependencies import require_permissions

@router.delete("/vendas/{venda_id}",
    dependencies=[Depends(require_permissions("vendas:delete", "vendas:cancel"))]
)
async def deletar_venda(venda_id: int):
    """Requer permissões vendas:delete E vendas:cancel"""
    return {"message": "Venda deletada"}
```

#### 4. Requer Superuser

```python
from app.modules.auth.dependencies import get_current_superuser

@router.get("/admin/users")
async def listar_usuarios(
    current_user: User = Depends(get_current_superuser)
):
    """Endpoint protegido - apenas superuser"""
    return {"users": []}
```

#### 5. Autenticação Opcional

```python
from app.modules.auth.dependencies import get_optional_current_user

@router.get("/produtos")
async def listar_produtos(
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Endpoint público, mas pode personalizar para usuário autenticado
    """
    if current_user:
        # Retorna produtos personalizados
        pass
    else:
        # Retorna produtos públicos
        pass
```

### Verificação Manual de Permissões

```python
from app.modules.auth.security import extract_permissions_from_token

def has_permission(user: User, permission: str) -> bool:
    """Verifica se usuário tem permissão específica"""
    # Superuser tem todas as permissões
    if user.is_superuser:
        return True

    # Extrai permissões dos roles do usuário
    user_permissions = []
    for role in user.roles:
        for perm in role.permissions:
            user_permissions.append(perm.name)

    return permission in user_permissions
```

## Auditoria

Todas as ações importantes são registradas automaticamente no AuditLog:

- Login/Logout
- Criação/Atualização/Deleção de usuários
- Atribuição de roles
- Mudança de senha

### Consultar Logs de Auditoria

```bash
GET /api/v1/auth/audit-logs?user_id=1&action=login&skip=0&limit=100
Authorization: Bearer {token_superuser}
```

### Criar Log de Auditoria Customizado

```python
from app.modules.auth.service import AuditService
from app.modules.auth.schemas import AuditLogCreate

audit_log = AuditLogCreate(
    user_id=current_user.id,
    action="venda_criada",
    resource="vendas",
    resource_id=venda.id,
    details=json.dumps({"valor": venda.valor_total}),
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    correlation_id=get_correlation_id()
)

await AuditService.create_audit_log(db, audit_log)
```

## Gerenciamento de Usuários (Admin)

### Criar Usuário

```bash
POST /api/v1/auth/register
```

### Listar Usuários

```bash
GET /api/v1/auth/users?skip=0&limit=100
Authorization: Bearer {token_superuser}
```

### Buscar Usuário

```bash
GET /api/v1/auth/users/{user_id}
Authorization: Bearer {token_superuser}
```

### Atualizar Usuário

```bash
PUT /api/v1/auth/users/{user_id}
Authorization: Bearer {token_superuser}
Content-Type: application/json

{
  "email": "novo.email@example.com",
  "full_name": "Novo Nome",
  "is_active": true
}
```

### Deletar Usuário

```bash
DELETE /api/v1/auth/users/{user_id}
Authorization: Bearer {token_superuser}
```

### Atribuir Roles a Usuário

```bash
POST /api/v1/auth/users/{user_id}/roles
Authorization: Bearer {token_superuser}
Content-Type: application/json

{
  "user_id": 1,
  "role_ids": [2, 3]
}
```

## Gerenciamento de Roles (Admin)

### Criar Role

```bash
POST /api/v1/auth/roles
Authorization: Bearer {token_superuser}
Content-Type: application/json

{
  "name": "Atendente",
  "description": "Atendimento ao cliente",
  "permission_ids": [1, 2, 5, 8]
}
```

### Listar Roles

```bash
GET /api/v1/auth/roles
Authorization: Bearer {token_superuser}
```

### Buscar Role

```bash
GET /api/v1/auth/roles/{role_id}
Authorization: Bearer {token_superuser}
```

## Gerenciamento de Permissões (Admin)

### Criar Permissão

```bash
POST /api/v1/auth/permissions
Authorization: Bearer {token_superuser}
Content-Type: application/json

{
  "name": "vendas:approve",
  "description": "Aprovar vendas",
  "resource": "vendas",
  "action": "approve"
}
```

### Listar Permissões

```bash
GET /api/v1/auth/permissions
Authorization: Bearer {token_superuser}
```

## Inicialização do Sistema

### 1. Executar Script de Inicialização

```bash
python scripts/init_auth.py
```

Este script:
- Cria todas as permissões padrão
- Cria os roles padrão
- Solicita dados para criar o primeiro superuser

### 2. Criar Superuser Manualmente

```python
from app.modules.auth.models import User, Role
from app.modules.auth.security import get_password_hash

# Criar superuser
superuser = User(
    username="admin",
    email="admin@example.com",
    full_name="Administrator",
    hashed_password=get_password_hash("admin123"),
    is_active=True,
    is_superuser=True
)

db.add(superuser)
await db.commit()
```

## Segurança

### Boas Práticas Implementadas

1. **Senhas**:
   - Hash bcrypt
   - Validação de força (mínimo 8 caracteres, maiúscula, minúscula, número)
   - Nunca armazenadas em texto plano

2. **Tokens JWT**:
   - Access token: 30 minutos de validade
   - Refresh token: 7 dias de validade
   - Assinados com SECRET_KEY

3. **Proteção contra**:
   - Brute force (rate limiting recomendado)
   - Token replay (validação de expiração)
   - SQL injection (SQLAlchemy com parameterização)

4. **Auditoria**:
   - Todas as ações registradas
   - Correlation IDs para rastreamento
   - IP e User-Agent capturados

### Configurações de Segurança

No `.env`:

```env
# SECRET_KEY - CRÍTICO! Mudar em produção
SECRET_KEY=seu-secret-key-super-seguro-aqui-256-bits

# Algoritmo JWT
ALGORITHM=HS256

# Tempo de expiração do access token (em minutos)
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**IMPORTANTE**: Gerar SECRET_KEY seguro:

```python
import secrets
print(secrets.token_urlsafe(32))
# Usar o resultado no .env
```

## Troubleshooting

### Token Inválido ou Expirado

**Erro**: `401 Unauthorized - Token inválido ou expirado`

**Solução**: Renovar token usando refresh token

```bash
POST /api/v1/auth/refresh
{
  "refresh_token": "..."
}
```

### Permissões Insuficientes

**Erro**: `403 Forbidden - Permissões insuficientes`

**Solução**:
1. Verificar se usuário tem o role necessário
2. Verificar se o role tem a permissão necessária
3. Atribuir role/permissão adequado

### Usuário Inativo

**Erro**: `403 Forbidden - Usuário inativo`

**Solução**: Reativar usuário (apenas superuser):

```bash
PUT /api/v1/auth/users/{user_id}
{
  "is_active": true
}
```

## Migrações

Após implementar autenticação, executar migrations:

```bash
# Criar migration
alembic revision --autogenerate -m "Add authentication tables"

# Aplicar migration
alembic upgrade head
```

## Testes

### Testar Autenticação

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "username": "test_user",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPass123"
    })
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    # Registra usuário
    await client.post("/api/v1/auth/register", json={
        "username": "test",
        "email": "test@example.com",
        "full_name": "Test",
        "password": "Test123"
    })

    # Faz login
    response = await client.post("/api/v1/auth/login", json={
        "username": "test",
        "password": "Test123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
```

## Próximos Passos

1. **Rate Limiting**: Implementar proteção contra brute force no login
2. **2FA**: Autenticação de dois fatores (opcional)
3. **OAuth2**: Integração com Google/Facebook (opcional)
4. **Session Management**: Revogar tokens ativos
5. **Password Reset**: Recuperação de senha por email
