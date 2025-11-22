/**
 * Testes da Página de Produtos
 */

import { render, screen, waitFor } from '@/__tests__/test-utils'
import { axe, toHaveNoViolations } from 'jest-axe'
import { useUserStore } from '@/lib/store/user'
import { mockUser } from '@/__tests__/test-utils'
import ProdutosPage from '../page'

expect.extend(toHaveNoViolations)

jest.mock('@/lib/store/user')
const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('ProdutosPage', () => {
  beforeEach(() => {
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: jest.fn(),
    })
  })

  describe('Renderização', () => {
    it('should render produtos page title', async () => {
      render(<ProdutosPage />)

      await waitFor(() => {
        expect(screen.getByText(/produtos/i)).toBeInTheDocument()
      })
    })

    it('should render produtos list after loading', async () => {
      render(<ProdutosPage />)

      // Aguardar dados serem carregados (MSW retorna mock)
      await waitFor(() => {
        expect(screen.getByText('Cimento CP-II 50kg')).toBeInTheDocument()
        expect(screen.getByText('Areia Média m³')).toBeInTheDocument()
      })
    })

    it('should display produtos in a table format', async () => {
      render(<ProdutosPage />)

      await waitFor(() => {
        const table = screen.getByRole('table')
        expect(table).toBeInTheDocument()
      })
    })
  })

  describe('Funcionalidades', () => {
    it('should show add button for users with create permission', async () => {
      render(<ProdutosPage />)

      await waitFor(() => {
        const addButton = screen.queryByRole('button', { name: /novo produto/i })
        expect(addButton).toBeInTheDocument()
      })
    })

    it('should filter produtos by search term', async () => {
      const { user } = render(<ProdutosPage />)

      // Aguardar lista carregar
      await waitFor(() => {
        expect(screen.getByText('Cimento CP-II 50kg')).toBeInTheDocument()
      })

      // Procurar campo de busca
      const searchInput = screen.getByPlaceholderText(/buscar/i)
      await user.type(searchInput, 'cimento')

      await waitFor(() => {
        expect(screen.getByText('Cimento CP-II 50kg')).toBeInTheDocument()
        // Areia não deve aparecer
        expect(screen.queryByText('Areia Média m³')).not.toBeInTheDocument()
      })
    })
  })

  describe('Estados', () => {
    it('should show loading state initially', () => {
      render(<ProdutosPage />)

      // Verificar se tem indicador de loading
      expect(screen.getByText(/carregando/i) || screen.getByRole('status')).toBeInTheDocument()
    })

    it('should handle empty state', async () => {
      // Mock retorno vazio
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/produtos', () => {
          return HttpResponse.json([])
        })
      )

      render(<ProdutosPage />)

      await waitFor(() => {
        expect(screen.getByText(/nenhum produto/i)).toBeInTheDocument()
      })
    })

    it('should handle error state', async () => {
      // Mock erro de API
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/produtos', () => {
          return HttpResponse.json(
            { detail: 'Erro ao carregar produtos' },
            { status: 500 }
          )
        })
      )

      render(<ProdutosPage />)

      await waitFor(() => {
        expect(screen.getByText(/erro/i)).toBeInTheDocument()
      })
    })
  })

  describe('Permissões', () => {
    it('should not show delete button without permission', async () => {
      const vendedor = {
        id: 2,
        username: 'vendedor',
        email: 'vendedor@siscom.com',
        role: {
          name: 'Vendedor',
          permissions: ['produtos.view'],
        },
      }

      mockUseUserStore.mockReturnValue({
        user: vendedor,
        setUser: jest.fn(),
        logout: jest.fn(),
      })

      render(<ProdutosPage />)

      await waitFor(() => {
        expect(screen.getByText('Cimento CP-II 50kg')).toBeInTheDocument()
      })

      // Botão de deletar não deve aparecer
      expect(screen.queryByRole('button', { name: /excluir/i })).not.toBeInTheDocument()
    })
  })

  describe('Acessibilidade', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(<ProdutosPage />)

      await waitFor(() => {
        expect(screen.getByText(/produtos/i)).toBeInTheDocument()
      })

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should have proper heading hierarchy', async () => {
      render(<ProdutosPage />)

      await waitFor(() => {
        const headings = screen.getAllByRole('heading')
        expect(headings.length).toBeGreaterThan(0)
        // H1 deve ser o primeiro
        expect(headings[0].tagName).toBe('H1')
      })
    })

    it('should have keyboard navigation support', async () => {
      const { user } = render(<ProdutosPage />)

      await waitFor(() => {
        expect(screen.getByText('Cimento CP-II 50kg')).toBeInTheDocument()
      })

      const firstButton = screen.getAllByRole('button')[0]
      firstButton.focus()

      expect(document.activeElement).toBe(firstButton)

      // Tab para próximo elemento
      await user.tab()
      expect(document.activeElement).not.toBe(firstButton)
    })
  })

  describe('Performance', () => {
    it('should render large list efficiently', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      // Mock 100 produtos
      const largeProdutosList = Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        codigo: `PROD-${String(i + 1).padStart(3, '0')}`,
        descricao: `Produto ${i + 1}`,
        preco_venda: Math.random() * 100,
        categoria_id: 1,
        estoque_atual: Math.floor(Math.random() * 100),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }))

      server.use(
        http.get('*/api/v1/produtos', () => {
          return HttpResponse.json(largeProdutosList)
        })
      )

      const startTime = performance.now()
      render(<ProdutosPage />)

      await waitFor(() => {
        expect(screen.getByText('Produto 1')).toBeInTheDocument()
      })

      const endTime = performance.now()
      const renderTime = endTime - startTime

      // Deve renderizar em menos de 2 segundos
      expect(renderTime).toBeLessThan(2000)
    })
  })
})
