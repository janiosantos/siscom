import { renderHook } from '@testing-library/react'
import { useUserStore } from '@/lib/store/user'
import {
  usePermission,
  useAnyPermission,
  useAllPermissions,
  useRole,
  useIsAdmin,
  useUserPermissions,
  useUserRole,
} from '../usePermissions'
import { mockUser, mockVendedor, mockEstoquista } from '@/__tests__/test-utils'

// Mock the user store
jest.mock('@/lib/store/user', () => ({
  useUserStore: jest.fn(),
}))

const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('usePermissions hooks', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('usePermission', () => {
    it('should return true when user has the permission', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => usePermission('produtos.view'))

      expect(result.current).toBe(true)
    })

    it('should return false when user does not have the permission', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => usePermission('produtos.delete'))

      expect(result.current).toBe(false)
    })

    it('should return false when user is null', () => {
      mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => usePermission('produtos.view'))

      expect(result.current).toBe(false)
    })

    it('should return false when user has no role', () => {
      const userWithoutRole = { ...mockUser, role: null }
      mockUseUserStore.mockReturnValue({ user: userWithoutRole as any, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => usePermission('produtos.view'))

      expect(result.current).toBe(false)
    })
  })

  describe('useAnyPermission', () => {
    it('should return true when user has at least one of the permissions', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() =>
        useAnyPermission(['produtos.view', 'produtos.create', 'produtos.delete'])
      )

      expect(result.current).toBe(true)
    })

    it('should return false when user has none of the permissions', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() =>
        useAnyPermission(['produtos.delete', 'estoque.view'])
      )

      expect(result.current).toBe(false)
    })

    it('should return false when user is null', () => {
      mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useAnyPermission(['produtos.view']))

      expect(result.current).toBe(false)
    })
  })

  describe('useAllPermissions', () => {
    it('should return true when user has all permissions', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() =>
        useAllPermissions(['produtos.view', 'produtos.create', 'vendas.view'])
      )

      expect(result.current).toBe(true)
    })

    it('should return false when user is missing at least one permission', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() =>
        useAllPermissions(['produtos.view', 'produtos.delete'])
      )

      expect(result.current).toBe(false)
    })

    it('should return false when user is null', () => {
      mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useAllPermissions(['produtos.view']))

      expect(result.current).toBe(false)
    })
  })

  describe('useRole', () => {
    it('should return true when user has the specified role', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useRole('Admin'))

      expect(result.current).toBe(true)
    })

    it('should return false when user does not have the specified role', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useRole('Admin'))

      expect(result.current).toBe(false)
    })

    it('should return false when user is null', () => {
      mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useRole('Admin'))

      expect(result.current).toBe(false)
    })
  })

  describe('useIsAdmin', () => {
    it('should return true for admin users', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useIsAdmin())

      expect(result.current).toBe(true)
    })

    it('should return false for non-admin users', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useIsAdmin())

      expect(result.current).toBe(false)
    })
  })

  describe('useUserPermissions', () => {
    it('should return array of permission names', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useUserPermissions())

      expect(result.current).toEqual([
        'produtos.view',
        'vendas.view',
        'vendas.create',
      ])
    })

    it('should return empty array when user is null', () => {
      mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useUserPermissions())

      expect(result.current).toEqual([])
    })

    it('should return empty array when user has no permissions', () => {
      const userWithoutPermissions = {
        ...mockUser,
        role: { ...mockUser.role, permissions: [] },
      }
      mockUseUserStore.mockReturnValue({
        user: userWithoutPermissions,
        setUser: jest.fn(),
        logout: jest.fn(),
      })

      const { result } = renderHook(() => useUserPermissions())

      expect(result.current).toEqual([])
    })
  })

  describe('useUserRole', () => {
    it('should return user role name', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useUserRole())

      expect(result.current).toBe('Vendedor')
    })

    it('should return null when user is null', () => {
      mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })

      const { result } = renderHook(() => useUserRole())

      expect(result.current).toBeNull()
    })

    it('should return null when user has no role', () => {
      const userWithoutRole = { ...mockUser, role: null }
      mockUseUserStore.mockReturnValue({
        user: userWithoutRole as any,
        setUser: jest.fn(),
        logout: jest.fn(),
      })

      const { result } = renderHook(() => useUserRole())

      expect(result.current).toBeNull()
    })
  })
})
