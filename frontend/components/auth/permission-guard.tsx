"use client"

import { usePermission, useRole, useAnyPermission } from "@/hooks/usePermissions"
import { ReactNode } from "react"

interface PermissionGuardProps {
  children: ReactNode
  permission?: string
  permissions?: string[]
  role?: string
  requireAll?: boolean // if true, requires all permissions; if false, requires any
  fallback?: ReactNode
}

/**
 * Component to conditionally render children based on user permissions or role
 *
 * Usage:
 * <PermissionGuard permission="produtos.create">
 *   <Button>Criar Produto</Button>
 * </PermissionGuard>
 *
 * <PermissionGuard role="Admin">
 *   <Button>Admin Only</Button>
 * </PermissionGuard>
 *
 * <PermissionGuard permissions={["produtos.view", "produtos.create"]} requireAll={false}>
 *   <Button>Produtos</Button>
 * </PermissionGuard>
 */
export function PermissionGuard({
  children,
  permission,
  permissions,
  role,
  requireAll = true,
  fallback = null,
}: PermissionGuardProps) {
  const hasPermission = usePermission(permission || "")
  const hasRole = useRole(role || "")
  const hasAnyPermission = useAnyPermission(permissions || [])

  // Check role
  if (role) {
    return hasRole ? <>{children}</> : <>{fallback}</>
  }

  // Check single permission
  if (permission) {
    return hasPermission ? <>{children}</> : <>{fallback}</>
  }

  // Check multiple permissions
  if (permissions && permissions.length > 0) {
    if (requireAll) {
      // All permissions required
      const hasAllPermissions = permissions.every((perm) => {
        const has = usePermission(perm)
        return has
      })
      return hasAllPermissions ? <>{children}</> : <>{fallback}</>
    } else {
      // Any permission required
      return hasAnyPermission ? <>{children}</> : <>{fallback}</>
    }
  }

  // No restrictions, show content
  return <>{children}</>
}
