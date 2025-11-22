# Sistema de Permissões e Roles - Frontend

## Visão Geral

O frontend implementa controle de acesso baseado em **roles** e **permissões** granulares, integrado com o backend FastAPI.

## Hooks Disponíveis

### `usePermission(permissionName: string): boolean`
Verifica se o usuário atual tem uma permissão específica.

```tsx
import { usePermission } from "@/hooks/usePermissions"

const canCreate = usePermission("produtos.create")
```

### `useAnyPermission(permissionNames: string[]): boolean`
Verifica se o usuário tem **pelo menos uma** das permissões especificadas.

```tsx
const canManageProdutos = useAnyPermission(["produtos.create", "produtos.update", "produtos.delete"])
```

### `useAllPermissions(permissionNames: string[]): boolean`
Verifica se o usuário tem **todas** as permissões especificadas.

```tsx
const hasFullAccess = useAllPermissions(["produtos.create", "produtos.update", "produtos.delete"])
```

### `useRole(roleName: string): boolean`
Verifica se o usuário tem uma role específica.

```tsx
const isAdmin = useRole("Admin")
const isGerente = useRole("Gerente")
```

### `useIsAdmin(): boolean`
Atalho para verificar se é Admin.

```tsx
const isAdmin = useIsAdmin()
```

### `useUserPermissions(): string[]`
Retorna array com todas as permissões do usuário.

```tsx
const permissions = useUserPermissions()
// ["produtos.view", "produtos.create", ...]
```

### `useUserRole(): string | null`
Retorna o nome da role do usuário.

```tsx
const role = useUserRole() // "Admin", "Gerente", etc.
```

## Componentes de Proteção

### `<PermissionGuard>`
Renderiza children apenas se o usuário tiver as permissões/role necessárias.

#### Uso Básico - Permissão Única
```tsx
import { PermissionGuard } from "@/components/auth/permission-guard"

<PermissionGuard permission="produtos.create">
  <Button>Criar Produto</Button>
</PermissionGuard>
```

#### Uso - Role Específica
```tsx
<PermissionGuard role="Admin">
  <Button>Admin Only</Button>
</PermissionGuard>
```

#### Uso - Múltiplas Permissões (qualquer uma)
```tsx
<PermissionGuard
  permissions={["produtos.view", "produtos.create"]}
  requireAll={false}
>
  <Button>Ver ou Criar Produtos</Button>
</PermissionGuard>
```

#### Uso - Múltiplas Permissões (todas necessárias)
```tsx
<PermissionGuard
  permissions={["produtos.create", "produtos.update"]}
  requireAll={true}
>
  <Button>Criar e Editar Produtos</Button>
</PermissionGuard>
```

#### Uso - Com Fallback
```tsx
<PermissionGuard
  permission="produtos.delete"
  fallback={<span className="text-muted-foreground">Sem permissão</span>}
>
  <Button variant="destructive">Deletar</Button>
</PermissionGuard>
```

### `<ProtectedPage>`
Protege páginas inteiras. Mostra tela de "Acesso Negado" se usuário não tiver permissão.

#### Uso em Páginas
```tsx
import { ProtectedPage } from "@/components/auth/protected-page"

export default function ProdutosPage() {
  return (
    <ProtectedPage permission="produtos.view">
      <div>
        {/* Conteúdo da página */}
      </div>
    </ProtectedPage>
  )
}
```

#### Com Role
```tsx
<ProtectedPage role="Admin">
  <div>Admin Only Page</div>
</ProtectedPage>
```

#### Com Múltiplas Permissões
```tsx
<ProtectedPage
  requiredPermissions={["vendas.view", "vendas.create"]}
>
  <div>Vendas Page</div>
</ProtectedPage>
```

## Permissões Disponíveis (Backend)

### Produtos
- `produtos.view` - Visualizar produtos
- `produtos.create` - Criar produtos
- `produtos.update` - Editar produtos
- `produtos.delete` - Deletar produtos

### Vendas
- `vendas.view` - Visualizar vendas
- `vendas.create` - Criar vendas
- `vendas.update` - Editar vendas
- `vendas.cancel` - Cancelar vendas
- `vendas.finalize` - Finalizar vendas

### Estoque
- `estoque.view` - Visualizar estoque
- `estoque.create` - Criar movimentações
- `estoque.update` - Editar movimentações
- `estoque.inventario` - Fazer inventário

### Financeiro
- `financeiro.view` - Visualizar contas
- `financeiro.create` - Criar contas
- `financeiro.update` - Editar contas
- `financeiro.approve` - Aprovar pagamentos
- `financeiro.pay` - Efetuar pagamentos

### Clientes
- `clientes.view` - Visualizar clientes
- `clientes.create` - Criar clientes
- `clientes.update` - Editar clientes
- `clientes.delete` - Deletar clientes

### Relatórios
- `relatorios.view` - Visualizar relatórios
- `relatorios.export` - Exportar relatórios

### Configurações
- `configuracoes.view` - Ver configurações
- `configuracoes.update` - Alterar configurações
- `users.manage` - Gerenciar usuários
- `roles.manage` - Gerenciar roles

## Roles Padrão (Backend)

### Admin
- **Todas as permissões**
- Acesso total ao sistema

### Gerente
- Todas as permissões exceto gerenciar usuários/roles
- Pode aprovar pagamentos
- Pode ver todos os relatórios

### Vendedor
- `produtos.view`
- `vendas.*` (todas de vendas)
- `clientes.*` (todas de clientes)
- `estoque.view`

### Estoquista
- `produtos.view`
- `estoque.*` (todas de estoque)
- `fornecedores.view`

### Financeiro
- `financeiro.*` (todas financeiras)
- `vendas.view`
- `clientes.view`
- `relatorios.view`, `relatorios.export`

## Exemplos Práticos

### Proteger Página Inteira
```tsx
// app/(dashboard)/produtos/page.tsx
import { ProtectedPage } from "@/components/auth/protected-page"

export default function ProdutosPage() {
  return (
    <ProtectedPage permission="produtos.view">
      {/* Se usuário não tiver permissão, verá tela de acesso negado */}
      <div className="space-y-6">
        {/* ... conteúdo ... */}
      </div>
    </ProtectedPage>
  )
}
```

### Proteger Botões de Ação
```tsx
import { PermissionGuard } from "@/components/auth/permission-guard"

// Botão de criar
<PermissionGuard permission="produtos.create">
  <Button onClick={handleCreate}>
    <Plus /> Novo Produto
  </Button>
</PermissionGuard>

// Botão de editar
<PermissionGuard permission="produtos.update">
  <Button onClick={handleEdit}>
    <Pencil /> Editar
  </Button>
</PermissionGuard>

// Botão de deletar
<PermissionGuard permission="produtos.delete">
  <Button onClick={handleDelete} variant="destructive">
    <Trash2 /> Deletar
  </Button>
</PermissionGuard>
```

### Proteger Rotas na Sidebar
```tsx
import { PermissionGuard } from "@/components/auth/permission-guard"

const menuItems = [
  { title: "Produtos", href: "/produtos", permission: "produtos.view" },
  { title: "Vendas", href: "/vendas", permission: "vendas.view" },
  { title: "Financeiro", href: "/financeiro", permission: "financeiro.view" },
]

{menuItems.map((item) => (
  <PermissionGuard key={item.href} permission={item.permission}>
    <Link href={item.href}>{item.title}</Link>
  </PermissionGuard>
))}
```

### Renderização Condicional com Hook
```tsx
import { usePermission } from "@/hooks/usePermissions"

function MyComponent() {
  const canDelete = usePermission("produtos.delete")

  return (
    <div>
      {canDelete && (
        <Button variant="destructive">Deletar</Button>
      )}
    </div>
  )
}
```

### Lógica Condicional
```tsx
import { useRole, usePermission } from "@/hooks/usePermissions"

function handleAction() {
  const isAdmin = useRole("Admin")
  const canApprove = usePermission("financeiro.approve")

  if (isAdmin || canApprove) {
    // Executar ação
  } else {
    toast.error("Sem permissão para esta ação")
  }
}
```

## Fluxo de Autenticação

1. **Login**: Usuário faz login em `/login`
2. **Token JWT**: Backend retorna `access_token` e `refresh_token`
3. **User Data**: Backend retorna objeto `User` com `role` e `permissions`
4. **Store**: Dados são salvos em Zustand + localStorage
5. **Proteção**: Hooks e componentes verificam permissões do `user.role.permissions`

## Estrutura de Dados

```typescript
interface User {
  id: number
  username: string
  email: string
  nome_completo: string
  role_id: number
  role: Role  // ← Contém as permissões
}

interface Role {
  id: number
  name: string  // "Admin", "Gerente", etc.
  description: string
  permissions: Permission[]  // ← Lista de permissões
}

interface Permission {
  id: number
  name: string  // "produtos.view", "vendas.create", etc.
  description: string
}
```

## Boas Práticas

1. **Sempre proteja páginas com `<ProtectedPage>`**
   - Evita usuários acessarem URLs diretamente

2. **Use `<PermissionGuard>` em botões de ação**
   - Esconde botões que o usuário não pode usar
   - Melhora UX

3. **Combine proteções**
   ```tsx
   <ProtectedPage permission="vendas.view">
     {/* Página protegida */}
     <PermissionGuard permission="vendas.create">
       <Button>Nova Venda</Button>
     </PermissionGuard>
   </ProtectedPage>
   ```

4. **Valide também no backend**
   - Frontend é para UX
   - Backend é segurança real
   - Sempre validar permissões na API

5. **Use hooks para lógica complexa**
   ```tsx
   const canManage = useAllPermissions([
     "produtos.create",
     "produtos.update",
     "produtos.delete"
   ])
   ```

## Troubleshooting

### Permissão não funciona
- Verificar se `user.role.permissions` está populado
- Conferir nome exato da permissão (case-sensitive)
- Verificar se backend está retornando permissões no login

### Página sempre mostra "Acesso Negado"
- Verificar se `permission` prop está correta
- Conferir se usuário está autenticado
- Ver console do browser para erros

### Botão não aparece mesmo com permissão
- Verificar se `<PermissionGuard>` está envolvendo corretamente
- Confirmar que não há CSS `display: none`
- Verificar se permissão está escrita corretamente

## Integração com Backend

O backend FastAPI usa os mesmos nomes de permissões:

```python
# Backend
@router.post("/", dependencies=[Depends(require_permission("produtos.create"))])
async def criar_produto(...):
    pass
```

```tsx
// Frontend
<PermissionGuard permission="produtos.create">
  <Button>Criar Produto</Button>
</PermissionGuard>
```

**As permissões devem ser idênticas** entre frontend e backend!
