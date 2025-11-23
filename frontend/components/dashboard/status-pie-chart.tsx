'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface StatusPieChartProps {
  data: Array<{
    status: string
    quantidade: number
    valor_total: number
  }>
  loading?: boolean
}

const COLORS = {
  RASCUNHO: '#9ca3af',
  CONFIRMADO: '#3b82f6',
  EM_SEPARACAO: '#f59e0b',
  SEPARADO: '#06b6d4',
  EM_ENTREGA: '#8b5cf6',
  ENTREGUE: '#10b981',
  FATURADO: '#059669',
  CANCELADO: '#ef4444',
}

const STATUS_LABELS: Record<string, string> = {
  RASCUNHO: 'Rascunho',
  CONFIRMADO: 'Confirmado',
  EM_SEPARACAO: 'Em Separação',
  SEPARADO: 'Separado',
  EM_ENTREGA: 'Em Entrega',
  ENTREGUE: 'Entregue',
  FATURADO: 'Faturado',
  CANCELADO: 'Cancelado',
}

export function StatusPieChart({ data, loading = false }: StatusPieChartProps) {
  if (loading) {
    return (
      <Card className="col-span-3">
        <CardHeader>
          <CardTitle>Status dos Pedidos</CardTitle>
          <CardDescription>Distribuição atual</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] w-full bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    )
  }

  // Filter out zero quantities
  const filteredData = data.filter((item) => item.quantidade > 0)

  // Format data for chart
  const chartData = filteredData.map((item) => ({
    name: STATUS_LABELS[item.status] || item.status,
    value: item.quantidade,
    status: item.status,
  }))

  const total = filteredData.reduce((sum, item) => sum + item.quantidade, 0)

  return (
    <Card className="col-span-3">
      <CardHeader>
        <CardTitle>Status dos Pedidos</CardTitle>
        <CardDescription>
          {total} pedidos em andamento
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) =>
                `${name}: ${(percent * 100).toFixed(0)}%`
              }
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[entry.status as keyof typeof COLORS] || '#9ca3af'}
                />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload
                  return (
                    <div className="rounded-lg border bg-background p-2 shadow-sm">
                      <div className="grid gap-2">
                        <div className="flex flex-col">
                          <span className="text-[0.70rem] uppercase text-muted-foreground">
                            {data.name}
                          </span>
                          <span className="font-bold text-muted-foreground">
                            {data.value} pedidos
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                }
                return null
              }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
