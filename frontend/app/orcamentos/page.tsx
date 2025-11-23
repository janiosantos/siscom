'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Plus, FileText, Check, X, Clock, DollarSign } from 'lucide-react'

interface Orcamento {
  id: number
  numero_orcamento: string
  cliente_nome: string
  vendedor_nome: string
  data_orcamento: string
  data_validade: string
  status: 'ABERTO' | 'APROVADO' | 'CONVERTIDO' | 'PERDIDO'
  valor_total: number
  itens_count: number
}

export default function OrcamentosPage() {
  const [orcamentos, setOrcamentos] = useState<Orcamento[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    total: 0,
    abertos: 0,
    aprovados: 0,
    valorTotal: 0
  })

  useEffect(() => {
    fetchOrcamentos()
  }, [])

  const fetchOrcamentos = async () => {
    try {
      // TODO: Integrar com API real
      // const response = await fetch('/api/v1/orcamentos/')
      // const data = await response.json()

      // Mock data para demonstração
      const mockData: Orcamento[] = [
        {
          id: 1,
          numero_orcamento: 'ORC-001',
          cliente_nome: 'João Silva Construções',
          vendedor_nome: 'Maria Santos',
          data_orcamento: '2025-11-20',
          data_validade: '2025-11-27',
          status: 'ABERTO',
          valor_total: 15420.50,
          itens_count: 15
        },
        {
          id: 2,
          numero_orcamento: 'ORC-002',
          cliente_nome: 'Reforma Total Ltda',
          vendedor_nome: 'Pedro Costa',
          data_orcamento: '2025-11-21',
          data_validade: '2025-11-28',
          status: 'APROVADO',
          valor_total: 8350.00,
          itens_count: 8
        },
        {
          id: 3,
          numero_orcamento: 'ORC-003',
          cliente_nome: 'Construtora ABC',
          vendedor_nome: 'Ana Paula',
          data_orcamento: '2025-11-18',
          data_validade: '2025-11-25',
          status: 'CONVERTIDO',
          valor_total: 22100.00,
          itens_count: 25
        }
      ]

      setOrcamentos(mockData)

      // Calcular estatísticas
      setStats({
        total: mockData.length,
        abertos: mockData.filter(o => o.status === 'ABERTO').length,
        aprovados: mockData.filter(o => o.status === 'APROVADO').length,
        valorTotal: mockData.reduce((sum, o) => sum + o.valor_total, 0)
      })
    } catch (error) {
      console.error('Erro ao carregar orçamentos:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: any, icon: any }> = {
      ABERTO: { variant: 'default', icon: Clock },
      APROVADO: { variant: 'success', icon: Check },
      CONVERTIDO: { variant: 'secondary', icon: DollarSign },
      PERDIDO: { variant: 'destructive', icon: X }
    }

    const config = variants[status] || variants.ABERTO
    const Icon = config.icon

    return (
      <Badge variant={config.variant as any} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {status}
      </Badge>
    )
  }

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Carregando...</div>
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Orçamentos</h1>
          <p className="text-muted-foreground">Gerencie orçamentos e propostas</p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Novo Orçamento
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Orçamentos</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Abertos</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.abertos}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Aprovados</CardTitle>
            <Check className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.aprovados}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Valor Total</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              R$ {stats.valorTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Orçamentos</CardTitle>
          <CardDescription>Visualize e gerencie todos os orçamentos</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Número</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Vendedor</TableHead>
                <TableHead>Data</TableHead>
                <TableHead>Validade</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Valor</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orcamentos.map((orc) => (
                <TableRow key={orc.id}>
                  <TableCell className="font-medium">{orc.numero_orcamento}</TableCell>
                  <TableCell>{orc.cliente_nome}</TableCell>
                  <TableCell>{orc.vendedor_nome}</TableCell>
                  <TableCell>{new Date(orc.data_orcamento).toLocaleDateString('pt-BR')}</TableCell>
                  <TableCell>{new Date(orc.data_validade).toLocaleDateString('pt-BR')}</TableCell>
                  <TableCell>{getStatusBadge(orc.status)}</TableCell>
                  <TableCell className="text-right font-bold">
                    R$ {orc.valor_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm">
                      <FileText className="h-4 w-4 mr-2" />
                      Ver
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
