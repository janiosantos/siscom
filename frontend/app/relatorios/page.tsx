'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  BarChart,
  TrendingUp,
  Users,
  Package,
  DollarSign,
  FileText,
  Download,
  Printer,
  Calendar,
} from 'lucide-react'

export default function RelatoriosPage() {
  const [dataInicio, setDataInicio] = useState('')
  const [dataFim, setDataFim] = useState('')
  const [vendedor, setVendedor] = useState<string>('')
  const [cliente, setCliente] = useState<string>('')

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Relatórios</h1>
          <p className="text-muted-foreground">
            Análises e relatórios gerenciais
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Exportar
          </Button>
          <Button variant="outline">
            <Printer className="mr-2 h-4 w-4" />
            Imprimir
          </Button>
        </div>
      </div>

      {/* Filters Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Filtros
          </CardTitle>
          <CardDescription>
            Configure os filtros para gerar os relatórios
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label htmlFor="dataInicio">Data Início</Label>
              <Input
                id="dataInicio"
                type="date"
                value={dataInicio}
                onChange={(e) => setDataInicio(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dataFim">Data Fim</Label>
              <Input
                id="dataFim"
                type="date"
                value={dataFim}
                onChange={(e) => setDataFim(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="vendedor">Vendedor</Label>
              <Select value={vendedor} onValueChange={setVendedor}>
                <SelectTrigger id="vendedor">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="1">Maria Santos</SelectItem>
                  <SelectItem value="2">Pedro Costa</SelectItem>
                  <SelectItem value="3">Ana Paula</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="cliente">Cliente</Label>
              <Select value={cliente} onValueChange={setCliente}>
                <SelectTrigger id="cliente">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="1">João Silva Construções</SelectItem>
                  <SelectItem value="2">Reforma Total Ltda</SelectItem>
                  <SelectItem value="3">Construtora ABC</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="outline">Limpar Filtros</Button>
            <Button>Aplicar Filtros</Button>
          </div>
        </CardContent>
      </Card>

      {/* Report Types Tabs */}
      <Tabs defaultValue="vendas" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="vendas" className="flex items-center gap-2">
            <BarChart className="h-4 w-4" />
            <span className="hidden sm:inline">Vendas</span>
          </TabsTrigger>
          <TabsTrigger value="vendedores" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">Vendedores</span>
          </TabsTrigger>
          <TabsTrigger value="produtos" className="flex items-center gap-2">
            <Package className="h-4 w-4" />
            <span className="hidden sm:inline">Produtos</span>
          </TabsTrigger>
          <TabsTrigger value="clientes" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            <span className="hidden sm:inline">Clientes</span>
          </TabsTrigger>
          <TabsTrigger value="margem" className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            <span className="hidden sm:inline">Margem</span>
          </TabsTrigger>
        </TabsList>

        {/* Relatório de Vendas */}
        <TabsContent value="vendas" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Relatório de Vendas por Período</CardTitle>
              <CardDescription>
                Análise de vendas realizadas no período selecionado
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">
                        Total de Vendas
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">245</div>
                      <p className="text-xs text-muted-foreground">
                        +12% vs período anterior
                      </p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">
                        Faturamento
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">R$ 306.372,50</div>
                      <p className="text-xs text-muted-foreground">
                        +15,3% vs período anterior
                      </p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">
                        Ticket Médio
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">R$ 1.250,50</div>
                      <p className="text-xs text-muted-foreground">
                        +2,8% vs período anterior
                      </p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-medium">
                        Clientes Atendidos
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">87</div>
                      <p className="text-xs text-muted-foreground">
                        +8 novos clientes
                      </p>
                    </CardContent>
                  </Card>
                </div>

                {/* Detailed Table */}
                <div className="border rounded-lg p-4">
                  <h3 className="font-semibold mb-4">Detalhamento Diário</h3>
                  <div className="space-y-2">
                    {[...Array(10)].map((_, i) => (
                      <div
                        key={i}
                        className="flex justify-between items-center py-2 border-b last:border-0"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-24 text-sm text-muted-foreground">
                            {new Date(2025, 10, i + 1).toLocaleDateString('pt-BR')}
                          </div>
                          <div className="font-medium">
                            {Math.floor(Math.random() * 30 + 10)} vendas
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold">
                            R$ {(Math.random() * 15000 + 5000).toFixed(2)}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Ticket: R$ {(Math.random() * 500 + 500).toFixed(2)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Relatório de Vendedores */}
        <TabsContent value="vendedores" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Desempenho por Vendedor</CardTitle>
              <CardDescription>
                Análise de performance dos vendedores
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {['Maria Santos', 'Pedro Costa', 'Ana Paula', 'Carlos Lima'].map(
                  (nome, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <div className="h-12 w-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold">
                          {nome.charAt(0)}
                        </div>
                        <div>
                          <div className="font-semibold">{nome}</div>
                          <div className="text-sm text-muted-foreground">
                            {Math.floor(Math.random() * 50 + 20)} vendas
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-lg">
                          R$ {(Math.random() * 50000 + 10000).toFixed(2)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Ticket: R$ {(Math.random() * 1000 + 500).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  )
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Relatório de Produtos */}
        <TabsContent value="produtos" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Produtos Mais Vendidos</CardTitle>
              <CardDescription>
                Ranking de produtos por quantidade e faturamento
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[
                  { nome: 'Cimento CP-II 50kg', qtd: 450, valor: 14850 },
                  { nome: 'Areia Média m³', qtd: 380, valor: 34200 },
                  { nome: 'Tijolo Baiano', qtd: 12500, valor: 10000 },
                  { nome: 'Brita 1 m³', qtd: 320, valor: 25600 },
                  { nome: 'Cal Hidratada 20kg', qtd: 280, valor: 5600 },
                ].map((produto, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
                        {i + 1}
                      </div>
                      <div>
                        <div className="font-medium">{produto.nome}</div>
                        <div className="text-sm text-muted-foreground">
                          {produto.qtd.toLocaleString('pt-BR')} unidades
                        </div>
                      </div>
                    </div>
                    <div className="text-right font-bold">
                      R$ {produto.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Relatório de Clientes (Curva ABC) */}
        <TabsContent value="clientes" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Curva ABC de Clientes</CardTitle>
              <CardDescription>
                Classificação de clientes por faturamento
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Summary */}
                <div className="grid grid-cols-3 gap-4">
                  <Card className="border-green-200 bg-green-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Classe A (80%)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">15 clientes</div>
                      <div className="text-sm text-muted-foreground">
                        R$ 245.098,00
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="border-yellow-200 bg-yellow-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Classe B (15%)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">28 clientes</div>
                      <div className="text-sm text-muted-foreground">
                        R$ 45.955,88
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="border-red-200 bg-red-50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Classe C (5%)</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">44 clientes</div>
                      <div className="text-sm text-muted-foreground">
                        R$ 15.318,62
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Cliente List */}
                <div className="space-y-2">
                  {[
                    { nome: 'Construtora ABC', classe: 'A', valor: 85000 },
                    { nome: 'Reforma Total Ltda', classe: 'A', valor: 72000 },
                    { nome: 'João Silva Construções', classe: 'A', valor: 55000 },
                    { nome: 'Obras Master', classe: 'B', valor: 28000 },
                    { nome: 'Engenharia XYZ', classe: 'B', valor: 18000 },
                  ].map((cliente, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <Badge
                          className={
                            cliente.classe === 'A'
                              ? 'bg-green-500'
                              : cliente.classe === 'B'
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }
                        >
                          {cliente.classe}
                        </Badge>
                        <div className="font-medium">{cliente.nome}</div>
                      </div>
                      <div className="font-bold">
                        R$ {cliente.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Relatório de Margem */}
        <TabsContent value="margem" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Análise de Margem de Lucro</CardTitle>
              <CardDescription>
                Margem de lucro por categoria e produto
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Summary */}
                <div className="grid grid-cols-3 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Margem Média</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-green-600">42,5%</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Lucro Bruto</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">R$ 130.208,31</div>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Markup Médio</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">1,74x</div>
                    </CardContent>
                  </Card>
                </div>

                {/* Category Analysis */}
                <div className="space-y-2">
                  {[
                    { categoria: 'Cimentos', margem: 38.5, faturamento: 85000 },
                    { categoria: 'Areia e Pedra', margem: 45.2, faturamento: 72000 },
                    { categoria: 'Tijolos e Blocos', margem: 42.8, faturamento: 55000 },
                    { categoria: 'Ferragens', margem: 48.5, faturamento: 48000 },
                    { categoria: 'Cal e Argamassa', margem: 35.8, faturamento: 28000 },
                  ].map((cat, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div>
                        <div className="font-medium">{cat.categoria}</div>
                        <div className="text-sm text-muted-foreground">
                          Faturamento: R${' '}
                          {cat.faturamento.toLocaleString('pt-BR', {
                            minimumFractionDigits: 2,
                          })}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-green-600">
                          {cat.margem}%
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Lucro: R${' '}
                          {(cat.faturamento * (cat.margem / 100)).toLocaleString('pt-BR', {
                            minimumFractionDigits: 2,
                          })}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
