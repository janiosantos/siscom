import {
  exportToPDF,
  exportProdutosToPDF,
  exportVendasToPDF,
  exportEstoqueToPDF,
  exportFinanceiroToPDF,
} from '../pdf-export'
import jsPDF from 'jspdf'

// Mock jsPDF
jest.mock('jspdf', () => {
  return jest.fn().mockImplementation(() => ({
    text: jest.fn(),
    setFontSize: jest.fn(),
    save: jest.fn(),
    autoTable: jest.fn(),
  }))
})

// Mock jspdf-autotable
jest.mock('jspdf-autotable', () => jest.fn())

describe('PDF Export Utilities', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('exportToPDF', () => {
    it('should create PDF with correct title', () => {
      const mockDoc = {
        text: jest.fn(),
        setFontSize: jest.fn(),
        save: jest.fn(),
      }
      ;(jsPDF as jest.MockedClass<typeof jsPDF>).mockImplementation(() => mockDoc as any)

      exportToPDF({
        title: 'Test Report',
        subtitle: 'Test Subtitle',
        columns: [
          { header: 'Name', dataKey: 'name' },
          { header: 'Value', dataKey: 'value' },
        ],
        data: [{ name: 'Item 1', value: '100' }],
        filename: 'test.pdf',
      })

      expect(mockDoc.setFontSize).toHaveBeenCalledWith(18)
      expect(mockDoc.text).toHaveBeenCalledWith('Test Report', 14, 20)
    })

    it('should save PDF with correct filename', () => {
      const mockDoc = {
        text: jest.fn(),
        setFontSize: jest.fn(),
        save: jest.fn(),
      }
      ;(jsPDF as jest.MockedClass<typeof jsPDF>).mockImplementation(() => mockDoc as any)

      exportToPDF({
        title: 'Test',
        columns: [{ header: 'Col', dataKey: 'col' }],
        data: [],
        filename: 'my-report.pdf',
      })

      expect(mockDoc.save).toHaveBeenCalledWith('my-report.pdf')
    })
  })

  describe('exportProdutosToPDF', () => {
    it('should export produtos with correct structure', () => {
      const mockSave = jest.fn()
      const mockDoc = {
        text: jest.fn(),
        setFontSize: jest.fn(),
        save: mockSave,
      }
      ;(jsPDF as jest.MockedClass<typeof jsPDF>).mockImplementation(() => mockDoc as any)

      const produtos = [
        {
          id: 1,
          codigo: 'PROD-001',
          descricao: 'Produto 1',
          categoria: { nome: 'Categoria 1' },
          preco_venda: 100,
          estoque_atual: 50,
        },
      ]

      exportProdutosToPDF(produtos)

      expect(mockDoc.text).toHaveBeenCalledWith('Relatório de Produtos', 14, 20)
      expect(mockSave).toHaveBeenCalledWith('produtos.pdf')
    })

    it('should handle empty produtos array', () => {
      const mockSave = jest.fn()
      const mockDoc = {
        text: jest.fn(),
        setFontSize: jest.fn(),
        save: mockSave,
      }
      ;(jsPDF as jest.MockedClass<typeof jsPDF>).mockImplementation(() => mockDoc as any)

      exportProdutosToPDF([])

      expect(mockSave).toHaveBeenCalledWith('produtos.pdf')
    })
  })

  describe('exportVendasToPDF', () => {
    it('should export vendas with correct structure', () => {
      const mockSave = jest.fn()
      const mockDoc = {
        text: jest.fn(),
        setFontSize: jest.fn(),
        save: mockSave,
      }
      ;(jsPDF as jest.MockedClass<typeof jsPDF>).mockImplementation(() => mockDoc as any)

      const vendas = [
        {
          id: 1,
          created_at: '2025-11-22T10:00:00',
          cliente: { nome: 'Cliente 1' },
          total: 1000,
          status: 'pago',
        },
      ]

      exportVendasToPDF(vendas)

      expect(mockDoc.text).toHaveBeenCalledWith('Relatório de Vendas', 14, 20)
      expect(mockSave).toHaveBeenCalledWith('vendas.pdf')
    })

    it('should handle vendas without cliente', () => {
      const mockSave = jest.fn()
      const mockDoc = {
        text: jest.fn(),
        setFontSize: jest.fn(),
        save: mockSave,
      }
      ;(jsPDF as jest.MockedClass<typeof jsPDF>).mockImplementation(() => mockDoc as any)

      const vendas = [
        {
          id: 1,
          created_at: '2025-11-22T10:00:00',
          total: 1000,
          status: 'pago',
        },
      ]

      exportVendasToPDF(vendas as any)

      expect(mockSave).toHaveBeenCalledWith('vendas.pdf')
    })
  })

  describe('exportEstoqueToPDF', () => {
    it('should export estoque with correct structure', () => {
      const mockSave = jest.fn()
      const mockDoc = {
        text: jest.fn(),
        setFontSize: jest.fn(),
        save: mockSave,
      }
      ;(jsPDF as jest.MockedClass<typeof jsPDF>).mockImplementation(() => mockDoc as any)

      const movimentacoes = [
        {
          id: 1,
          created_at: '2025-11-22T10:00:00',
          produto: { descricao: 'Produto 1' },
          tipo: 'entrada',
          quantidade: 100,
          observacao: 'Test',
        },
      ]

      exportEstoqueToPDF(movimentacoes)

      expect(mockDoc.text).toHaveBeenCalledWith('Relatório de Estoque', 14, 20)
      expect(mockSave).toHaveBeenCalledWith('estoque.pdf')
    })
  })

  describe('exportFinanceiroToPDF', () => {
    it('should export financeiro with correct structure', () => {
      const mockSave = jest.fn()
      const mockDoc = {
        text: jest.fn(),
        setFontSize: jest.fn(),
        save: mockSave,
      }
      ;(jsPDF as jest.MockedClass<typeof jsPDF>).mockImplementation(() => mockDoc as any)

      const contas = [
        {
          id: 1,
          descricao: 'Conta 1',
          valor: 500,
          vencimento: '2025-11-30',
          status: 'pendente',
        },
      ]

      exportFinanceiroToPDF(contas)

      expect(mockDoc.text).toHaveBeenCalledWith('Relatório Financeiro', 14, 20)
      expect(mockSave).toHaveBeenCalledWith('financeiro.pdf')
    })

    it('should handle empty financeiro array', () => {
      const mockSave = jest.fn()
      const mockDoc = {
        text: jest.fn(),
        setFontSize: jest.fn(),
        save: mockSave,
      }
      ;(jsPDF as jest.MockedClass<typeof jsPDF>).mockImplementation(() => mockDoc as any)

      exportFinanceiroToPDF([])

      expect(mockSave).toHaveBeenCalledWith('financeiro.pdf')
    })
  })
})
