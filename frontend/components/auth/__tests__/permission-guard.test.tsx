import React from 'react'
import { render, screen } from '@/__tests__/test-utils'
import { PermissionGuard } from '../permission-guard'
import { useUserStore } from '@/lib/store/user'
import { mockUser, mockVendedor } from '@/__tests__/test-utils'

// Mock the user store
jest.mock('@/lib/store/user', () => ({
  useUserStore: jest.fn(),
}))

const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('PermissionGuard', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Single permission check', () => {
    it('should render children when user has the required permission', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard permission="produtos.view">
          <div>Protected Content</div>
        </PermissionGuard>
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    it('should not render children when user lacks the permission', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard permission="produtos.delete">
          <div>Protected Content</div>
        </PermissionGuard>
      )

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('should render fallback when provided and permission is denied', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard
          permission="produtos.delete"
          fallback={<div>Access Denied</div>}
        >
          <div>Protected Content</div>
        </PermissionGuard>
      )

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
      expect(screen.getByText('Access Denied')).toBeInTheDocument()
    })
  })

  describe('Multiple permissions check', () => {
    it('should render when user has any of the permissions (requireAll=false)', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard
          permissions={['produtos.view', 'produtos.delete']}
          requireAll={false}
        >
          <div>Protected Content</div>
        </PermissionGuard>
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    it('should not render when user has none of the permissions', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard
          permissions={['estoque.view', 'financeiro.view']}
          requireAll={false}
        >
          <div>Protected Content</div>
        </PermissionGuard>
      )

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('should render when user has all permissions (requireAll=true)', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard
          permissions={['produtos.view', 'vendas.view']}
          requireAll={true}
        >
          <div>Protected Content</div>
        </PermissionGuard>
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    it('should not render when user is missing one permission (requireAll=true)', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard
          permissions={['produtos.view', 'produtos.delete']}
          requireAll={true}
        >
          <div>Protected Content</div>
        </PermissionGuard>
      )

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })
  })

  describe('Role-based check', () => {
    it('should render when user has the required role', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard role="Admin">
          <div>Admin Content</div>
        </PermissionGuard>
      )

      expect(screen.getByText('Admin Content')).toBeInTheDocument()
    })

    it('should not render when user lacks the role', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard role="Admin">
          <div>Admin Content</div>
        </PermissionGuard>
      )

      expect(screen.queryByText('Admin Content')).not.toBeInTheDocument()
    })
  })

  describe('Edge cases', () => {
    it('should not render when user is null', () => {
      mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard permission="produtos.view">
          <div>Protected Content</div>
        </PermissionGuard>
      )

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('should handle empty permissions array', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(
        <PermissionGuard permissions={[]}>
          <div>Protected Content</div>
        </PermissionGuard>
      )

      // Empty permissions array should render (no restriction)
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })
  })
})
