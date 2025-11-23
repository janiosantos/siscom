// Mock data for dashboard when API is not available
import {
  DashboardStats,
  VendasPorDia,
  ProdutoMaisVendido,
  StatusPedidos,
} from './use-dashboard'

export const mockDashboardStats: DashboardStats = {
  vendas_hoje: 12,
  vendas_mes: 245,
  pedidos_abertos: 18,
  pedidos_atrasados: 3,
  ticket_medio: 1250.50,
  faturamento_mes: 306372.50,
  crescimento_mes: 15.3,
  meta_mes: 350000.00,
}

export const mockVendasPorDia: VendasPorDia[] = Array.from({ length: 30 }, (_, i) => {
  const date = new Date()
  date.setDate(date.getDate() - (29 - i))

  return {
    data: date.toISOString().split('T')[0],
    vendas: Math.floor(Math.random() * 15 + 5),
    faturamento: Math.random() * 15000 + 5000,
  }
})

export const mockProdutosMaisVendidos: ProdutoMaisVendido[] = [
  { produto_id: 1, produto_nome: 'Cimento CP-II 50kg', quantidade: 450, faturamento: 14850.00 },
  { produto_id: 2, produto_nome: 'Areia Média m³', quantidade: 380, faturamento: 34200.00 },
  { produto_id: 3, produto_nome: 'Tijolo Baiano', quantidade: 12500, faturamento: 10000.00 },
  { produto_id: 4, produto_nome: 'Brita 1 m³', quantidade: 320, faturamento: 25600.00 },
  { produto_id: 5, produto_nome: 'Cal Hidratada 20kg', quantidade: 280, faturamento: 5600.00 },
  { produto_id: 6, produto_nome: 'Ferro 8mm 12m', quantidade: 250, faturamento: 18750.00 },
  { produto_id: 7, produto_nome: 'Telha Colonial', quantidade: 2200, faturamento: 13200.00 },
  { produto_id: 8, produto_nome: 'Argamassa AC-II 20kg', quantidade: 180, faturamento: 5040.00 },
  { produto_id: 9, produto_nome: 'Bloco de Concreto 14x19x39', quantidade: 3500, faturamento: 8750.00 },
  { produto_id: 10, produto_nome: 'Arame Recozido kg', quantidade: 150, faturamento: 1950.00 },
]

export const mockStatusPedidos: StatusPedidos[] = [
  { status: 'RASCUNHO', quantidade: 5, valor_total: 15000.00 },
  { status: 'CONFIRMADO', quantidade: 8, valor_total: 35000.00 },
  { status: 'EM_SEPARACAO', quantidade: 4, valor_total: 18000.00 },
  { status: 'SEPARADO', quantidade: 6, valor_total: 25000.00 },
  { status: 'EM_ENTREGA', quantidade: 3, valor_total: 12000.00 },
  { status: 'ENTREGUE', quantidade: 2, valor_total: 8000.00 },
  { status: 'FATURADO', quantidade: 225, valor_total: 650000.00 },
  { status: 'CANCELADO', quantidade: 5, valor_total: 8500.00 },
]
