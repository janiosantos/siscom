'use client'

import { TrendingUp, DollarSign, ShoppingCart, AlertCircle, Package, Users } from 'lucide-react'
import { StatsCard } from '@/components/dashboard/stats-card'
import { SalesChart } from '@/components/dashboard/sales-chart'
import { StatusPieChart } from '@/components/dashboard/status-pie-chart'
import { TopProductsChart } from '@/components/dashboard/top-products-chart'
import {
  useDashboardStats,
  useVendasPorDia,
  useStatusPedidos,
  useProdutosMaisVendidos,
} from '@/lib/hooks/use-dashboard'

export default function DashboardPage() {
  const { stats, isLoading: statsLoading } = useDashboardStats()
  const { vendas, isLoading: vendasLoading } = useVendasPorDia(30)
  const { statusData, isLoading: statusLoading } = useStatusPedidos()
  const { produtos, isLoading: produtosLoading } = useProdutosMaisVendidos(10)

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Visão geral do desempenho do seu negócio
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Vendas Hoje"
          value={stats?.vendas_hoje ?? 0}
          icon={ShoppingCart}
          description={`R$ ${(stats?.faturamento_mes ?? 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
          })}`}
          loading={statsLoading}
        />

        <StatsCard
          title="Faturamento do Mês"
          value={`R$ ${(stats?.faturamento_mes ?? 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
          })}`}
          icon={DollarSign}
          description={`Meta: R$ ${(stats?.meta_mes ?? 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
          })}`}
          trend={
            stats?.crescimento_mes
              ? {
                  value: stats.crescimento_mes,
                  isPositive: stats.crescimento_mes > 0,
                }
              : undefined
          }
          loading={statsLoading}
        />

        <StatsCard
          title="Ticket Médio"
          value={`R$ ${(stats?.ticket_medio ?? 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
          })}`}
          icon={TrendingUp}
          description="Valor médio por venda"
          loading={statsLoading}
        />

        <StatsCard
          title="Pedidos Abertos"
          value={stats?.pedidos_abertos ?? 0}
          icon={Package}
          description={
            stats?.pedidos_atrasados
              ? `${stats.pedidos_atrasados} atrasados`
              : 'Nenhum atrasado'
          }
          loading={statsLoading}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-7">
        {/* Sales Chart */}
        <SalesChart
          data={vendas ?? []}
          loading={vendasLoading}
        />

        {/* Status Pie Chart */}
        <StatusPieChart
          data={statusData ?? []}
          loading={statusLoading}
        />
      </div>

      {/* Top Products Chart */}
      <div className="grid gap-4 grid-cols-1">
        <TopProductsChart
          data={produtos ?? []}
          loading={produtosLoading}
        />
      </div>

      {/* Quick Actions / Recent Activity */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Recent Sales */}
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="flex flex-col space-y-1.5 p-6">
            <h3 className="text-2xl font-semibold leading-none tracking-tight">
              Vendas Recentes
            </h3>
            <p className="text-sm text-muted-foreground">
              Últimas 5 vendas realizadas
            </p>
          </div>
          <div className="p-6 pt-0">
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center">
                  <div className="ml-4 space-y-1">
                    <p className="text-sm font-medium leading-none">
                      Venda #{1000 + i}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Cliente Exemplo {i}
                    </p>
                  </div>
                  <div className="ml-auto font-medium">
                    R$ {(Math.random() * 1000 + 100).toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Sellers */}
        <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
          <div className="flex flex-col space-y-1.5 p-6">
            <h3 className="text-2xl font-semibold leading-none tracking-tight">
              Top Vendedores
            </h3>
            <p className="text-sm text-muted-foreground">
              Desempenho do mês atual
            </p>
          </div>
          <div className="p-6 pt-0">
            <div className="space-y-4">
              {['Maria Santos', 'Pedro Costa', 'Ana Paula', 'Carlos Lima'].map(
                (nome, i) => (
                  <div key={i} className="flex items-center">
                    <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      {nome.charAt(0)}
                    </div>
                    <div className="ml-4 space-y-1">
                      <p className="text-sm font-medium leading-none">{nome}</p>
                      <p className="text-sm text-muted-foreground">
                        {Math.floor(Math.random() * 50 + 20)} vendas
                      </p>
                    </div>
                    <div className="ml-auto font-medium">
                      R$ {(Math.random() * 50000 + 10000).toFixed(2)}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
