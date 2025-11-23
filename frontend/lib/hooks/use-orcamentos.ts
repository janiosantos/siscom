/**
 * Hook customizado para Orçamentos
 */
import useSWR from 'swr'
import { apiClient, buildQueryParams } from '../api-client'

export interface Orcamento {
  id: number
  numero_orcamento: string
  cliente_id: number
  cliente_nome: string
  vendedor_id: number
  vendedor_nome: string
  data_orcamento: string
  data_validade: string
  validade_dias: number
  status: 'ABERTO' | 'APROVADO' | 'CONVERTIDO' | 'PERDIDO'
  subtotal: number
  desconto: number
  valor_total: number
  observacoes?: string
  itens: ItemOrcamento[]
  created_at: string
  updated_at: string
}

export interface ItemOrcamento {
  id: number
  produto_id: number
  produto_codigo: string
  produto_descricao: string
  quantidade: number
  preco_unitario: number
  desconto_item: number
  total: number
}

export interface OrcamentoCreate {
  cliente_id: number
  validade_dias: number
  desconto: number
  observacoes?: string
  itens: {
    produto_id: number
    quantidade: number
    preco_unitario: number
    desconto_item: number
  }[]
}

export interface OrcamentoFilters {
  status?: string
  cliente_id?: number
  vendedor_id?: number
  data_inicio?: string
  data_fim?: string
}

// Hook para listar orçamentos
export function useOrcamentos(filters?: OrcamentoFilters) {
  const queryParams = filters ? buildQueryParams(filters) : ''
  const { data, error, mutate } = useSWR(
    `/orcamentos/${queryParams}`,
    (url) => apiClient.get<Orcamento[]>(url)
  )

  return {
    orcamentos: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  }
}

// Hook para obter um orçamento específico
export function useOrcamento(id: number | null) {
  const { data, error, mutate } = useSWR(
    id ? `/orcamentos/${id}` : null,
    (url) => apiClient.get<Orcamento>(url)
  )

  return {
    orcamento: data,
    isLoading: !error && !data,
    isError: error,
    mutate,
  }
}

// Funções de mutação (criar, atualizar, etc)
export async function criarOrcamento(data: OrcamentoCreate): Promise<Orcamento> {
  return apiClient.post<Orcamento>('/orcamentos/', data)
}

export async function atualizarOrcamento(
  id: number,
  data: Partial<OrcamentoCreate>
): Promise<Orcamento> {
  return apiClient.put<Orcamento>(`/orcamentos/${id}`, data)
}

export async function aprovarOrcamento(id: number): Promise<Orcamento> {
  return apiClient.post<Orcamento>(`/orcamentos/${id}/aprovar`)
}

export async function reprovarOrcamento(id: number): Promise<Orcamento> {
  return apiClient.post<Orcamento>(`/orcamentos/${id}/reprovar`)
}

export async function converterOrcamentoParaVenda(
  id: number,
  formaPagamento: string
): Promise<{ orcamento: Orcamento; venda: any }> {
  return apiClient.post<any>(`/orcamentos/${id}/converter-venda`, {
    forma_pagamento: formaPagamento,
  })
}

export async function deletarOrcamento(id: number): Promise<void> {
  return apiClient.delete(`/orcamentos/${id}`)
}
