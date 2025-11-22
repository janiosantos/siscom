import { apiClient } from "./client"
import {
  ContaPagar,
  ContaReceber,
  ContaPagarCreate,
  ContaReceberCreate,
  PaginatedResponse,
} from "@/types"

export const financeiroApi = {
  // Contas a Pagar
  listContasPagar: async (params?: {
    page?: number
    page_size?: number
    status?: string
    data_inicio?: string
    data_fim?: string
  }): Promise<PaginatedResponse<ContaPagar>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append("page", params.page.toString())
    if (params?.page_size)
      queryParams.append("page_size", params.page_size.toString())
    if (params?.status) queryParams.append("status", params.status)
    if (params?.data_inicio)
      queryParams.append("data_inicio", params.data_inicio)
    if (params?.data_fim) queryParams.append("data_fim", params.data_fim)

    const query = queryParams.toString()
    return apiClient.get<PaginatedResponse<ContaPagar>>(
      `/financeiro/contas-pagar${query ? `?${query}` : ""}`
    )
  },

  createContaPagar: async (data: ContaPagarCreate): Promise<ContaPagar> => {
    return apiClient.post<ContaPagar>("/financeiro/contas-pagar", data)
  },

  pagarConta: async (id: number): Promise<ContaPagar> => {
    return apiClient.post<ContaPagar>(
      `/financeiro/contas-pagar/${id}/pagar`,
      {}
    )
  },

  // Contas a Receber
  listContasReceber: async (params?: {
    page?: number
    page_size?: number
    status?: string
    data_inicio?: string
    data_fim?: string
  }): Promise<PaginatedResponse<ContaReceber>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append("page", params.page.toString())
    if (params?.page_size)
      queryParams.append("page_size", params.page_size.toString())
    if (params?.status) queryParams.append("status", params.status)
    if (params?.data_inicio)
      queryParams.append("data_inicio", params.data_inicio)
    if (params?.data_fim) queryParams.append("data_fim", params.data_fim)

    const query = queryParams.toString()
    return apiClient.get<PaginatedResponse<ContaReceber>>(
      `/financeiro/contas-receber${query ? `?${query}` : ""}`
    )
  },

  createContaReceber: async (
    data: ContaReceberCreate
  ): Promise<ContaReceber> => {
    return apiClient.post<ContaReceber>("/financeiro/contas-receber", data)
  },

  receberConta: async (id: number): Promise<ContaReceber> => {
    return apiClient.post<ContaReceber>(
      `/financeiro/contas-receber/${id}/receber`,
      {}
    )
  },

  // Dashboard
  dashboard: async (): Promise<any> => {
    return apiClient.get("/financeiro/dashboard")
  },
}
