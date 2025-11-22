import { apiClient } from "./client"
import {
  MovimentacaoEstoque,
  MovimentacaoEstoqueCreate,
  PaginatedResponse,
  Produto,
} from "@/types"

export const estoqueApi = {
  // Movimentações
  listMovimentacoes: async (params?: {
    page?: number
    page_size?: number
    produto_id?: number
    tipo?: string
    data_inicio?: string
    data_fim?: string
  }): Promise<PaginatedResponse<MovimentacaoEstoque>> => {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append("page", params.page.toString())
    if (params?.page_size)
      queryParams.append("page_size", params.page_size.toString())
    if (params?.produto_id)
      queryParams.append("produto_id", params.produto_id.toString())
    if (params?.tipo) queryParams.append("tipo", params.tipo)
    if (params?.data_inicio)
      queryParams.append("data_inicio", params.data_inicio)
    if (params?.data_fim) queryParams.append("data_fim", params.data_fim)

    const query = queryParams.toString()
    return apiClient.get<PaginatedResponse<MovimentacaoEstoque>>(
      `/estoque/movimentacoes${query ? `?${query}` : ""}`
    )
  },

  createMovimentacao: async (
    data: MovimentacaoEstoqueCreate
  ): Promise<MovimentacaoEstoque> => {
    return apiClient.post<MovimentacaoEstoque>(
      "/estoque/movimentacoes",
      data
    )
  },

  // Produtos com estoque baixo
  produtosBaixoEstoque: async (): Promise<Produto[]> => {
    return apiClient.get<Produto[]>("/estoque/alertas/baixo-estoque")
  },

  // Relatório de estoque
  relatorioEstoque: async (): Promise<any> => {
    return apiClient.get("/estoque/relatorio")
  },
}
