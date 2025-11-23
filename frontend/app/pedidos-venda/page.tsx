'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
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
  Edit,
  Loader2
} from 'lucide-react'
import { usePedidosVenda, confirmarPedido, faturarPedido } from '@/lib/hooks/use-pedidos-venda'
import { PedidoVendaForm } from '@/components/forms/pedido-venda-form'
import { useToast } from '@/components/ui/use-toast'

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
  const { toast } = useToast()
  const [filtroStatus, setFiltroStatus] = useState<Status | 'TODOS'>('TODOS')
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedPedido, setSelectedPedido] = useState<PedidoVenda | null>(null)

  const { pedidos: allPedidos, isLoading, isError, mutate } = usePedidosVenda(
    filtroStatus !== 'TODOS' ? { status: filtroStatus } : undefined
  )

  const pedidos = allPedidos || []

  // Calcular estatísticas
  const stats = pedidos.length > 0 ? {
    total: pedidos.length,
    rascunho: pedidos.filter((p: PedidoVenda) => p.status === 'RASCUNHO').length,
    confirmado: pedidos.filter((p: PedidoVenda) => p.status === 'CONFIRMADO').length,
    emSeparacao: pedidos.filter((p: PedidoVenda) => p.status === 'EM_SEPARACAO').length,
    separado: pedidos.filter((p: PedidoVenda) => p.status === 'SEPARADO').length,
    emEntrega: pedidos.filter((p: PedidoVenda) => p.status === 'EM_ENTREGA').length,
    entregue: pedidos.filter((p: PedidoVenda) => p.status === 'ENTREGUE').length,
    faturado: pedidos.filter((p: PedidoVenda) => p.status === 'FATURADO').length,
    atrasados: pedidos.filter((p: PedidoVenda) => {
      const hoje = new Date()
      const entrega = new Date(p.data_entrega_prevista)
      return entrega < hoje && !['ENTREGUE', 'FATURADO', 'CANCELADO'].includes(p.status)
    }).length,
    valorTotal: pedidos.reduce((sum: number, p: PedidoVenda) => sum + p.valor_total, 0)
  } : {
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
  }

  const handleNovoPedido = () => {
    setSelectedPedido(null)
    setIsDialogOpen(true)
  }

  const handleEditarPedido = (pedido: PedidoVenda) => {
    setSelectedPedido(pedido)
    setIsDialogOpen(true)
  }

  const handleSuccess = () => {
    setIsDialogOpen(false)
    setSelectedPedido(null)
    mutate() // Revalidar dados
  }

  const handleAcao = async (pedidoId: number, acao: string) => {
    try {
      if (acao === 'confirmar') {
        await confirmarPedido(pedidoId)
        toast({
          title: 'Sucesso',
          description: 'Pedido confirmado com sucesso',
        })
      } else if (acao === 'faturar') {
        await faturarPedido(pedidoId)
        toast({
          title: 'Sucesso',
          description: 'Pedido faturado com sucesso',
        })
      }
      // Add other actions as needed
      mutate() // Revalidar dados
    } catch (error: any) {
      toast({
        title: 'Erro',
        description: error.message || 'Erro ao executar ação',
        variant: 'destructive',
      })
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Carregando pedidos...</span>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Erro ao carregar pedidos</h2>
          <p className="text-muted-foreground">Tente novamente mais tarde</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Dialog para Criar/Editar Pedido */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedPedido ? 'Editar Pedido de Venda' : 'Novo Pedido de Venda'}
            </DialogTitle>
            <DialogDescription>
              {selectedPedido
                ? `Editando pedido ${selectedPedido.numero_pedido}`
                : 'Preencha os dados abaixo para criar um novo pedido de venda'
              }
            </DialogDescription>
          </DialogHeader>
          <PedidoVendaForm
            pedidoId={selectedPedido?.id}
            initialData={selectedPedido || undefined}
            onSuccess={handleSuccess}
            onCancel={() => setIsDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Pedidos de Venda</h1>
          <p className="text-muted-foreground">Gerencie o ciclo completo de pedidos</p>
        </div>
        <Button className="flex items-center gap-2" onClick={handleNovoPedido}>
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
