/**
 * Testes da Página de Financeiro
 */

import { render, screen, waitFor } from '@/__tests__/test-utils'
import { axe, toHaveNoViolations } from 'jest-axe'
import { useUserStore } from '@/lib/store/user'
import { mockUser } from '@/__tests__/test-utils'
import FinanceiroPage from '../page'

expect.extend(toHaveNoViolations)

jest.mock('@/lib/store/user')
const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('FinanceiroPage', () => {
  beforeEach(() => {
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: jest.fn(),
    })
  })

  describe('Renderização', () => {
    it('should render financeiro page title', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText(/financeiro/i)).toBeInTheDocument()
      })
    })

    it('should render tabs for contas a receber and contas a pagar', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /contas a receber/i })).toBeInTheDocument()
        expect(screen.getByRole('tab', { name: /contas a pagar/i })).toBeInTheDocument()
      })
    })

    it('should display financial summary', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText(/total a receber/i)).toBeInTheDocument()
        expect(screen.getByText(/total a pagar/i)).toBeInTheDocument()
        expect(screen.getByText(/saldo líquido/i)).toBeInTheDocument()
      })
    })
  })

  describe('Contas a Receber', () => {
    it('should display contas a receber list', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText('Venda #VND-00001')).toBeInTheDocument()
        expect(screen.getByText('Venda #VND-00002')).toBeInTheDocument()
      })
    })

    it('should show status badges', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText(/paga/i)).toBeInTheDocument()
        expect(screen.getByText(/pendente/i)).toBeInTheDocument()
      })
    })

    it('should filter by status', async () => {
      const { user } = render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText('Venda #VND-00001')).toBeInTheDocument()
      })

      const statusFilter = screen.getByRole('combobox', { name: /status/i })
      await user.selectOptions(statusFilter, 'pendente')

      await waitFor(() => {
        expect(screen.getByText('Venda #VND-00002')).toBeInTheDocument()
        expect(screen.queryByText('Venda #VND-00001')).not.toBeInTheDocument()
      })
    })

    it('should filter by date range', async () => {
      const { user } = render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText('Venda #VND-00001')).toBeInTheDocument()
      })

      const dateFromInput = screen.getByLabelText(/data inicial/i)
      const dateToInput = screen.getByLabelText(/data final/i)

      await user.type(dateFromInput, '2025-01-15')
      await user.type(dateToInput, '2025-01-15')

      await waitFor(() => {
        expect(screen.getByText('Venda #VND-00001')).toBeInTheDocument()
      })
    })

    it('should show overdue items', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/financeiro/contas-receber', () => {
          return HttpResponse.json([
            {
              id: 1,
              descricao: 'Venda Atrasada',
              valor: 100.00,
              valor_pago: 0,
              valor_pendente: 100.00,
              status: 'pendente',
              data_vencimento: '2025-01-01', // Data passada
              data_pagamento: null,
            },
          ])
        })
      )

      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText(/atrasada/i) || screen.getByTestId('overdue-badge')).toBeInTheDocument()
      })
    })
  })

  describe('Contas a Pagar', () => {
    it('should switch to contas a pagar tab', async () => {
      const { user } = render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /contas a pagar/i })).toBeInTheDocument()
      })

      const contasPagarTab = screen.getByRole('tab', { name: /contas a pagar/i })
      await user.click(contasPagarTab)

      await waitFor(() => {
        expect(screen.getByText('Fornecedor ABC - Compra #001')).toBeInTheDocument()
      })
    })

    it('should display contas a pagar list', async () => {
      const { user } = render(<FinanceiroPage />)

      const contasPagarTab = screen.getByRole('tab', { name: /contas a pagar/i })
      await user.click(contasPagarTab)

      await waitFor(() => {
        expect(screen.getByText(/5000[,.]00/)).toBeInTheDocument()
      })
    })
  })

  describe('Resumo Financeiro', () => {
    it('should calculate total a receber correctly', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        // Total: 329.00 + 160.00 = 489.00
        expect(screen.getByText(/489[,.]00/)).toBeInTheDocument()
      })
    })

    it('should calculate saldo líquido correctly', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        // Saldo: Receber (489) - Pagar (5000) = -4511
        expect(screen.getByText(/4511[,.]00/)).toBeInTheDocument()
      })
    })

    it('should show negative balance in red', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        const saldoElement = screen.getByText(/saldo líquido/i).nextElementSibling
        expect(saldoElement).toHaveClass('text-red-500')
      })
    })
  })

  describe('Ações', () => {
    it('should show register payment button', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        const payButton = screen.queryByRole('button', { name: /registrar pagamento/i })
        expect(payButton).toBeInTheDocument()
      })
    })

    it('should register payment for pending conta', async () => {
      const { user } = render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText('Venda #VND-00002')).toBeInTheDocument()
      })

      const payButton = screen.getAllByRole('button', { name: /pagar/i })[0]
      await user.click(payButton)

      await waitFor(() => {
        // Modal de pagamento deve aparecer
        expect(screen.getByText(/registrar pagamento/i)).toBeInTheDocument()
      })
    })
  })

  describe('Estados', () => {
    it('should show loading state', () => {
      render(<FinanceiroPage />)

      expect(screen.getByText(/carregando/i) || screen.getByRole('status')).toBeInTheDocument()
    })

    it('should handle empty state for contas a receber', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/financeiro/contas-receber', () => {
          return HttpResponse.json([])
        })
      )

      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText(/nenhuma conta a receber/i)).toBeInTheDocument()
      })
    })

    it('should handle error state', async () => {
      const { server } = await import('@/__tests__/mocks/server')
      const { http, HttpResponse } = await import('msw')

      server.use(
        http.get('*/api/v1/financeiro/resumo', () => {
          return HttpResponse.json(
            { detail: 'Erro ao carregar dados financeiros' },
            { status: 500 }
          )
        })
      )

      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText(/erro/i)).toBeInTheDocument()
      })
    })
  })

  describe('Permissões', () => {
    it('should show all actions for admin', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText('Venda #VND-00001')).toBeInTheDocument()
      })

      expect(screen.queryByRole('button', { name: /pagar/i })).toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /editar/i })).toBeInTheDocument()
    })

    it('should limit actions for non-admin users', async () => {
      const vendedor = {
        id: 2,
        username: 'vendedor',
        email: 'vendedor@siscom.com',
        role: {
          name: 'Vendedor',
          permissions: ['financeiro.view'],
        },
      }

      mockUseUserStore.mockReturnValue({
        user: vendedor,
        setUser: jest.fn(),
        logout: jest.fn(),
      })

      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText('Venda #VND-00001')).toBeInTheDocument()
      })

      expect(screen.queryByRole('button', { name: /editar/i })).not.toBeInTheDocument()
    })
  })

  describe('Relatórios', () => {
    it('should show export button', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        const exportButton = screen.queryByRole('button', { name: /exportar/i })
        expect(exportButton).toBeInTheDocument()
      })
    })

    it('should export financial report', async () => {
      const { user } = render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText('Venda #VND-00001')).toBeInTheDocument()
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
      const { container } = render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText(/financeiro/i)).toBeInTheDocument()
      })

      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('should have proper tab navigation', async () => {
      const { user } = render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByRole('tab', { name: /contas a receber/i })).toBeInTheDocument()
      })

      const contasReceberTab = screen.getByRole('tab', { name: /contas a receber/i })
      const contasPagarTab = screen.getByRole('tab', { name: /contas a pagar/i })

      expect(contasReceberTab).toHaveAttribute('aria-selected', 'true')
      expect(contasPagarTab).toHaveAttribute('aria-selected', 'false')

      await user.click(contasPagarTab)

      expect(contasPagarTab).toHaveAttribute('aria-selected', 'true')
      expect(contasReceberTab).toHaveAttribute('aria-selected', 'false')
    })
  })

  describe('Gráficos', () => {
    it('should display financial charts', async () => {
      render(<FinanceiroPage />)

      await waitFor(() => {
        expect(screen.getByText(/fluxo de caixa/i) || screen.getByTestId('cash-flow-chart')).toBeInTheDocument()
      })
    })
  })
})
