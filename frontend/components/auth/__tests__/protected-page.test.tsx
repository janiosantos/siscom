import React from 'react'
import { render, screen, fireEvent } from '@/__tests__/test-utils'
import { ProtectedPage } from '../protected-page'
import { useUserStore } from '@/lib/store/user'
import { useRouter } from 'next/navigation'
import { mockUser, mockVendedor } from '@/__tests__/test-utils'

// Mock the user store
jest.mock('@/lib/store/user', () => ({
  useUserStore: jest.fn(),
}))

const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>
const mockRouter = {
  push: jest.fn(),
  replace: jest.fn(),
  back: jest.fn(),
}

// Mock useRouter is already done in jest.setup.js, but we need to access it
jest.mock('next/navigation', () => ({
  useRouter: () => mockRouter,
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

describe('ProtectedPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Permission-based protection', () => {
    it('should render children when user has the required permission', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage permission="produtos.view">
          <div>Page Content</div>
        </ProtectedPage>
      )

      expect(screen.getByText('Page Content')).toBeInTheDocument()
      expect(screen.queryByText('Acesso Negado')).not.toBeInTheDocument()
    })

    it('should show access denied when user lacks permission', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage permission="produtos.delete">
          <div>Page Content</div>
        </ProtectedPage>
      )

      expect(screen.queryByText('Page Content')).not.toBeInTheDocument()
      expect(screen.getByText('Acesso Negado')).toBeInTheDocument()
      expect(screen.getByText(/Você não tem permissão para acessar esta página/i)).toBeInTheDocument()
    })

    it('should display required permission in access denied message', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage permission="financeiro.view">
          <div>Page Content</div>
        </ProtectedPage>
      )

      expect(screen.getByText(/Permissão necessária: financeiro.view/i)).toBeInTheDocument()
    })

    it('should allow going back when clicking Voltar button', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage permission="financeiro.view">
          <div>Page Content</div>
        </ProtectedPage>
      )

      const backButton = screen.getByRole('button', { name: /voltar/i })
      fireEvent.click(backButton)

      expect(mockRouter.back).toHaveBeenCalledTimes(1)
    })
  })

  describe('Role-based protection', () => {
    it('should render children when user has the required role', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage role="Admin">
          <div>Admin Page</div>
        </ProtectedPage>
      )

      expect(screen.getByText('Admin Page')).toBeInTheDocument()
      expect(screen.queryByText('Acesso Negado')).not.toBeInTheDocument()
    })

    it('should show access denied when user lacks role', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage role="Admin">
          <div>Admin Page</div>
        </ProtectedPage>
      )

      expect(screen.queryByText('Admin Page')).not.toBeInTheDocument()
      expect(screen.getByText('Acesso Negado')).toBeInTheDocument()
      expect(screen.getByText(/Role necessária: Admin/i)).toBeInTheDocument()
    })
  })

  describe('Multiple permissions protection', () => {
    it('should render when user has all required permissions', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage requiredPermissions={['produtos.view', 'vendas.view']}>
          <div>Multi-Permission Page</div>
        </ProtectedPage>
      )

      expect(screen.getByText('Multi-Permission Page')).toBeInTheDocument()
    })

    it('should show access denied when user lacks one of the required permissions', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage requiredPermissions={['produtos.view', 'produtos.delete']}>
          <div>Multi-Permission Page</div>
        </ProtectedPage>
      )

      expect(screen.queryByText('Multi-Permission Page')).not.toBeInTheDocument()
      expect(screen.getByText('Acesso Negado')).toBeInTheDocument()
    })

    it('should display all required permissions in access denied message', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage requiredPermissions={['financeiro.view', 'financeiro.update']}>
          <div>Page Content</div>
        </ProtectedPage>
      )

      expect(screen.getByText(/Permissões necessárias:/i)).toBeInTheDocument()
      expect(screen.getByText(/financeiro.view/i)).toBeInTheDocument()
      expect(screen.getByText(/financeiro.update/i)).toBeInTheDocument()
    })
  })

  describe('Edge cases', () => {
    it('should show access denied when user is null', () => {
      mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage permission="produtos.view">
          <div>Page Content</div>
        </ProtectedPage>
      )

      expect(screen.queryByText('Page Content')).not.toBeInTheDocument()
      expect(screen.getByText('Acesso Negado')).toBeInTheDocument()
    })

    it('should render when no permission or role is specified', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(
        <ProtectedPage>
          <div>Public Page</div>
        </ProtectedPage>
      )

      // When no restriction is specified, should render
      expect(screen.getByText('Public Page')).toBeInTheDocument()
    })
  })
})
