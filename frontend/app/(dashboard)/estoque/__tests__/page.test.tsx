/**
 * Testes da Página de Estoque
 */

import { render, screen, waitFor } from '@/__tests__/test-utils'
import { axe, toHaveNoViolations } from 'jest-axe'
import { useUserStore } from '@/lib/store/user'
import { mockUser, mockEstoquista } from '@/__tests__/test-utils'
import EstoquePage from '../page'

expect.extend(toHaveNoViolations)

jest.mock('@/lib/store/user')
const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('EstoquePage', () => {
  beforeEach(() => {
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: jest.fn(),
    })
  })

  describe('Renderização', () => {
    it('should render estoque page title', async () => {
      render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText(/estoque/i)).toBeInTheDocument()
      })
    })

    it('should render estoque list', async () => {
      render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText('CIM-001')).toBeInTheDocument()
        expect(screen.getByText('ARE-001')).toBeInTheDocument()
      })
    })

    it('should display product quantities', async () => {
      render(<EstoquePage />)

      await waitFor(() => {
        // Cimento: 100 unidades
        expect(screen.getByText(/100/)).toBeInTheDocument()
        // Areia: 50 unidades
        expect(screen.getByText(/50/)).toBeInTheDocument()
      })
    })

    it('should display product locations', async () => {
      render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText('A1-01')).toBeInTheDocument()
        expect(screen.getByText('B2-03')).toBeInTheDocument()
      })
    })
  })

  describe('Funcionalidades', () => {
    it('should show adjustment button for authorized users', async () => {
      render(<EstoquePage />)

      await waitFor(() => {
        const adjustButton = screen.queryByRole('button', { name: /ajustar/i })
        expect(adjustButton).toBeInTheDocument()
      })
    })

    it('should filter by low stock items', async () => {
      const { user } = render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText('CIM-001')).toBeInTheDocument()
      })

      const lowStockFilter = screen.getByRole('checkbox', { name: /estoque baixo/i })
      await user.click(lowStockFilter)

      await waitFor(() => {
        // Filtrar produtos com quantidade < mínima
        expect(screen.queryByText('CIM-001')).toBeInTheDocument()
      })
    })

    it('should search by product code or description', async () => {
      const { user } = render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText('CIM-001')).toBeInTheDocument()
      })

      const searchInput = screen.getByPlaceholderText(/buscar/i)
      await user.type(searchInput, 'cimento')

      await waitFor(() => {
        expect(screen.getByText('Cimento CP-II 50kg')).toBeInTheDocument()
        expect(screen.queryByText('Areia Média m³')).not.toBeInTheDocument()
      })
    })
  })

  describe('Indicadores Visuais', () => {
    it('should highlight low stock items', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/estoque', () => {
          return HttpResponse.json([
            {
              id: 1,
              produto_id: 1,
              produto_codigo: 'CIM-001',
              produto_descricao: 'Cimento CP-II 50kg',
              quantidade_atual: 10,
              quantidade_minima: 20,
              quantidade_maxima: 200,
              localizacao: 'A1-01',
            },
          ])
        })
      )

      render(<EstoquePage />)

      await waitFor(() => {
        // Verificar se há indicador visual de estoque baixo
        const lowStockIndicator = screen.getByText(/estoque baixo/i) ||
                                  screen.getByTestId('low-stock-indicator')
        expect(lowStockIndicator).toBeInTheDocument()
      })
    })

    it('should highlight items without location', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/estoque', () => {
          return HttpResponse.json([
            {
              id: 1,
              produto_id: 1,
              produto_codigo: 'CIM-001',
              produto_descricao: 'Cimento CP-II 50kg',
              quantidade_atual: 100,
              quantidade_minima: 20,
              quantidade_maxima: 200,
              localizacao: null,
            },
          ])
        })
      )

      render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText(/sem localização/i)).toBeInTheDocument()
      })
    })
  })

  describe('Movimentações', () => {
    it('should show movement history button', async () => {
      render(<EstoquePage />)

      await waitFor(() => {
        const historyButton = screen.queryByRole('button', { name: /histórico/i })
        expect(historyButton).toBeInTheDocument()
      })
    })

    it('should display last movement date', async () => {
      render(<EstoquePage />)

      await waitFor(() => {
        // Verificar se a última movimentação está sendo exibida
        expect(screen.getByText(/última movimentação/i)).toBeInTheDocument()
      })
    })
  })

  describe('Estados', () => {
    it('should show loading state', () => {
      render(<EstoquePage />)

      expect(screen.getByText(/carregando/i) || screen.getByRole('status')).toBeInTheDocument()
    })

    it('should handle empty state', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/estoque', () => {
          return HttpResponse.json([])
        })
      )

      render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText(/nenhum item no estoque/i)).toBeInTheDocument()
      })
    })

    it('should handle error state', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/estoque', () => {
          return HttpResponse.json(
            { detail: 'Erro ao carregar estoque' },
            { status: 500 }
          )
        })
      )

      render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText(/erro/i)).toBeInTheDocument()
      })
    })
  })

  describe('Permissões', () => {
    it('should allow estoquista to adjust stock', async () => {
      mockUseUserStore.mockReturnValue({
        user: mockEstoquista,
        setUser: jest.fn(),
        logout: jest.fn(),
      })

      render(<EstoquePage />)

      await waitFor(() => {
        const adjustButton = screen.queryByRole('button', { name: /ajustar/i })
        expect(adjustButton).toBeInTheDocument()
      })
    })

    it('should not allow vendedor to adjust stock', async () => {
      const vendedor = {
        id: 2,
        username: 'vendedor',
        email: 'vendedor@siscom.com',
        role: {
          name: 'Vendedor',
          permissions: ['estoque.view'],
        },
      }

      mockUseUserStore.mockReturnValue({
        user: vendedor,
        setUser: jest.fn(),
        logout: jest.fn(),
      })

      render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText('CIM-001')).toBeInTheDocument()
      })

      expect(screen.queryByRole('button', { name: /ajustar/i })).not.toBeInTheDocument()
    })
  })

  describe('Relatórios', () => {
    it('should show stock summary', async () => {
      render(<EstoquePage />)

      await waitFor(() => {
        // Resumo: total de itens, valor total, itens em falta
        expect(screen.getByText(/total de itens/i)).toBeInTheDocument()
        expect(screen.getByText(/valor total/i)).toBeInTheDocument()
      })
    })

    it('should export stock report', async () => {
      const { user } = render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText('CIM-001')).toBeInTheDocument()
      })

      const exportButton = screen.getByRole('button', { name: /exportar/i })
      await user.click(exportButton)

      await waitFor(() => {
        expect(screen.getByText(/exportar relatório/i)).toBeInTheDocument()
      })
    })
  })

  describe('Acessibilidade', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText(/estoque/i)).toBeInTheDocument()
      })

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should have proper keyboard navigation', async () => {
      const { user } = render(<EstoquePage />)

      await waitFor(() => {
        expect(screen.getByText('CIM-001')).toBeInTheDocument()
      })

      const firstButton = screen.getAllByRole('button')[0]
      firstButton.focus()

      expect(document.activeElement).toBe(firstButton)

      await user.tab()
      expect(document.activeElement).not.toBe(firstButton)
    })
  })

  describe('Inventário', () => {
    it('should show inventory button', async () => {
      render(<EstoquePage />)

      await waitFor(() => {
        const inventoryButton = screen.queryByRole('button', { name: /inventário/i })
        expect(inventoryButton).toBeInTheDocument()
      })
    })
  })
})
