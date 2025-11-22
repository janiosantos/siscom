import React from 'react'
import { render, screen } from '@/__tests__/test-utils'
import DashboardPage from '../page'
import { useUserStore } from '@/lib/store/user'
import { mockUser } from '@/__tests__/test-utils'

// Mock the user store
jest.mock('@/lib/store/user', () => ({
  useUserStore: jest.fn(),
}))

// Mock Recharts to avoid canvas issues in tests
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Line: () => null,
  Pie: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  Cell: () => null,
}))

const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('DashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: jest.fn(),
    })
  })

  it('should render dashboard title', () => {
    render(<DashboardPage />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText(/Visão geral do sistema/i)).toBeInTheDocument()
  })

  it('should render KPI cards', () => {
    render(<DashboardPage />)

    // Check for KPI titles
    expect(screen.getByText('Vendas do Mês')).toBeInTheDocument()
    expect(screen.getByText('Produtos Cadastrados')).toBeInTheDocument()
    expect(screen.getByText('Clientes Ativos')).toBeInTheDocument()
    expect(screen.getByText('Pedidos Pendentes')).toBeInTheDocument()
  })

  it('should render KPI values', () => {
    render(<DashboardPage />)

    // Check for mock values
    expect(screen.getByText('R$ 145.280,00')).toBeInTheDocument()
    expect(screen.getByText('1.234')).toBeInTheDocument()
    expect(screen.getByText('856')).toBeInTheDocument()
    expect(screen.getByText('23')).toBeInTheDocument()
  })

  it('should render growth indicators', () => {
    render(<DashboardPage />)

    // Check for percentage indicators
    expect(screen.getByText('+12.5%')).toBeInTheDocument()
    expect(screen.getByText('+5.2%')).toBeInTheDocument()
    expect(screen.getByText('+8.1%')).toBeInTheDocument()
  })

  it('should render charts section', () => {
    render(<DashboardPage />)

    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument()
  })

  it('should render sales vs costs chart title', () => {
    render(<DashboardPage />)

    expect(screen.getByText('Vendas vs Custo (6 meses)')).toBeInTheDocument()
  })

  it('should render category distribution chart title', () => {
    render(<DashboardPage />)

    expect(screen.getByText('Distribuição por Categoria')).toBeInTheDocument()
  })

  it('should render top products section', () => {
    render(<DashboardPage />)

    expect(screen.getByText('Top 5 Produtos')).toBeInTheDocument()
  })

  it('should render top product names', () => {
    render(<DashboardPage />)

    expect(screen.getByText('Cimento CP-II 50kg')).toBeInTheDocument()
    expect(screen.getByText('Tijolo Cerâmico 6 furos')).toBeInTheDocument()
    expect(screen.getByText('Areia Lavada (m³)')).toBeInTheDocument()
    expect(screen.getByText('Brita 1 (m³)')).toBeInTheDocument()
    expect(screen.getByText('Cal Hidratada 20kg')).toBeInTheDocument()
  })

  it('should render product sales quantities', () => {
    render(<DashboardPage />)

    expect(screen.getByText('1.245 vendas')).toBeInTheDocument()
    expect(screen.getByText('986 vendas')).toBeInTheDocument()
    expect(screen.getByText('845 vendas')).toBeInTheDocument()
    expect(screen.getByText('723 vendas')).toBeInTheDocument()
    expect(screen.getByText('654 vendas')).toBeInTheDocument()
  })

  it('should render product trends', () => {
    render(<DashboardPage />)

    // All mock products have positive trend
    const trendTexts = screen.getAllByText('+5%')
    expect(trendTexts.length).toBeGreaterThan(0)
  })

  describe('Responsive behavior', () => {
    it('should render grid layout', () => {
      const { container } = render(<DashboardPage />)

      const gridElements = container.querySelectorAll('.grid')
      expect(gridElements.length).toBeGreaterThan(0)
    })
  })

  describe('Without user', () => {
    it('should still render when user is null', () => {
      mockUseUserStore.mockReturnValue({
        user: null,
        setUser: jest.fn(),
        logout: jest.fn(),
      })

      render(<DashboardPage />)

      // Dashboard should still render basic structure
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
  })
})
