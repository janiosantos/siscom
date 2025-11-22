/**
 * Testes de Snapshot - Componentes de Autenticação
 */

import { render } from '@/__tests__/test-utils'
import { useUserStore } from '@/lib/store/user'
import { mockUser, mockVendedor } from '@/__tests__/test-utils'
import { PermissionGuard } from '../permission-guard'
import { ProtectedPage } from '../protected-page'

jest.mock('@/lib/store/user')
const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('PermissionGuard Snapshots', () => {
  beforeEach(() => {
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: jest.fn(),
    })
  })

  it('should match snapshot when user has permission', () => {
    const { container } = render(
      <PermissionGuard permission="produtos.view">
        <div>Protected Content</div>
      </PermissionGuard>
    )
    expect(container).toMatchSnapshot()
  })

  it('should match snapshot when user lacks permission', () => {
    mockUseUserStore.mockReturnValue({
      user: mockVendedor,
      setUser: jest.fn(),
      logout: jest.fn(),
    })

    const { container } = render(
      <PermissionGuard permission="produtos.delete">
        <div>Protected Content</div>
      </PermissionGuard>
    )
    expect(container).toMatchSnapshot()
  })

  it('should match snapshot with fallback', () => {
    mockUseUserStore.mockReturnValue({
      user: mockVendedor,
      setUser: jest.fn(),
      logout: jest.fn(),
    })

    const { container } = render(
      <PermissionGuard
        permission="produtos.delete"
        fallback={<div>No permission</div>}
      >
        <div>Protected Content</div>
      </PermissionGuard>
    )
    expect(container).toMatchSnapshot()
  })
})

describe('ProtectedPage Snapshots', () => {
  it('should match snapshot for authenticated user', () => {
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: jest.fn(),
    })

    const { container } = render(
      <ProtectedPage>
        <div>Protected Page Content</div>
      </ProtectedPage>
    )
    expect(container).toMatchSnapshot()
  })

  it('should match snapshot for unauthenticated user', () => {
    mockUseUserStore.mockReturnValue({
      user: null,
      setUser: jest.fn(),
      logout: jest.fn(),
    })

    const { container } = render(
      <ProtectedPage>
        <div>Protected Page Content</div>
      </ProtectedPage>
    )
    expect(container).toMatchSnapshot()
  })
})
