"use client"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  DollarSign,
  ShoppingCart,
  Package,
  TrendingUp,
  AlertTriangle,
} from "lucide-react"
import { formatCurrency } from "@/lib/utils"

export default function DashboardPage() {
  // Mock data - in real app, fetch from API
  const stats = {
    vendas_mes: 125840.50,
    vendas_mes_anterior: 98420.30,
    pedidos_abertos: 23,
    produtos_baixo_estoque: 12,
    contas_vencer: 8,
  }

  const crescimento = ((stats.vendas_mes - stats.vendas_mes_anterior) / stats.vendas_mes_anterior) * 100

  return (
    <div className="space-y-6">
      {/* Page title */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Visão geral do seu negócio
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Vendas do Mês
            </CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(stats.vendas_mes)}
            </div>
            <p className="text-xs text-muted-foreground">
              <span className="text-green-600">
                +{crescimento.toFixed(1)}%
              </span>{" "}
              em relação ao mês anterior
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Pedidos Abertos
            </CardTitle>
            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pedidos_abertos}</div>
            <p className="text-xs text-muted-foreground">
              Pendentes de finalização
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Produtos com Baixo Estoque
            </CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {stats.produtos_baixo_estoque}
            </div>
            <p className="text-xs text-muted-foreground">
              Abaixo do estoque mínimo
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Contas a Vencer
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {stats.contas_vencer}
            </div>
            <p className="text-xs text-muted-foreground">
              Próximos 7 dias
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      <Card className="border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-950">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-600" />
            Alertas
          </CardTitle>
          <CardDescription>Itens que precisam de atenção</CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            <li className="text-sm">
              • {stats.produtos_baixo_estoque} produtos com estoque abaixo do mínimo
            </li>
            <li className="text-sm">
              • {stats.contas_vencer} contas a vencer nos próximos 7 dias
            </li>
            <li className="text-sm">
              • {stats.pedidos_abertos} pedidos aguardando finalização
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Recent activity */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Vendas Recentes</CardTitle>
            <CardDescription>Últimas 5 vendas realizadas</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">Venda #{1000 + i}</p>
                    <p className="text-xs text-muted-foreground">
                      Cliente: João Silva
                    </p>
                  </div>
                  <div className="text-sm font-medium">
                    {formatCurrency(Math.random() * 1000 + 100)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Produtos Mais Vendidos</CardTitle>
            <CardDescription>Top 5 produtos do mês</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {["Cimento CP-II 50kg", "Areia Média 20kg", "Tijolo Comum", "Cal Hidratada", "Argamassa AC-II"].map((produto, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium">{produto}</p>
                    <p className="text-xs text-muted-foreground">
                      {Math.floor(Math.random() * 100) + 50} unidades
                    </p>
                  </div>
                  <div className="text-sm font-medium text-green-600">
                    {formatCurrency(Math.random() * 5000 + 1000)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
