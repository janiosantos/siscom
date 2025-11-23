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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Plus,
  FileText,
  Clock,
  CheckCircle,
  Package,
  Truck,
  DollarSign,
  XCircle,
  MoreVertical,
  Eye,
  Printer,
  Edit
} from 'lucide-react'

type Status = 'RASCUNHO' | 'CONFIRMADO' | 'EM_SEPARACAO' | 'SEPARADO' | 'EM_ENTREGA' | 'ENTREGUE' | 'FATURADO' | 'CANCELADO'

interface PedidoVenda {
  id: number
  numero_pedido: string
  cliente_nome: string
  vendedor_nome: string
  data_pedido: string
  data_entrega_prevista: string
  status: Status
  tipo_entrega: string
  valor_total: number
  itens_count: number
}

export default function PedidosVendaPage() {
  const [pedidos, setPedidos] = useState<PedidoVenda[]>([])
  const [loading, setLoading] = useState(true)
  const [filtroStatus, setFiltroStatus] = useState<Status | 'TODOS'>('TODOS')
  const [stats, setStats] = useState({
    total: 0,
    rascunho: 0,
    confirmado: 0,
    emSeparacao: 0,
    separado: 0,
    emEntrega: 0,
    entregue: 0,
    faturado: 0,
    atrasados: 0,
    valorTotal: 0
  })

  useEffect(() => {
    fetchPedidos()
  }, [filtroStatus])

  const fetchPedidos = async () => {
    try {
      // TODO: Integrar com API real
      // const response = await fetch('/api/v1/pedidos-venda/')
      // const data = await response.json()

      // Mock data
      const mockData: PedidoVenda[] = [
        {
          id: 1,
          numero_pedido: 'PV000001',
          cliente_nome: 'Construtora XYZ Ltda',
          vendedor_nome: 'Maria Santos',
          data_pedido: '2025-11-20',
          data_entrega_prevista: '2025-11-25',
          status: 'CONFIRMADO',
          tipo_entrega: 'ENTREGA',
          valor_total: 15420.50,
          itens_count: 25
        },
        {
          id: 2,
          numero_pedido: 'PV000002',
          cliente_nome: 'João Silva Materiais',
          vendedor_nome: 'Pedro Costa',
          data_pedido: '2025-11-21',
          data_entrega_prevista: '2025-11-26',
          status: 'EM_SEPARACAO',
          tipo_entrega: 'RETIRADA',
          valor_total: 8350.00,
          itens_count: 12
        },
        {
          id: 3,
          numero_pedido: 'PV000003',
          cliente_nome: 'Reforma Total S.A.',
          vendedor_nome: 'Ana Paula',
          data_pedido: '2025-11-19',
          data_entrega_prevista: '2025-11-24',
          status: 'SEPARADO',
          tipo_entrega: 'ENTREGA',
          valor_total: 22100.00,
          itens_count: 38
        },
        {
          id: 4,
          numero_pedido: 'PV000004',
          cliente_nome: 'ABC Construções',
          vendedor_nome: 'Carlos Lima',
          data_pedido: '2025-11-22',
          data_entrega_prevista: '2025-11-28',
          status: 'EM_ENTREGA',
          tipo_entrega: 'TRANSPORTADORA',
          valor_total: 31200.00,
          itens_count: 45
        },
        {
          id: 5,
          numero_pedido: 'PV000005',
          cliente_nome: 'Engenharia Master',
          vendedor_nome: 'Maria Santos',
          data_pedido: '2025-11-18',
          data_entrega_prevista: '2025-11-23',
          status: 'FATURADO',
          tipo_entrega: 'ENTREGA',
          valor_total: 18900.00,
          itens_count: 28
        },
        {
          id: 6,
          numero_pedido: 'PV000006',
          cliente_nome: 'Obras & Cia',
          vendedor_nome: 'Pedro Costa',
          data_pedido: '2025-11-23',
          data_entrega_prevista: '2025-11-30',
          status: 'RASCUNHO',
          tipo_entrega: 'ENTREGA',
          valor_total: 5600.00,
          itens_count: 8
        }
      ]

      const filtered = filtroStatus === 'TODOS'
        ? mockData
        : mockData.filter(p => p.status === filtroStatus)

      setPedidos(filtered)

      // Calcular estatísticas
      setStats({
        total: mockData.length,
        rascunho: mockData.filter(p => p.status === 'RASCUNHO').length,
        confirmado: mockData.filter(p => p.status === 'CONFIRMADO').length,
        emSeparacao: mockData.filter(p => p.status === 'EM_SEPARACAO').length,
        separado: mockData.filter(p => p.status === 'SEPARADO').length,
        emEntrega: mockData.filter(p => p.status === 'EM_ENTREGA').length,
        entregue: mockData.filter(p => p.status === 'ENTREGUE').length,
        faturado: mockData.filter(p => p.status === 'FATURADO').length,
        atrasados: mockData.filter(p => {
          const hoje = new Date()
          const entrega = new Date(p.data_entrega_prevista)
          return entrega < hoje && !['ENTREGUE', 'FATURADO', 'CANCELADO'].includes(p.status)
        }).length,
        valorTotal: mockData.reduce((sum, p) => sum + p.valor_total, 0)
      })
    } catch (error) {
      console.error('Erro ao carregar pedidos:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusConfig = (status: Status) => {
    const configs: Record<Status, { label: string; variant: any; icon: any; color: string }> = {
      RASCUNHO: { label: 'Rascunho', variant: 'outline', icon: Edit, color: 'text-gray-500' },
      CONFIRMADO: { label: 'Confirmado', variant: 'default', icon: CheckCircle, color: 'text-blue-500' },
      EM_SEPARACAO: { label: 'Em Separação', variant: 'secondary', icon: Package, color: 'text-orange-500' },
      SEPARADO: { label: 'Separado', variant: 'secondary', icon: CheckCircle, color: 'text-cyan-500' },
      EM_ENTREGA: { label: 'Em Entrega', variant: 'secondary', icon: Truck, color: 'text-purple-500' },
      ENTREGUE: { label: 'Entregue', variant: 'success', icon: CheckCircle, color: 'text-green-500' },
      FATURADO: { label: 'Faturado', variant: 'success', icon: DollarSign, color: 'text-green-600' },
      CANCELADO: { label: 'Cancelado', variant: 'destructive', icon: XCircle, color: 'text-red-500' }
    }
    return configs[status]
  }

  const getStatusBadge = (status: Status) => {
    const config = getStatusConfig(status)
    const Icon = config.icon

    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    )
  }

  const handleAcao = (pedidoId: number, acao: string) => {
    console.log(`Ação ${acao} no pedido ${pedidoId}`)
    // TODO: Implementar ações (confirmar, separar, faturar, etc)
  }

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Carregando...</div>
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Pedidos de Venda</h1>
          <p className="text-muted-foreground">Gerencie o ciclo completo de pedidos</p>
        </div>
        <Button className="flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Novo Pedido
        </Button>
      </div>

      {/* Filtros de Status */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <Button
          variant={filtroStatus === 'TODOS' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroStatus('TODOS')}
        >
          Todos ({stats.total})
        </Button>
        <Button
          variant={filtroStatus === 'RASCUNHO' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroStatus('RASCUNHO')}
        >
          Rascunho ({stats.rascunho})
        </Button>
        <Button
          variant={filtroStatus === 'CONFIRMADO' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroStatus('CONFIRMADO')}
        >
          Confirmado ({stats.confirmado})
        </Button>
        <Button
          variant={filtroStatus === 'EM_SEPARACAO' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroStatus('EM_SEPARACAO')}
        >
          Em Separação ({stats.emSeparacao})
        </Button>
        <Button
          variant={filtroStatus === 'SEPARADO' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroStatus('SEPARADO')}
        >
          Separado ({stats.separado})
        </Button>
        <Button
          variant={filtroStatus === 'EM_ENTREGA' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroStatus('EM_ENTREGA')}
        >
          Em Entrega ({stats.emEntrega})
        </Button>
        <Button
          variant={filtroStatus === 'FATURADO' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFiltroStatus('FATURADO')}
        >
          Faturado ({stats.faturado})
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Pedidos</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Todos os status</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Em Andamento</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.confirmado + stats.emSeparacao + stats.separado + stats.emEntrega}
            </div>
            <p className="text-xs text-muted-foreground">Aguardando conclusão</p>
          </CardContent>
        </Card>

        <Card className={stats.atrasados > 0 ? 'border-red-500' : ''}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Atrasados</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-500">{stats.atrasados}</div>
            <p className="text-xs text-muted-foreground">Entrega vencida</p>
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
            <p className="text-xs text-muted-foreground">Todos os pedidos</p>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Visual */}
      <Card>
        <CardHeader>
          <CardTitle>Pipeline de Pedidos</CardTitle>
          <CardDescription>Visualize o fluxo de pedidos por status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-8 gap-2">
            {(['RASCUNHO', 'CONFIRMADO', 'EM_SEPARACAO', 'SEPARADO', 'EM_ENTREGA', 'ENTREGUE', 'FATURADO', 'CANCELADO'] as Status[]).map((status) => {
              const config = getStatusConfig(status)
              const Icon = config.icon
              const count = stats[status.toLowerCase().replace('_', '') as keyof typeof stats] as number || 0

              return (
                <div key={status} className="text-center">
                  <div className={`p-4 rounded-lg border-2 ${count > 0 ? 'border-primary' : 'border-gray-200'}`}>
                    <Icon className={`h-6 w-6 mx-auto mb-2 ${config.color}`} />
                    <div className="text-2xl font-bold">{count}</div>
                    <div className="text-xs text-muted-foreground mt-1">{config.label}</div>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Tabela de Pedidos */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Pedidos</CardTitle>
          <CardDescription>
            {filtroStatus === 'TODOS' ? 'Todos os pedidos' : `Pedidos com status: ${filtroStatus}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Número</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Vendedor</TableHead>
                <TableHead>Data Pedido</TableHead>
                <TableHead>Entrega Prevista</TableHead>
                <TableHead>Tipo Entrega</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Valor</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pedidos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                    Nenhum pedido encontrado
                  </TableCell>
                </TableRow>
              ) : (
                pedidos.map((pedido) => (
                  <TableRow key={pedido.id}>
                    <TableCell className="font-medium">{pedido.numero_pedido}</TableCell>
                    <TableCell>{pedido.cliente_nome}</TableCell>
                    <TableCell>{pedido.vendedor_nome}</TableCell>
                    <TableCell>{new Date(pedido.data_pedido).toLocaleDateString('pt-BR')}</TableCell>
                    <TableCell>{new Date(pedido.data_entrega_prevista).toLocaleDateString('pt-BR')}</TableCell>
                    <TableCell>{pedido.tipo_entrega}</TableCell>
                    <TableCell>{getStatusBadge(pedido.status)}</TableCell>
                    <TableCell className="text-right font-bold">
                      R$ {pedido.valor_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuLabel>Ações</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem onClick={() => handleAcao(pedido.id, 'visualizar')}>
                            <Eye className="mr-2 h-4 w-4" />
                            Visualizar
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleAcao(pedido.id, 'imprimir')}>
                            <Printer className="mr-2 h-4 w-4" />
                            Imprimir
                          </DropdownMenuItem>
                          {pedido.status === 'RASCUNHO' && (
                            <DropdownMenuItem onClick={() => handleAcao(pedido.id, 'confirmar')}>
                              <CheckCircle className="mr-2 h-4 w-4" />
                              Confirmar
                            </DropdownMenuItem>
                          )}
                          {pedido.status === 'CONFIRMADO' && (
                            <DropdownMenuItem onClick={() => handleAcao(pedido.id, 'iniciar_separacao')}>
                              <Package className="mr-2 h-4 w-4" />
                              Iniciar Separação
                            </DropdownMenuItem>
                          )}
                          {pedido.status === 'EM_SEPARACAO' && (
                            <DropdownMenuItem onClick={() => handleAcao(pedido.id, 'separar')}>
                              <CheckCircle className="mr-2 h-4 w-4" />
                              Marcar Separado
                            </DropdownMenuItem>
                          )}
                          {pedido.status === 'SEPARADO' && (
                            <DropdownMenuItem onClick={() => handleAcao(pedido.id, 'enviar_entrega')}>
                              <Truck className="mr-2 h-4 w-4" />
                              Enviar para Entrega
                            </DropdownMenuItem>
                          )}
                          {pedido.status === 'ENTREGUE' && (
                            <DropdownMenuItem onClick={() => handleAcao(pedido.id, 'faturar')}>
                              <DollarSign className="mr-2 h-4 w-4" />
                              Faturar Pedido
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
