"use client"

import {
  DollarSign,
  ShoppingCart,
  Package,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Download,
} from "lucide-react"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import { formatCurrency } from "@/lib/utils"

// Mock data - in real app, this would come from API
const salesData = [
  { month: "Jan", vendas: 45000, custo: 28000 },
  { month: "Fev", vendas: 52000, custo: 32000 },
  { month: "Mar", vendas: 48000, custo: 29000 },
  { month: "Abr", vendas: 61000, custo: 37000 },
  { month: "Mai", vendas: 55000, custo: 33000 },
  { month: "Jun", vendas: 67000, custo: 40000 },
]

const categoryData = [
  { name: "Cimento", value: 35, color: "#3b82f6" },
  { name: "Ferragens", value: 25, color: "#10b981" },
  { name: "Tintas", value: 20, color: "#f59e0b" },
  { name: "Elétrica", value: 15, color: "#ef4444" },
  { name: "Outros", value: 5, color: "#6b7280" },
]

const topProducts = [
  {
    id: 1,
    nome: "Cimento CP-II 50kg",
    vendas: 245,
    receita: 32450.0,
    trend: "up",
  },
  {
    id: 2,
    nome: "Barra de Ferro 10mm",
    vendas: 189,
    receita: 28350.0,
    trend: "up",
  },
  {
    id: 3,
    nome: "Tinta Acrílica 18L",
    vendas: 134,
    receita: 24120.0,
    trend: "down",
  },
  {
    id: 4,
    nome: "Areia Lavada m³",
    vendas: 98,
    receita: 19600.0,
    trend: "up",
  },
  {
    id: 5,
    nome: "Brita 1 m³",
    vendas: 87,
    receita: 17400.0,
    trend: "down",
  },
]

export default function DashboardPage() {
  const stats = {
    vendas_mes: 125840.5,
    pedidos_abertos: 23,
    produtos_baixo_estoque: 12,
    contas_vencer: 8,
    crescimento_vendas: 29.0,
    margem_lucro: 42.5,
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Visão geral do desempenho do negócio
          </p>
        </div>
        <Button>
          <Download className="mr-2 h-4 w-4" />
          Exportar Relatório
        </Button>
      </div>

      {/* KPIs */}
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
            <p className="text-xs text-green-600 flex items-center gap-1 mt-1">
              <TrendingUp className="h-3 w-3" />
              +{stats.crescimento_vendas}% em relação ao mês anterior
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
            <p className="text-xs text-muted-foreground mt-1">
              Aguardando finalização
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Estoque Baixo
            </CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {stats.produtos_baixo_estoque}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Produtos abaixo do mínimo
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Margem de Lucro
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {stats.margem_lucro}%
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Média do último trimestre
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Sales Chart */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Vendas vs Custos (Últimos 6 Meses)</CardTitle>
            <CardDescription>
              Comparativo de receitas e custos operacionais
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={salesData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value)}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="vendas"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Vendas"
                />
                <Line
                  type="monotone"
                  dataKey="custo"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Custos"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Category Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Vendas por Categoria</CardTitle>
            <CardDescription>Distribuição percentual</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name} (${value}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top Products */}
        <Card>
          <CardHeader>
            <CardTitle>Top 5 Produtos</CardTitle>
            <CardDescription>Mais vendidos do mês</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topProducts.map((product, index) => (
                <div
                  key={product.id}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-3 flex-1">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{product.nome}</p>
                      <p className="text-xs text-muted-foreground">
                        {product.vendas} unidades
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {formatCurrency(product.receita)}
                    </p>
                    {product.trend === "up" ? (
                      <TrendingUp className="h-3 w-3 text-green-600 ml-auto" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-red-600 ml-auto" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border-orange-200 bg-orange-50 dark:bg-orange-950/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800 dark:text-orange-400">
              <AlertTriangle className="h-5 w-5" />
              Alertas de Estoque
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              <li className="flex items-center justify-between text-sm">
                <span className="text-orange-700 dark:text-orange-300">
                  {stats.produtos_baixo_estoque} produtos com estoque abaixo do
                  mínimo
                </span>
                <Badge variant="warning">Urgente</Badge>
              </li>
              <li className="flex items-center justify-between text-sm">
                <span className="text-orange-700 dark:text-orange-300">
                  3 produtos sem movimentação há 30 dias
                </span>
                <Badge variant="default">Atenção</Badge>
              </li>
            </ul>
          </CardContent>
        </Card>

        <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-800 dark:text-blue-400">
              <DollarSign className="h-5 w-5" />
              Alertas Financeiros
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              <li className="flex items-center justify-between text-sm">
                <span className="text-blue-700 dark:text-blue-300">
                  {stats.contas_vencer} contas a vencer nos próximos 7 dias
                </span>
                <Badge variant="default">Pendente</Badge>
              </li>
              <li className="flex items-center justify-between text-sm">
                <span className="text-blue-700 dark:text-blue-300">
                  2 contas vencidas há mais de 15 dias
                </span>
                <Badge variant="destructive">Atrasado</Badge>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
