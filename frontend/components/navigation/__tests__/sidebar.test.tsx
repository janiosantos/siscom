import React from 'react'
import { render, screen } from '@/__tests__/test-utils'
import { Sidebar } from '../sidebar'
import { useUserStore } from '@/lib/store/user'
import { mockUser, mockVendedor, mockEstoquista } from '@/__tests__/test-utils'

// Mock the user store
jest.mock('@/lib/store/user', () => ({
  useUserStore: jest.fn(),
}))

const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('Sidebar', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('should render the logo and app name', () => {
    mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

    render(<Sidebar />)

    expect(screen.getByText('ERP Siscom')).toBeInTheDocument()
  })

  it('should render copyright footer', () => {
    mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

    render(<Sidebar />)

    expect(screen.getByText(/© 2025 ERP Siscom/i)).toBeInTheDocument()
  })

  describe('Admin user', () => {
    it('should show all menu items for admin', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(<Sidebar />)

      // Admin should see all menu items
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Vendas')).toBeInTheDocument()
      expect(screen.getByText('Produtos')).toBeInTheDocument()
      expect(screen.getByText('Estoque')).toBeInTheDocument()
      expect(screen.getByText('Financeiro')).toBeInTheDocument()
      expect(screen.getByText('Clientes')).toBeInTheDocument()
      expect(screen.getByText('Relatórios')).toBeInTheDocument()
      expect(screen.getByText('Configurações')).toBeInTheDocument()
    })
  })

  describe('Vendedor user', () => {
    it('should show only permitted menu items for vendedor', () => {
      mockUseUserStore.mockReturnValue({ user: mockVendedor, setUser: jest.fn(), logout: jest.fn() })

      render(<Sidebar />)

      // Vendedor should see these
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Vendas')).toBeInTheDocument()
      expect(screen.getByText('Produtos')).toBeInTheDocument()

      // Vendedor should NOT see these (no permissions)
      expect(screen.queryByText('Estoque')).not.toBeInTheDocument()
      expect(screen.queryByText('Financeiro')).not.toBeInTheDocument()
      expect(screen.queryByText('Configurações')).not.toBeInTheDocument()
    })
  })

  describe('Estoquista user', () => {
    it('should show only permitted menu items for estoquista', () => {
      mockUseUserStore.mockReturnValue({ user: mockEstoquista, setUser: jest.fn(), logout: jest.fn() })

      render(<Sidebar />)

      // Estoquista should see these
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Produtos')).toBeInTheDocument()
      expect(screen.getByText('Estoque')).toBeInTheDocument()

      // Estoquista should NOT see these
      expect(screen.queryByText('Vendas')).not.toBeInTheDocument()
      expect(screen.queryByText('Financeiro')).not.toBeInTheDocument()
      expect(screen.queryByText('Configurações')).not.toBeInTheDocument()
    })
  })

  describe('Navigation links', () => {
    it('should have correct href attributes', () => {
      mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })

      render(<Sidebar />)

      const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
      expect(dashboardLink).toHaveAttribute('href', '/dashboard')

      const vendasLink = screen.getByRole('link', { name: /vendas/i })
      expect(vendasLink).toHaveAttribute('href', '/dashboard/vendas')

      const produtosLink = screen.getByRole('link', { name: /produtos/i })
      expect(produtosLink).toHaveAttribute('href', '/dashboard/produtos')
    })
  })

  describe('No user logged in', () => {
    it('should not show restricted items when user is null', () => {
      mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })

      render(<Sidebar />)

      // Dashboard should still be visible (no permission required)
      expect(screen.getByText('Dashboard')).toBeInTheDocument()

      // Other items should not be visible
      expect(screen.queryByText('Vendas')).not.toBeInTheDocument()
      expect(screen.queryByText('Produtos')).not.toBeInTheDocument()
      expect(screen.queryByText('Estoque')).not.toBeInTheDocument()
      expect(screen.queryByText('Financeiro')).not.toBeInTheDocument()
    })
  })
})
