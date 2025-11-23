/**
 * Hook customizado para Pedidos de Venda
 */
import useSWR from 'swr'
import { apiClient, buildQueryParams } from '../api-client'

export type StatusPedido =
  | 'RASCUNHO'
  | 'CONFIRMADO'
  | 'EM_SEPARACAO'
  | 'SEPARADO'
  | 'EM_ENTREGA'
  | 'ENTREGUE'
  | 'FATURADO'
  | 'CANCELADO'

export interface PedidoVenda {
  id: number
  numero_pedido: string
  orcamento_id?: number
  cliente_id: number
  cliente_nome: string
  vendedor_id: number
  vendedor_nome: string
  data_pedido: string
  data_entrega_prevista: string
  data_entrega_real?: string
  tipo_entrega: 'RETIRADA' | 'ENTREGA' | 'TRANSPORTADORA'
  endereco_entrega?: string
  subtotal: number
  desconto: number
  valor_frete: number
  outras_despesas: number
  valor_total: number
  status: StatusPedido
  condicao_pagamento_id?: number
  forma_pagamento?: string
  observacoes?: string
  observacoes_internas?: string
  venda_id?: number
  usuario_separacao_id?: number
  data_separacao?: string
  itens: ItemPedidoVenda[]
  created_at: string
  updated_at: string
}

export interface ItemPedidoVenda {
  id: number
  produto_id: number
  produto_codigo: string
  produto_descricao: string
  quantidade: number
  quantidade_separada: number
  preco_unitario: number
  desconto_item: number
  total_item: number
  observacao_item?: string
}

export interface PedidoVendaCreate {
  cliente_id: number
  orcamento_id?: number
  data_entrega_prevista: string
  tipo_entrega: 'RETIRADA' | 'ENTREGA' | 'TRANSPORTADORA'
  endereco_entrega?: string
  desconto: number
  valor_frete: number
  outras_despesas: number
  condicao_pagamento_id?: number
  forma_pagamento?: string
  observacoes?: string
  itens: {
    produto_id: number
    quantidade: number
    preco_unitario: number
    desconto_item: number
    observacao_item?: string
  }[]
}

export interface PedidoFilters {
  cliente_id?: number
  vendedor_id?: number
  status?: StatusPedido
  data_inicio?: string
  data_fim?: string
  skip?: number
  limit?: number
}

// Hook para listar pedidos
export function usePedidosVenda(filters?: PedidoFilters) {
  const queryParams = filters ? buildQueryParams(filters) : ''
  const { data, error, mutate } = useSWR(
    `/pedidos-venda/${queryParams}`,
    (url) => apiClient.get<PedidoVenda[]>(url)
  )

  return {
    pedidos: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  }
}

// Hook para obter um pedido específico
export function usePedidoVenda(id: number | null) {
  const { data, error, mutate } = useSWR(
    id ? `/pedidos-venda/${id}` : null,
    (url) => apiClient.get<PedidoVenda>(url)
  )

  return {
    pedido: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  }
}

// Hook para pedidos atrasados
export function usePedidosAtrasados() {
  const { data, error, mutate } = useSWR(
    '/pedidos-venda/relatorios/atrasados',
    (url) => apiClient.get<PedidoVenda[]>(url)
  )

  return {
    pedidosAtrasados: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  }
}

// Hook para estatísticas
export function useEstatisticasPedidos(
  dataInicio?: string,
  dataFim?: string
) {
  const queryParams = buildQueryParams({
    data_inicio: dataInicio,
    data_fim: dataFim,
  })

  const { data, error } = useSWR(
    `/pedidos-venda/relatorios/estatisticas${queryParams}`,
    (url) =>
      apiClient.get<{
        total_pedidos: number
        total_valor: number
        pedidos_por_status: Record<StatusPedido, number>
        pedidos_atrasados: number
        ticket_medio: number
      }>(url)
  )

  return {
    estatisticas: data,
    isLoading: !error && !data,
    isError: error,
  }
}

// Funções de mutação
export async function criarPedidoVenda(
  data: PedidoVendaCreate
): Promise<PedidoVenda> {
  return apiClient.post<PedidoVenda>('/pedidos-venda/', data)
}

export async function atualizarPedidoVenda(
  id: number,
  data: Partial<PedidoVendaCreate>
): Promise<PedidoVenda> {
  return apiClient.put<PedidoVenda>(`/pedidos-venda/${id}`, data)
}

export async function confirmarPedido(
  id: number,
  observacao?: string
): Promise<PedidoVenda> {
  return apiClient.post<PedidoVenda>(`/pedidos-venda/${id}/confirmar`, {
    observacao,
  })
}

export async function iniciarSeparacao(id: number): Promise<PedidoVenda> {
  return apiClient.post<PedidoVenda>(`/pedidos-venda/${id}/iniciar-separacao`)
}

export async function separarPedido(
  id: number,
  itensSeparados: { produto_id: number; quantidade_separada: number }[]
): Promise<PedidoVenda> {
  return apiClient.post<PedidoVenda>(`/pedidos-venda/${id}/separar`, {
    itens_separados: itensSeparados,
  })
}

export async function enviarParaEntrega(id: number): Promise<PedidoVenda> {
  return apiClient.post<PedidoVenda>(`/pedidos-venda/${id}/enviar-entrega`)
}

export async function confirmarEntrega(id: number): Promise<PedidoVenda> {
  return apiClient.post<PedidoVenda>(`/pedidos-venda/${id}/confirmar-entrega`)
}

export async function faturarPedido(
  id: number,
  gerarNfe: boolean = false,
  observacao?: string
): Promise<{ pedido: PedidoVenda; venda: any }> {
  return apiClient.post<any>(`/pedidos-venda/${id}/faturar`, {
    gerar_nfe: gerarNfe,
    observacao,
  })
}

export async function cancelarPedido(
  id: number,
  motivo: string
): Promise<PedidoVenda> {
  return apiClient.post<PedidoVenda>(`/pedidos-venda/${id}/cancelar`, {
    motivo,
  })
}
