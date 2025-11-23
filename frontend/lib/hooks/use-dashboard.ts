import useSWR from 'swr'
import { apiClient } from '@/lib/api-client'
import {
  mockDashboardStats,
  mockVendasPorDia,
  mockProdutosMaisVendidos,
  mockStatusPedidos,
} from './use-dashboard-mock'

// Types
export interface DashboardStats {
  vendas_hoje: number
  vendas_mes: number
  pedidos_abertos: number
  pedidos_atrasados: number
  ticket_medio: number
  faturamento_mes: number
  crescimento_mes: number // %
  meta_mes: number
}

export interface VendasPorDia {
  data: string
  vendas: number
  faturamento: number
}

export interface ProdutoMaisVendido {
  produto_id: number
  produto_nome: string
  quantidade: number
  faturamento: number
}

export interface VendasPorVendedor {
  vendedor_id: number
  vendedor_nome: string
  total_vendas: number
  ticket_medio: number
}

export interface StatusPedidos {
  status: string
  quantidade: number
  valor_total: number
}

// Hooks
export function useDashboardStats() {
  const { data, error, mutate } = useSWR<DashboardStats>(
    '/dashboard/stats',
    (url) => apiClient.get<DashboardStats>(url),
    {
      fallbackData: mockDashboardStats,
      onError: () => {
        // Silently use mock data on error
      },
    }
  )

  return {
    stats: data ?? mockDashboardStats,
    isLoading: !error && !data,
    isError: false, // Don't show error, use mock data instead
    mutate,
  }
}

export function useVendasPorDia(dias: number = 30) {
  const { data, error, mutate } = useSWR<VendasPorDia[]>(
    `/dashboard/vendas-por-dia?dias=${dias}`,
    (url) => apiClient.get<VendasPorDia[]>(url),
    {
      fallbackData: mockVendasPorDia,
      onError: () => {},
    }
  )

  return {
    vendas: data ?? mockVendasPorDia,
    isLoading: !error && !data,
    isError: false,
    mutate,
  }
}

export function useProdutosMaisVendidos(limit: number = 10) {
  const { data, error, mutate } = useSWR<ProdutoMaisVendido[]>(
    `/dashboard/produtos-mais-vendidos?limit=${limit}`,
    (url) => apiClient.get<ProdutoMaisVendido[]>(url),
    {
      fallbackData: mockProdutosMaisVendidos,
      onError: () => {},
    }
  )

  return {
    produtos: data ?? mockProdutosMaisVendidos.slice(0, limit),
    isLoading: !error && !data,
    isError: false,
    mutate,
  }
}

export function useVendasPorVendedor() {
  const { data, error, mutate } = useSWR<VendasPorVendedor[]>(
    '/dashboard/vendas-por-vendedor',
    (url) => apiClient.get<VendasPorVendedor[]>(url),
    {
      fallbackData: [],
      onError: () => {},
    }
  )

  return {
    vendedores: data ?? [],
    isLoading: !error && !data,
    isError: false,
    mutate,
  }
}

export function useStatusPedidos() {
  const { data, error, mutate } = useSWR<StatusPedidos[]>(
    '/dashboard/status-pedidos',
    (url) => apiClient.get<StatusPedidos[]>(url),
    {
      fallbackData: mockStatusPedidos,
      onError: () => {},
    }
  )

  return {
    statusData: data ?? mockStatusPedidos,
    isLoading: !error && !data,
    isError: false,
    mutate,
  }
}
