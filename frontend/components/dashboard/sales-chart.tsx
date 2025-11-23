'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

interface SalesChartProps {
  data: Array<{
    data: string
    vendas: number
    faturamento: number
  }>
  loading?: boolean
}

export function SalesChart({ data, loading = false }: SalesChartProps) {
  if (loading) {
    return (
      <Card className="col-span-4">
        <CardHeader>
          <CardTitle>Vendas e Faturamento</CardTitle>
          <CardDescription>Últimos 30 dias</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] w-full bg-muted animate-pulse rounded" />
        </CardContent>
      </Card>
    )
  }

  // Format data for display
  const formattedData = data.map((item) => ({
    ...item,
    dataFormatada: format(new Date(item.data), 'dd/MM', { locale: ptBR }),
  }))

  return (
    <Card className="col-span-4">
      <CardHeader>
        <CardTitle>Vendas e Faturamento</CardTitle>
        <CardDescription>
          Evolução diária nos últimos 30 dias
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={formattedData}>
            <defs>
              <linearGradient id="colorVendas" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="colorFaturamento" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8} />
                <stop offset="95%" stopColor="#82ca9d" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="dataFormatada"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}`}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="rounded-lg border bg-background p-2 shadow-sm">
                      <div className="grid grid-cols-2 gap-2">
                        <div className="flex flex-col">
                          <span className="text-[0.70rem] uppercase text-muted-foreground">
                            Vendas
                          </span>
                          <span className="font-bold text-muted-foreground">
                            {payload[0].value}
                          </span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-[0.70rem] uppercase text-muted-foreground">
                            Faturamento
                          </span>
                          <span className="font-bold">
                            R$ {Number(payload[1].value).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </span>
                        </div>
                      </div>
                    </div>
                  )
                }
                return null
              }}
            />
            <Legend />
            <Area
              type="monotone"
              dataKey="vendas"
              stroke="#8884d8"
              fillOpacity={1}
              fill="url(#colorVendas)"
              name="Vendas"
            />
            <Area
              type="monotone"
              dataKey="faturamento"
              stroke="#82ca9d"
              fillOpacity={1}
              fill="url(#colorFaturamento)"
              name="Faturamento (R$)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
