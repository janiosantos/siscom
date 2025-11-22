"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { usePermission, useRole } from "@/hooks/usePermissions"
import { useUserStore } from "@/lib/store/user"
import { AlertTriangle } from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface ProtectedPageProps {
  children: React.ReactNode
  permission?: string
  role?: string
  requiredPermissions?: string[]
}

/**
 * Component to protect entire pages based on permissions or roles
 *
 * Usage in page component:
 * export default function ProdutosPage() {
 *   return (
 *     <ProtectedPage permission="produtos.view">
 *       <div>Content here</div>
 *     </ProtectedPage>
 *   )
 * }
 */
export function ProtectedPage({
  children,
  permission,
  role,
  requiredPermissions,
}: ProtectedPageProps) {
  const router = useRouter()
  const { user } = useUserStore()
  const hasPermission = usePermission(permission || "")
  const hasRole = useRole(role || "")

  const hasAllRequiredPermissions =
    !requiredPermissions ||
    requiredPermissions.every((perm) => {
      return (
        user?.role?.permissions?.some((p) => p.name === perm) ?? false
      )
    })

  const isAuthorized =
    !permission && !role && !requiredPermissions
      ? true
      : permission
      ? hasPermission
      : role
      ? hasRole
      : hasAllRequiredPermissions

  if (!user) {
    // Not logged in, redirect handled by layout
    return null
  }

  if (!isAuthorized) {
    return (
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
        <Card className="w-full max-w-md border-red-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="h-5 w-5" />
              Acesso Negado
            </CardTitle>
            <CardDescription>
              Você não tem permissão para acessar esta página
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              {permission && (
                <>
                  Permissão necessária: <code className="text-xs bg-muted px-1 py-0.5 rounded">{permission}</code>
                </>
              )}
              {role && (
                <>
                  Role necessária: <code className="text-xs bg-muted px-1 py-0.5 rounded">{role}</code>
                </>
              )}
              {requiredPermissions && requiredPermissions.length > 0 && (
                <>
                  Permissões necessárias:
                  <ul className="list-disc list-inside mt-2">
                    {requiredPermissions.map((perm) => (
                      <li key={perm}>
                        <code className="text-xs bg-muted px-1 py-0.5 rounded">
                          {perm}
                        </code>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </p>
            <div className="flex gap-2">
              <Button onClick={() => router.back()} variant="outline">
                Voltar
              </Button>
              <Button onClick={() => router.push("/dashboard")}>
                Ir para Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return <>{children}</>
}
