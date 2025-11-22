import { apiClient } from "./client"
import { Cliente, ClienteCreate, ClienteUpdate, PaginatedResponse } from "@/types"

export const clientesApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    search?: string
    tipo?: "PF" | "PJ"
  }): Promise<PaginatedResponse<Cliente>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append("page", params.page.toString())
    if (params?.page_size)
      queryParams.append("page_size", params.page_size.toString())
    if (params?.search) queryParams.append("search", params.search)
    if (params?.tipo) queryParams.append("tipo", params.tipo)

    const query = queryParams.toString()
    return apiClient.get<PaginatedResponse<Cliente>>(
      `/clientes${query ? `?${query}` : ""}`
    )
  },

  listAll: async (): Promise<Cliente[]> => {
    const response = await apiClient.get<PaginatedResponse<Cliente>>(
      "/clientes?page_size=1000"
    )
    return response.items
  },

  get: async (id: number): Promise<Cliente> => {
    return apiClient.get<Cliente>(`/clientes/${id}`)
  },

  create: async (data: ClienteCreate): Promise<Cliente> => {
    return apiClient.post<Cliente>("/clientes", data)
  },

  update: async (id: number, data: ClienteUpdate): Promise<Cliente> => {
    return apiClient.put<Cliente>(`/clientes/${id}`, data)
  },

  delete: async (id: number): Promise<void> => {
    return apiClient.delete(`/clientes/${id}`)
  },
}
