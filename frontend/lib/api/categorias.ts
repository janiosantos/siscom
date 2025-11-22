import { apiClient } from "./client"
import { Categoria, PaginatedResponse } from "@/types"

export const categoriasApi = {
  list: async (params?: {
    page?: number
    page_size?: number
  }): Promise<PaginatedResponse<Categoria>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append("page", params.page.toString())
    if (params?.page_size)
      queryParams.append("page_size", params.page_size.toString())

    const query = queryParams.toString()
    return apiClient.get<PaginatedResponse<Categoria>>(
      `/categorias${query ? `?${query}` : ""}`
    )
  },

  listAll: async (): Promise<Categoria[]> => {
    const response = await apiClient.get<PaginatedResponse<Categoria>>(
      "/categorias?page_size=1000"
    )
    return response.items
  },

  get: async (id: number): Promise<Categoria> => {
    return apiClient.get<Categoria>(`/categorias/${id}`)
  },

  create: async (data: Omit<Categoria, "id">): Promise<Categoria> => {
    return apiClient.post<Categoria>("/categorias", data)
  },

  update: async (
    id: number,
    data: Partial<Omit<Categoria, "id">>
  ): Promise<Categoria> => {
    return apiClient.put<Categoria>(`/categorias/${id}`, data)
  },

  delete: async (id: number): Promise<void> => {
    return apiClient.delete(`/categorias/${id}`)
  },
}
