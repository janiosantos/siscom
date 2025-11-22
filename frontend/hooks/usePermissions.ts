import { useUserStore } from "@/lib/store/user"

/**
 * Hook to check if current user has a specific permission
 */
export function usePermission(permissionName: string): boolean {
  const { user } = useUserStore()

  if (!user || !user.role) return false

  return user.role.permissions?.some((p) => p.name === permissionName) ?? false
}

/**
 * Hook to check if current user has any of the specified permissions
 */
export function useAnyPermission(permissionNames: string[]): boolean {
  const { user } = useUserStore()

  if (!user || !user.role) return false

  return permissionNames.some((permissionName) =>
    user.role.permissions?.some((p) => p.name === permissionName)
  )
}

/**
 * Hook to check if current user has all of the specified permissions
 */
export function useAllPermissions(permissionNames: string[]): boolean {
  const { user } = useUserStore()

  if (!user || !user.role) return false

  return permissionNames.every((permissionName) =>
    user.role.permissions?.some((p) => p.name === permissionName)
  )
}

/**
 * Hook to check if current user has a specific role
 */
export function useRole(roleName: string): boolean {
  const { user } = useUserStore()

  if (!user || !user.role) return false

  return user.role.name === roleName
}

/**
 * Hook to check if current user is admin
 */
export function useIsAdmin(): boolean {
  return useRole("Admin")
}

/**
 * Hook to get all user permissions
 */
export function useUserPermissions(): string[] {
  const { user } = useUserStore()

  if (!user || !user.role || !user.role.permissions) return []

  return user.role.permissions.map((p) => p.name)
}

/**
 * Hook to get user role name
 */
export function useUserRole(): string | null {
  const { user } = useUserStore()

  if (!user || !user.role) return null

  return user.role.name
}
