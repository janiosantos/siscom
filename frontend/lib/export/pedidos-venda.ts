import { exportToExcelFormatted, exportToExcelMultiSheet } from './excel'
import { exportToCSVFormatted } from './csv'

// Types
interface PedidoVenda {
  id: number
  numero_pedido: string
  cliente_nome: string
  vendedor_nome: string
  data_pedido: string
  data_entrega_prevista: string
  status: string
  tipo_entrega: string
  valor_total: number
  itens_count: number
}

interface PedidoVendaDetalhado extends PedidoVenda {
  itens: Array<{
    produto_nome: string
    quantidade: number
    preco_unitario: number
    desconto_item: number
    total: number
  }>
  desconto?: number
  valor_frete?: number
  outras_despesas?: number
  observacoes?: string
}

// Export lista de pedidos para Excel
export function exportPedidosToExcel(pedidos: PedidoVenda[], fileName?: string) {
  const headers = {
    numero_pedido: 'Número',
    cliente_nome: 'Cliente',
    vendedor_nome: 'Vendedor',
    data_pedido: 'Data Pedido',
    data_entrega_prevista: 'Entrega Prevista',
    status: 'Status',
    tipo_entrega: 'Tipo Entrega',
    itens_count: 'Qtd. Itens',
    valor_total: 'Valor Total',
  }

  exportToExcelFormatted(pedidos, headers, fileName ?? `pedidos_${new Date().toISOString().split('T')[0]}`, {
    sheetName: 'Pedidos de Venda',
    currencyFields: ['valor_total'],
    dateFields: ['data_pedido', 'data_entrega_prevista'],
    numberFields: ['itens_count'],
  })
}

// Export lista de pedidos para CSV
export function exportPedidosToCSV(pedidos: PedidoVenda[], fileName?: string) {
  const headers = {
    numero_pedido: 'Número',
    cliente_nome: 'Cliente',
    vendedor_nome: 'Vendedor',
    data_pedido: 'Data Pedido',
    data_entrega_prevista: 'Entrega Prevista',
    status: 'Status',
    tipo_entrega: 'Tipo Entrega',
    itens_count: 'Qtd. Itens',
    valor_total: 'Valor Total',
  }

  exportToCSVFormatted(pedidos, headers, fileName ?? `pedidos_${new Date().toISOString().split('T')[0]}`, {
    currencyFields: ['valor_total'],
    dateFields: ['data_pedido', 'data_entrega_prevista'],
    numberFields: ['itens_count'],
  })
}

// Export pedido detalhado com itens (Excel multi-sheet)
export function exportPedidoDetalhadoToExcel(pedido: PedidoVendaDetalhado, fileName?: string) {
  // Sheet 1: Cabeçalho
  const cabecalho = [
    {
      'Número': pedido.numero_pedido,
      'Cliente': pedido.cliente_nome,
      'Vendedor': pedido.vendedor_nome,
      'Data Pedido': new Date(pedido.data_pedido).toLocaleDateString('pt-BR'),
      'Entrega Prevista': new Date(pedido.data_entrega_prevista).toLocaleDateString('pt-BR'),
      'Status': pedido.status,
      'Tipo Entrega': pedido.tipo_entrega,
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

  const itensFormatados = pedido.itens.map((item) => ({
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
      'Valor': pedido.valor_total + (pedido.desconto ?? 0) - (pedido.valor_frete ?? 0) - (pedido.outras_despesas ?? 0),
    },
    {
      'Descrição': 'Desconto',
      'Valor': -(pedido.desconto ?? 0),
    },
    {
      'Descrição': 'Frete',
      'Valor': pedido.valor_frete ?? 0,
    },
    {
      'Descrição': 'Outras Despesas',
      'Valor': pedido.outras_despesas ?? 0,
    },
    {
      'Descrição': 'TOTAL',
      'Valor': pedido.valor_total,
    },
  ]

  exportToExcelMultiSheet(
    [
      { data: cabecalho, name: 'Cabeçalho' },
      { data: itensFormatados, name: 'Itens', headers: itensHeaders },
      { data: totalizadores, name: 'Totais' },
    ],
    fileName ?? `pedido_${pedido.numero_pedido}_${new Date().toISOString().split('T')[0]}`
  )
}

// Export pedidos agrupados por status
export function exportPedidosPorStatusToExcel(pedidos: PedidoVenda[], fileName?: string) {
  // Group by status
  const pedidosPorStatus: Record<string, PedidoVenda[]> = {}

  pedidos.forEach((pedido) => {
    if (!pedidosPorStatus[pedido.status]) {
      pedidosPorStatus[pedido.status] = []
    }
    pedidosPorStatus[pedido.status].push(pedido)
  })

  // Create sheets
  const sheets = Object.entries(pedidosPorStatus).map(([status, pedidosDoStatus]) => ({
    data: pedidosDoStatus.map((p) => ({
      'Número': p.numero_pedido,
      'Cliente': p.cliente_nome,
      'Vendedor': p.vendedor_nome,
      'Data Pedido': new Date(p.data_pedido).toLocaleDateString('pt-BR'),
      'Entrega Prevista': new Date(p.data_entrega_prevista).toLocaleDateString('pt-BR'),
      'Tipo Entrega': p.tipo_entrega,
      'Valor': p.valor_total.toLocaleString('pt-BR', {
        style: 'currency',
        currency: 'BRL',
      }),
    })),
    name: status.length > 31 ? status.substring(0, 31) : status, // Excel sheet name limit
  }))

  exportToExcelMultiSheet(
    sheets,
    fileName ?? `pedidos_por_status_${new Date().toISOString().split('T')[0]}`
  )
}
