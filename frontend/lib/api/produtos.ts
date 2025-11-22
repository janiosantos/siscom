import { apiClient } from "./client"
import { Produto, ProdutoCreate, ProdutoUpdate, PaginatedResponse } from "@/types"

export const produtosApi = {
  list: async (params?: {
    page?: number
    page_size?: number
    categoria_id?: number
    search?: string
  }): Promise<PaginatedResponse<Produto>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append("page", params.page.toString())
    if (params?.page_size) queryParams.append("page_size", params.page_size.toString())
    if (params?.categoria_id) queryParams.append("categoria_id", params.categoria_id.toString())
    if (params?.search) queryParams.append("search", params.search)

    return apiClient.get<PaginatedResponse<Produto>>(
      `/produtos?${queryParams.toString()}`
    )
  },

  get: async (id: number): Promise<Produto> => {
    return apiClient.get<Produto>(`/produtos/${id}`)
  },

  create: async (data: ProdutoCreate): Promise<Produto> => {
    return apiClient.post<Produto>("/produtos", data)
  },

  update: async (id: number, data: ProdutoUpdate): Promise<Produto> => {
    return apiClient.put<Produto>(`/produtos/${id}`, data)
  },

  delete: async (id: number): Promise<void> => {
    return apiClient.delete(`/produtos/${id}`)
  },
}
