import { apiClient } from "./client"
import { Venda, VendaCreate, VendaUpdate, PaginatedResponse } from "@/types"

export const vendasApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    cliente_id?: number
    status?: string
    data_inicio?: string
    data_fim?: string
  }): Promise<PaginatedResponse<Venda>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append("page", params.page.toString())
    if (params?.page_size)
      queryParams.append("page_size", params.page_size.toString())
    if (params?.cliente_id)
      queryParams.append("cliente_id", params.cliente_id.toString())
    if (params?.status) queryParams.append("status", params.status)
    if (params?.data_inicio)
      queryParams.append("data_inicio", params.data_inicio)
    if (params?.data_fim) queryParams.append("data_fim", params.data_fim)

    const query = queryParams.toString()
    return apiClient.get<PaginatedResponse<Venda>>(
      `/vendas${query ? `?${query}` : ""}`
    )
  },

  get: async (id: number): Promise<Venda> => {
    return apiClient.get<Venda>(`/vendas/${id}`)
  },

  create: async (data: VendaCreate): Promise<Venda> => {
    return apiClient.post<Venda>("/vendas", data)
  },

  update: async (id: number, data: VendaUpdate): Promise<Venda> => {
    return apiClient.put<Venda>(`/vendas/${id}`, data)
  },

  cancel: async (id: number): Promise<Venda> => {
    return apiClient.post<Venda>(`/vendas/${id}/cancelar`, {})
  },

  finalize: async (id: number): Promise<Venda> => {
    return apiClient.post<Venda>(`/vendas/${id}/finalizar`, {})
  },

  delete: async (id: number): Promise<void> => {
    return apiClient.delete(`/vendas/${id}`)
  },
}
