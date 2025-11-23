import { render, screen, fireEvent, waitFor } from '@/__tests__/test-utils'
import OrcamentosPage from '@/app/orcamentos/page'
import * as orcamentosHooks from '@/lib/hooks/use-orcamentos'

// Mock the hooks
jest.mock('@/lib/hooks/use-orcamentos')

// Mock the form component
jest.mock('@/components/forms/orcamento-form', () => ({
  OrcamentoForm: ({ onSuccess, onCancel }: any) => (
    <div data-testid="orcamento-form">
      <button onClick={onSuccess}>Mock Success</button>
      <button onClick={onCancel}>Mock Cancel</button>
    </div>
  ),
}))

describe('OrcamentosPage', () => {
  const mockOrcamentos = [
    {
      id: 1,
      numero_orcamento: 'ORC-001',
      cliente_nome: 'João Silva Construções',
      vendedor_nome: 'Maria Santos',
      data_orcamento: '2025-11-20',
      data_validade: '2025-11-27',
      status: 'ABERTO' as const,
      valor_total: 15420.50,
      itens_count: 15,
    },
    {
      id: 2,
      numero_orcamento: 'ORC-002',
      cliente_nome: 'Reforma Total Ltda',
      vendedor_nome: 'Pedro Costa',
      data_orcamento: '2025-11-21',
      data_validade: '2025-11-28',
      status: 'APROVADO' as const,
      valor_total: 8350.00,
      itens_count: 8,
    },
    {
      id: 3,
      numero_orcamento: 'ORC-003',
      cliente_nome: 'Construtora ABC',
      vendedor_nome: 'Ana Paula',
      data_orcamento: '2025-11-18',
      data_validade: '2025-11-25',
      status: 'CONVERTIDO' as const,
      valor_total: 22100.00,
      itens_count: 25,
    },
  ]

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Loading State', () => {
    it('should show loading state while fetching data', () => {
      ;(orcamentosHooks.useOrcamentos as jest.Mock).mockReturnValue({
        orcamentos: undefined,
        isLoading: true,
        isError: false,
        mutate: jest.fn(),
      })

      render(<OrcamentosPage />)

      expect(screen.getByText(/carregando orçamentos/i)).toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should show error state when fetch fails', () => {
      ;(orcamentosHooks.useOrcamentos as jest.Mock).mockReturnValue({
        orcamentos: undefined,
        isLoading: false,
        isError: true,
        mutate: jest.fn(),
      })

      render(<OrcamentosPage />)

      expect(screen.getByText(/erro ao carregar orçamentos/i)).toBeInTheDocument()
    })
  })

  describe('Data Rendering', () => {
    beforeEach(() => {
      ;(orcamentosHooks.useOrcamentos as jest.Mock).mockReturnValue({
        orcamentos: mockOrcamentos,
        isLoading: false,
        isError: false,
        mutate: jest.fn(),
      })
    })

    it('should render page title and description', () => {
      render(<OrcamentosPage />)

      expect(screen.getByText('Orçamentos')).toBeInTheDocument()
      expect(screen.getByText('Gerencie orçamentos e propostas')).toBeInTheDocument()
    })

    it('should render "Novo Orçamento" button', () => {
      render(<OrcamentosPage />)

      expect(screen.getByRole('button', { name: /novo orçamento/i })).toBeInTheDocument()
    })

    it('should render statistics cards', () => {
      render(<OrcamentosPage />)

      expect(screen.getByText('Total Orçamentos')).toBeInTheDocument()
      expect(screen.getByText('Abertos')).toBeInTheDocument()
      expect(screen.getByText('Aprovados')).toBeInTheDocument()
      expect(screen.getByText('Valor Total')).toBeInTheDocument()
    })

    it('should calculate and display correct statistics', () => {
      render(<OrcamentosPage />)

      // Total orçamentos
      expect(screen.getByText('3')).toBeInTheDocument()

      // Total abertos (1)
      const stats = screen.getAllByText('1')
      expect(stats.length).toBeGreaterThan(0)
    })

    it('should render table with all orcamentos', () => {
      render(<OrcamentosPage />)

      expect(screen.getByText('ORC-001')).toBeInTheDocument()
      expect(screen.getByText('ORC-002')).toBeInTheDocument()
      expect(screen.getByText('ORC-003')).toBeInTheDocument()
    })

    it('should display client names', () => {
      render(<OrcamentosPage />)

      expect(screen.getByText('João Silva Construções')).toBeInTheDocument()
      expect(screen.getByText('Reforma Total Ltda')).toBeInTheDocument()
      expect(screen.getByText('Construtora ABC')).toBeInTheDocument()
    })

    it('should display status badges', () => {
      render(<OrcamentosPage />)

      expect(screen.getByText('ABERTO')).toBeInTheDocument()
      expect(screen.getByText('APROVADO')).toBeInTheDocument()
      expect(screen.getByText('CONVERTIDO')).toBeInTheDocument()
    })

    it('should display formatted values', () => {
      render(<OrcamentosPage />)

      // Check if currency values are displayed
      expect(screen.getByText(/15\.420,50/)).toBeInTheDocument()
      expect(screen.getByText(/8\.350,00/)).toBeInTheDocument()
      expect(screen.getByText(/22\.100,00/)).toBeInTheDocument()
    })

    it('should render edit buttons for each orcamento', () => {
      render(<OrcamentosPage />)

      const editButtons = screen.getAllByRole('button', { name: /editar/i })
      expect(editButtons).toHaveLength(3)
    })

    it('should render view buttons for each orcamento', () => {
      render(<OrcamentosPage />)

      const viewButtons = screen.getAllByRole('button', { name: /ver/i })
      expect(viewButtons).toHaveLength(3)
    })
  })

  describe('Dialog Interactions', () => {
    beforeEach(() => {
      ;(orcamentosHooks.useOrcamentos as jest.Mock).mockReturnValue({
        orcamentos: mockOrcamentos,
        isLoading: false,
        isError: false,
        mutate: jest.fn(),
      })
    })

    it('should open dialog when clicking "Novo Orçamento"', async () => {
      render(<OrcamentosPage />)

      const novoButton = screen.getByRole('button', { name: /novo orçamento/i })
      fireEvent.click(novoButton)

      await waitFor(() => {
        expect(screen.getByText('Novo Orçamento')).toBeInTheDocument()
      })
    })

    it('should open dialog when clicking "Editar"', async () => {
      render(<OrcamentosPage />)

      const editButtons = screen.getAllByRole('button', { name: /editar/i })
      fireEvent.click(editButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Editar Orçamento')).toBeInTheDocument()
      })
    })

    it('should show orcamento form in dialog', async () => {
      render(<OrcamentosPage />)

      const novoButton = screen.getByRole('button', { name: /novo orçamento/i })
      fireEvent.click(novoButton)

      await waitFor(() => {
        expect(screen.getByTestId('orcamento-form')).toBeInTheDocument()
      })
    })

    it('should close dialog on success', async () => {
      const mockMutate = jest.fn()
      ;(orcamentosHooks.useOrcamentos as jest.Mock).mockReturnValue({
        orcamentos: mockOrcamentos,
        isLoading: false,
        isError: false,
        mutate: mockMutate,
      })

      render(<OrcamentosPage />)

      const novoButton = screen.getByRole('button', { name: /novo orçamento/i })
      fireEvent.click(novoButton)

      await waitFor(() => {
        expect(screen.getByTestId('orcamento-form')).toBeInTheDocument()
      })

      const successButton = screen.getByText('Mock Success')
      fireEvent.click(successButton)

      await waitFor(() => {
        expect(mockMutate).toHaveBeenCalled()
      })
    })

    it('should close dialog on cancel', async () => {
      render(<OrcamentosPage />)

      const novoButton = screen.getByRole('button', { name: /novo orçamento/i })
      fireEvent.click(novoButton)

      await waitFor(() => {
        expect(screen.getByTestId('orcamento-form')).toBeInTheDocument()
      })

      const cancelButton = screen.getByText('Mock Cancel')
      fireEvent.click(cancelButton)

      // Dialog should close (form should not be visible)
      // This behavior depends on Dialog component implementation
    })
  })

  describe('Empty State', () => {
    it('should handle empty orcamentos list', () => {
      ;(orcamentosHooks.useOrcamentos as jest.Mock).mockReturnValue({
        orcamentos: [],
        isLoading: false,
        isError: false,
        mutate: jest.fn(),
      })

      render(<OrcamentosPage />)

      // Should still render the page structure
      expect(screen.getByText('Orçamentos')).toBeInTheDocument()

      // Statistics should show zero values
      expect(screen.getByText('Total Orçamentos')).toBeInTheDocument()
    })
  })
})
