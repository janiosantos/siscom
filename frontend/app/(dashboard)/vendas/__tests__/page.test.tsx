/**
 * Testes da Página de Vendas
 */

import { render, screen, waitFor } from '@/__tests__/test-utils'
import { axe, toHaveNoViolations } from 'jest-axe'
import { useUserStore } from '@/lib/store/user'
import { mockUser } from '@/__tests__/test-utils'
import VendasPage from '../page'

expect.extend(toHaveNoViolations)

jest.mock('@/lib/store/user')
const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('VendasPage', () => {
  beforeEach(() => {
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: jest.fn(),
    })
  })

  describe('Renderização', () => {
    it('should render vendas page title', async () => {
      render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText(/vendas/i)).toBeInTheDocument()
      })
    })

    it('should render vendas list', async () => {
      render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText('VND-00001')).toBeInTheDocument()
        expect(screen.getByText('VND-00002')).toBeInTheDocument()
      })
    })

    it('should display venda details', async () => {
      render(<VendasPage />)

      await waitFor(() => {
        // Verificar cliente
        expect(screen.getByText('João Silva')).toBeInTheDocument()
        expect(screen.getByText('Maria Santos')).toBeInTheDocument()

        // Verificar valores
        expect(screen.getByText(/329[,.]00/)).toBeInTheDocument()
        expect(screen.getByText(/160[,.]00/)).toBeInTheDocument()
      })
    })
  })

  describe('Funcionalidades', () => {
    it('should show add new venda button', async () => {
      render(<VendasPage />)

      await waitFor(() => {
        const addButton = screen.queryByRole('button', { name: /nova venda/i })
        expect(addButton).toBeInTheDocument()
      })
    })

    it('should filter vendas by status', async () => {
      const { user } = render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText('VND-00001')).toBeInTheDocument()
      })

      const statusFilter = screen.getByRole('combobox', { name: /status/i })
      await user.selectOptions(statusFilter, 'finalizada')

      await waitFor(() => {
        expect(screen.getByText('VND-00001')).toBeInTheDocument()
      })
    })

    it('should filter vendas by date range', async () => {
      const { user } = render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText('VND-00001')).toBeInTheDocument()
      })

      const dateFromInput = screen.getByLabelText(/data inicial/i)
      const dateToInput = screen.getByLabelText(/data final/i)

      await user.type(dateFromInput, '2025-01-15')
      await user.type(dateToInput, '2025-01-15')

      await waitFor(() => {
        expect(screen.getByText('VND-00001')).toBeInTheDocument()
        expect(screen.queryByText('VND-00002')).not.toBeInTheDocument()
      })
    })

    it('should show venda details on click', async () => {
      const { user } = render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText('VND-00001')).toBeInTheDocument()
      })

      const vendaRow = screen.getByText('VND-00001')
      await user.click(vendaRow)

      await waitFor(() => {
        // Modal ou seção de detalhes deve aparecer
        expect(screen.getByText(/detalhes da venda/i)).toBeInTheDocument()
        expect(screen.getByText(/itens/i)).toBeInTheDocument()
      })
    })
  })

  describe('Estados', () => {
    it('should show loading state', () => {
      render(<VendasPage />)

      expect(screen.getByText(/carregando/i) || screen.getByRole('status')).toBeInTheDocument()
    })

    it('should handle empty state', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/vendas', () => {
          return HttpResponse.json([])
        })
      )

      render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText(/nenhuma venda/i)).toBeInTheDocument()
      })
    })

    it('should handle error state', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/vendas', () => {
          return HttpResponse.json(
            { detail: 'Erro ao carregar vendas' },
            { status: 500 }
          )
        })
      )

      render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText(/erro/i)).toBeInTheDocument()
      })
    })
  })

  describe('Permissões', () => {
    it('should show cancel button only for authorized users', async () => {
      render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText('VND-00001')).toBeInTheDocument()
      })

      const cancelButtons = screen.queryAllByRole('button', { name: /cancelar/i })
      expect(cancelButtons.length).toBeGreaterThan(0)
    })

    it('should not show cancel button for users without permission', async () => {
      const vendedor = {
        id: 2,
        username: 'vendedor',
        email: 'vendedor@siscom.com',
        role: {
          name: 'Vendedor',
          permissions: ['vendas.view'],
        },
      }

      mockUseUserStore.mockReturnValue({
        user: vendedor,
        setUser: jest.fn(),
        logout: jest.fn(),
      })

      render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText('VND-00001')).toBeInTheDocument()
      })

      expect(screen.queryByRole('button', { name: /cancelar/i })).not.toBeInTheDocument()
    })
  })

  describe('Cálculos', () => {
    it('should display correct totals', async () => {
      render(<VendasPage />)

      await waitFor(() => {
        // Verificar valores totais
        expect(screen.getByText(/total:/i)).toBeInTheDocument()

        // Soma de todas as vendas: 329 + 160 = 489
        expect(screen.getByText(/489[,.]00/)).toBeInTheDocument()
      })
    })

    it('should calculate discount correctly', async () => {
      render(<VendasPage />)

      await waitFor(() => {
        // VND-00002 tem desconto de 10.00
        expect(screen.getByText(/desconto/i)).toBeInTheDocument()
        expect(screen.getByText(/10[,.]00/)).toBeInTheDocument()
      })
    })
  })

  describe('Acessibilidade', () => {
    it('should not have accessibility violations', async () => {
      const { container } = render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText(/vendas/i)).toBeInTheDocument()
      })

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should have proper ARIA labels', async () => {
      render(<VendasPage />)

      await waitFor(() => {
        const table = screen.getByRole('table')
        expect(table).toHaveAttribute('aria-label')
      })
    })
  })

  describe('Exportação', () => {
    it('should have export button', async () => {
      render(<VendasPage />)

      await waitFor(() => {
        const exportButton = screen.queryByRole('button', { name: /exportar/i })
        expect(exportButton).toBeInTheDocument()
      })
    })

    it('should export vendas to PDF', async () => {
      const { user } = render(<VendasPage />)

      await waitFor(() => {
        expect(screen.getByText('VND-00001')).toBeInTheDocument()
      })

      const exportButton = screen.getByRole('button', { name: /exportar/i })
      await user.click(exportButton)

      // Verificar se opção PDF está disponível
      await waitFor(() => {
        expect(screen.getByText(/pdf/i)).toBeInTheDocument()
      })
    })
  })
})
