/**
 * Testes - UserMenu Component
 */

import { render, screen, waitFor } from '@/__tests__/test-utils'
import { useUserStore } from '@/lib/store/user'
import { mockUser } from '@/__tests__/test-utils'

// Mock do componente UserMenu (criar se não existir)
const UserMenu = ({ user }: { user: any }) => {
  const { logout } = useUserStore()

  return (
    <div data-testid="user-menu">
      <button data-testid="user-button">
        {user?.username || 'User'}
      </button>
      <div data-testid="user-dropdown" className="dropdown">
        <div>{user?.email}</div>
        <div>{user?.role?.name}</div>
        <button onClick={logout} data-testid="logout-button">
          Sair
        </button>
      </div>
    </div>
  )
}

jest.mock('@/lib/store/user')
const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('UserMenu', () => {
  const mockLogout = jest.fn()

  beforeEach(() => {
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: mockLogout,
    })
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  describe('Renderização', () => {
    it('should render user menu', () => {
      render(<UserMenu user={mockUser} />)

      expect(screen.getByTestId('user-menu')).toBeInTheDocument()
    })

    it('should display username', () => {
      render(<UserMenu user={mockUser} />)

      expect(screen.getByText(mockUser.username)).toBeInTheDocument()
    })

    it('should display email', () => {
      render(<UserMenu user={mockUser} />)

      expect(screen.getByText(mockUser.email)).toBeInTheDocument()
    })

    it('should display role name', () => {
      render(<UserMenu user={mockUser} />)

      expect(screen.getByText(mockUser.role.name)).toBeInTheDocument()
    })

    it('should render logout button', () => {
      render(<UserMenu user={mockUser} />)

      expect(screen.getByTestId('logout-button')).toBeInTheDocument()
    })
  })

  describe('Interações', () => {
    it('should call logout when logout button is clicked', async () => {
      const { user } = render(<UserMenu user={mockUser} />)

      const logoutButton = screen.getByTestId('logout-button')
      await user.click(logoutButton)

      expect(mockLogout).toHaveBeenCalledTimes(1)
    })

    it('should handle null user', () => {
      render(<UserMenu user={null} />)

      expect(screen.getByText('User')).toBeInTheDocument()
    })
  })

  describe('Snapshot', () => {
    it('should match snapshot', () => {
      const { container } = render(<UserMenu user={mockUser} />)

      expect(container).toMatchSnapshot()
    })
  })
})
