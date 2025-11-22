import React from 'react'
import { render, screen, fireEvent } from '@/__tests__/test-utils'
import { Header } from '../header'
import { useUserStore } from '@/lib/store/user'
import { mockUser } from '@/__tests__/test-utils'

// Mock the user store
jest.mock('@/lib/store/user', () => ({
  useUserStore: jest.fn(),
}))

// Mock ThemeToggle component
jest.mock('@/components/theme-toggle', () => ({
  ThemeToggle: () => <button>Theme Toggle</button>,
}))

const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('Header', () => {
  const mockLogout = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: mockLogout,
    })
  })

  it('should render correctly', () => {
    render(<Header />)

    expect(screen.getByText('Busca rápida')).toBeInTheDocument()
  })

  it('should display keyboard shortcut hint', () => {
    render(<Header />)

    expect(screen.getByText('K')).toBeInTheDocument()
    expect(screen.getByText('Busca rápida')).toBeInTheDocument()
  })

  it('should display notification bell with indicator', () => {
    render(<Header />)

    // Bell button should be present
    const bellButton = screen.getByRole('button', { name: '' })
    expect(bellButton).toBeInTheDocument()
  })

  it('should display theme toggle', () => {
    render(<Header />)

    expect(screen.getByText('Theme Toggle')).toBeInTheDocument()
  })

  describe('User dropdown', () => {
    it('should display user name and role', () => {
      render(<Header />)

      expect(screen.getByText('Test User')).toBeInTheDocument()
      expect(screen.getByText('Admin')).toBeInTheDocument()
    })

    it('should show dropdown menu when user button is clicked', () => {
      render(<Header />)

      const userButton = screen.getByRole('button', { name: /test user/i })
      fireEvent.click(userButton)

      expect(screen.getByText('Meu Perfil')).toBeInTheDocument()
      expect(screen.getByText('Configurações')).toBeInTheDocument()
      expect(screen.getByText('Sair')).toBeInTheDocument()
    })

    it('should display user email in dropdown', () => {
      render(<Header />)

      const userButton = screen.getByRole('button', { name: /test user/i })
      fireEvent.click(userButton)

      expect(screen.getByText('test@example.com')).toBeInTheDocument()
    })

    it('should call logout when Sair is clicked', () => {
      render(<Header />)

      const userButton = screen.getByRole('button', { name: /test user/i })
      fireEvent.click(userButton)

      const logoutItem = screen.getByText('Sair')
      fireEvent.click(logoutItem)

      expect(mockLogout).toHaveBeenCalledTimes(1)
    })
  })

  describe('Default values when user is null', () => {
    it('should show default values when user is not logged in', () => {
      mockUseUserStore.mockReturnValue({
        user: null,
        setUser: jest.fn(),
        logout: mockLogout,
      })

      render(<Header />)

      expect(screen.getByText('Usuário')).toBeInTheDocument()
      expect(screen.getByText('Admin')).toBeInTheDocument()
    })

    it('should show default email in dropdown when user is null', () => {
      mockUseUserStore.mockReturnValue({
        user: null,
        setUser: jest.fn(),
        logout: mockLogout,
      })

      render(<Header />)

      const userButton = screen.getByRole('button', { name: /usuário/i })
      fireEvent.click(userButton)

      expect(screen.getByText('email@exemplo.com')).toBeInTheDocument()
    })
  })

  describe('User without role', () => {
    it('should show default role when user has no role', () => {
      const userWithoutRole = { ...mockUser, role: null }
      mockUseUserStore.mockReturnValue({
        user: userWithoutRole as any,
        setUser: jest.fn(),
        logout: mockLogout,
      })

      render(<Header />)

      expect(screen.getByText('Admin')).toBeInTheDocument()
    })
  })
})
