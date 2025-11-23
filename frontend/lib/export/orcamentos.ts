import { exportToExcelFormatted, exportToExcelMultiSheet } from './excel'
import { exportToCSVFormatted } from './csv'

// Types
interface Orcamento {
  id: number
  numero_orcamento: string
  cliente_nome: string
  vendedor_nome: string
  data_orcamento: string
  data_validade: string
  status: string
  valor_total: number
  itens_count: number
  desconto?: number
  outras_despesas?: number
  observacoes?: string
}

interface OrcamentoDetalhado extends Orcamento {
  itens: Array<{
    produto_nome: string
    quantidade: number
    preco_unitario: number
    desconto_item: number
    total: number
  }>
}

// Export lista de orçamentos para Excel
export function exportOrcamentosToExcel(orcamentos: Orcamento[], fileName?: string) {
  const headers = {
    numero_orcamento: 'Número',
    cliente_nome: 'Cliente',
    vendedor_nome: 'Vendedor',
    data_orcamento: 'Data Orçamento',
    data_validade: 'Validade',
    status: 'Status',
    itens_count: 'Qtd. Itens',
    valor_total: 'Valor Total',
  }

  exportToExcelFormatted(orcamentos, headers, fileName ?? `orcamentos_${new Date().toISOString().split('T')[0]}`, {
    sheetName: 'Orçamentos',
    currencyFields: ['valor_total'],
    dateFields: ['data_orcamento', 'data_validade'],
    numberFields: ['itens_count'],
  })
}

// Export lista de orçamentos para CSV
export function exportOrcamentosToCSV(orcamentos: Orcamento[], fileName?: string) {
  const headers = {
    numero_orcamento: 'Número',
    cliente_nome: 'Cliente',
    vendedor_nome: 'Vendedor',
    data_orcamento: 'Data Orçamento',
    data_validade: 'Validade',
    status: 'Status',
    itens_count: 'Qtd. Itens',
    valor_total: 'Valor Total',
  }

  exportToCSVFormatted(orcamentos, headers, fileName ?? `orcamentos_${new Date().toISOString().split('T')[0]}`, {
    currencyFields: ['valor_total'],
    dateFields: ['data_orcamento', 'data_validade'],
    numberFields: ['itens_count'],
  })
}

// Export orçamento detalhado com itens (Excel multi-sheet)
export function exportOrcamentoDetalhadoToExcel(orcamento: OrcamentoDetalhado, fileName?: string) {
  // Sheet 1: Cabeçalho
  const cabecalho = [
    {
      'Número': orcamento.numero_orcamento,
      'Cliente': orcamento.cliente_nome,
      'Vendedor': orcamento.vendedor_nome,
      'Data Orçamento': new Date(orcamento.data_orcamento).toLocaleDateString('pt-BR'),
      'Data Validade': new Date(orcamento.data_validade).toLocaleDateString('pt-BR'),
      'Status': orcamento.status,
    },
  ]

  // Sheet 2: Itens
  const itensHeaders = {
    produto_nome: 'Produto',
    quantidade: 'Quantidade',
    preco_unitario: 'Preço Unit.',
    desconto_item: 'Desconto',
    total: 'Total',
  }

  const itensFormatados = orcamento.itens.map((item) => ({
    produto_nome: item.produto_nome,
    quantidade: item.quantidade,
    preco_unitario: item.preco_unitario,
    desconto_item: item.desconto_item,
    total: item.total,
  }))

  // Sheet 3: Totalizadores
  const totalizadores = [
    {
      'Descrição': 'Subtotal',
      'Valor': orcamento.valor_total + (orcamento.desconto ?? 0) - (orcamento.outras_despesas ?? 0),
    },
    {
      'Descrição': 'Desconto',
      'Valor': -(orcamento.desconto ?? 0),
    },
    {
      'Descrição': 'Outras Despesas',
      'Valor': orcamento.outras_despesas ?? 0,
    },
    {
      'Descrição': 'TOTAL',
      'Valor': orcamento.valor_total,
    },
  ]

  exportToExcelMultiSheet(
    [
      { data: cabecalho, name: 'Cabeçalho' },
      { data: itensFormatados, name: 'Itens', headers: itensHeaders },
      { data: totalizadores, name: 'Totais' },
    ],
    fileName ?? `orcamento_${orcamento.numero_orcamento}_${new Date().toISOString().split('T')[0]}`
  )
}
