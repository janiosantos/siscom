'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Calendar,
  User,
  DollarSign,
  Package,
  FileText,
  CheckCircle,
  Truck,
  MapPin,
  Clock,
  Printer,
  Download,
  Edit,
} from 'lucide-react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

type Status = 'RASCUNHO' | 'CONFIRMADO' | 'EM_SEPARACAO' | 'SEPARADO' | 'EM_ENTREGA' | 'ENTREGUE' | 'FATURADO' | 'CANCELADO'

interface PedidoVendaDetalhado {
  id: number
  numero_pedido: string
  cliente_id: number
  cliente_nome: string
  cliente_documento: string
  cliente_endereco?: string
  vendedor_id: number
  vendedor_nome: string
  data_pedido: string
  data_entrega_prevista: string
  data_entrega_real?: string
  status: Status
  tipo_entrega: 'RETIRADA' | 'ENTREGA' | 'TRANSPORTADORA'
  endereco_entrega?: string
  desconto: number
  valor_frete: number
  outras_despesas: number
  valor_total: number
  observacoes?: string
  forma_pagamento?: string
  itens: Array<{
    id: number
    produto_id: number
    produto_nome: string
    produto_codigo: string
    quantidade: number
    quantidade_separada?: number
    preco_unitario: number
    desconto_item: number
    observacao_item?: string
  }>
  historico?: Array<{
    id: number
    data: string
    status: Status
    usuario: string
    observacao?: string
  }>
}

interface PedidoVendaDetailProps {
  pedido: PedidoVendaDetalhado
  onClose?: () => void
  onEdit?: () => void
  onConfirmar?: () => void
  onIniciarSeparacao?: () => void
  onFinalizarSeparacao?: () => void
  onEnviarParaEntrega?: () => void
  onConfirmarEntrega?: () => void
  onFaturar?: () => void
  onCancelar?: () => void
}

export function PedidoVendaDetail({
  pedido,
  onClose,
  onEdit,
  onConfirmar,
  onIniciarSeparacao,
  onFinalizarSeparacao,
  onEnviarParaEntrega,
  onConfirmarEntrega,
  onFaturar,
  onCancelar,
}: PedidoVendaDetailProps) {
  const subtotal = pedido.itens.reduce(
    (sum, item) => sum + (item.quantidade * item.preco_unitario - item.desconto_item),
    0
  )

  const getStatusConfig = (status: Status) => {
    const configs = {
      RASCUNHO: { label: 'Rascunho', color: 'bg-gray-500' },
      CONFIRMADO: { label: 'Confirmado', color: 'bg-blue-500' },
      EM_SEPARACAO: { label: 'Em Separação', color: 'bg-orange-500' },
      SEPARADO: { label: 'Separado', color: 'bg-cyan-500' },
      EM_ENTREGA: { label: 'Em Entrega', color: 'bg-purple-500' },
      ENTREGUE: { label: 'Entregue', color: 'bg-green-500' },
      FATURADO: { label: 'Faturado', color: 'bg-green-600' },
      CANCELADO: { label: 'Cancelado', color: 'bg-red-500' },
    }
    return configs[status]
  }

  const statusFlow: Status[] = [
    'RASCUNHO',
    'CONFIRMADO',
    'EM_SEPARACAO',
    'SEPARADO',
    'EM_ENTREGA',
    'ENTREGUE',
    'FATURADO',
  ]

  const currentStatusIndex = statusFlow.indexOf(pedido.status)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold">{pedido.numero_pedido}</h2>
          <p className="text-muted-foreground mt-1">
            Criado em {format(new Date(pedido.data_pedido), "dd 'de' MMMM 'de' yyyy", { locale: ptBR })}
          </p>
        </div>
        <Badge className={`${getStatusConfig(pedido.status).color} text-white`}>
          {getStatusConfig(pedido.status).label}
        </Badge>
      </div>

      {/* Status Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Linha do Tempo</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <div className="flex justify-between items-center">
              {statusFlow.map((status, index) => {
                const config = getStatusConfig(status)
                const isActive = index <= currentStatusIndex
                const isCurrent = status === pedido.status

                return (
                  <div key={status} className="flex flex-col items-center flex-1">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isActive ? config.color : 'bg-gray-300'
                      } text-white relative z-10`}
                    >
                      {isCurrent && <CheckCircle className="h-5 w-5" />}
                      {!isCurrent && index < currentStatusIndex && <CheckCircle className="h-5 w-5" />}
                      {!isActive && <Clock className="h-5 w-5" />}
                    </div>
                    <div className="text-xs mt-2 text-center whitespace-nowrap">
                      {config.label}
                    </div>
                    {index < statusFlow.length - 1 && (
                      <div
                        className={`absolute top-5 h-0.5 ${
                          index < currentStatusIndex ? config.color : 'bg-gray-300'
                        }`}
                        style={{
                          left: `${(index * 100) / (statusFlow.length - 1) + 7}%`,
                          width: `${93 / (statusFlow.length - 1)}%`,
                        }}
                      />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Info Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cliente</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{pedido.cliente_nome}</div>
            <p className="text-xs text-muted-foreground mt-1">{pedido.cliente_documento}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Vendedor</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{pedido.vendedor_nome}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Entrega Prevista</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {format(new Date(pedido.data_entrega_prevista), 'dd/MM/yyyy')}
            </div>
            {pedido.data_entrega_real && (
              <p className="text-xs text-muted-foreground mt-1">
                Entregue em {format(new Date(pedido.data_entrega_real), 'dd/MM/yyyy')}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Valor Total</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {pedido.valor_total.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL',
              })}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {pedido.itens.length} {pedido.itens.length === 1 ? 'item' : 'itens'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Delivery Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Truck className="h-5 w-5" />
            Informações de Entrega
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-start gap-2">
            <MapPin className="h-4 w-4 mt-0.5 text-muted-foreground" />
            <div>
              <p className="font-medium">Tipo: {pedido.tipo_entrega}</p>
              {pedido.endereco_entrega && (
                <p className="text-sm text-muted-foreground mt-1">{pedido.endereco_entrega}</p>
              )}
            </div>
          </div>
          {pedido.forma_pagamento && (
            <div className="flex items-start gap-2">
              <DollarSign className="h-4 w-4 mt-0.5 text-muted-foreground" />
              <div>
                <p className="font-medium">Pagamento: {pedido.forma_pagamento}</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Items Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Itens do Pedido
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[60px]">Cód.</TableHead>
                <TableHead>Produto</TableHead>
                <TableHead className="text-right">Qtd.</TableHead>
                {pedido.status !== 'RASCUNHO' && pedido.status !== 'CONFIRMADO' && (
                  <TableHead className="text-right">Separado</TableHead>
                )}
                <TableHead className="text-right">Preço Unit.</TableHead>
                <TableHead className="text-right">Desconto</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {pedido.itens.map((item) => {
                const total = item.quantidade * item.preco_unitario - item.desconto_item
                return (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono text-xs">{item.produto_codigo}</TableCell>
                    <TableCell>
                      <div className="font-medium">{item.produto_nome}</div>
                      {item.observacao_item && (
                        <div className="text-xs text-muted-foreground mt-1">
                          {item.observacao_item}
                        </div>
                      )}
                    </TableCell>
                    <TableCell className="text-right">{item.quantidade}</TableCell>
                    {pedido.status !== 'RASCUNHO' && pedido.status !== 'CONFIRMADO' && (
                      <TableCell className="text-right">
                        <Badge variant={item.quantidade_separada === item.quantidade ? 'default' : 'secondary'}>
                          {item.quantidade_separada || 0}
                        </Badge>
                      </TableCell>
                    )}
                    <TableCell className="text-right">
                      {item.preco_unitario.toLocaleString('pt-BR', {
                        style: 'currency',
                        currency: 'BRL',
                      })}
                    </TableCell>
                    <TableCell className="text-right">
                      {item.desconto_item > 0 && (
                        <span className="text-red-600">
                          -{item.desconto_item.toLocaleString('pt-BR', {
                            style: 'currency',
                            currency: 'BRL',
                          })}
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-bold">
                      {total.toLocaleString('pt-BR', {
                        style: 'currency',
                        currency: 'BRL',
                      })}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Totals */}
      <Card>
        <CardHeader>
          <CardTitle>Totalizadores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Subtotal:</span>
              <span className="font-medium">
                {subtotal.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </span>
            </div>
            {pedido.desconto > 0 && (
              <div className="flex justify-between text-red-600">
                <span>Desconto:</span>
                <span className="font-medium">
                  -{pedido.desconto.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </span>
              </div>
            )}
            {pedido.valor_frete > 0 && (
              <div className="flex justify-between">
                <span>Frete:</span>
                <span className="font-medium">
                  +{pedido.valor_frete.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </span>
              </div>
            )}
            {pedido.outras_despesas > 0 && (
              <div className="flex justify-between">
                <span>Outras Despesas:</span>
                <span className="font-medium">
                  +{pedido.outras_despesas.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </span>
              </div>
            )}
            <Separator />
            <div className="flex justify-between text-lg font-bold">
              <span>TOTAL:</span>
              <span className="text-primary">
                {pedido.valor_total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Observations */}
      {pedido.observacoes && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Observações
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap">{pedido.observacoes}</p>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end gap-2 flex-wrap">
        <Button variant="outline" onClick={() => window.print()}>
          <Printer className="mr-2 h-4 w-4" />
          Imprimir
        </Button>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          PDF
        </Button>

        {pedido.status === 'RASCUNHO' && onEdit && (
          <Button variant="outline" onClick={onEdit}>
            <Edit className="mr-2 h-4 w-4" />
            Editar
          </Button>
        )}
        {pedido.status === 'RASCUNHO' && onConfirmar && (
          <Button onClick={onConfirmar}>
            <CheckCircle className="mr-2 h-4 w-4" />
            Confirmar Pedido
          </Button>
        )}
        {pedido.status === 'CONFIRMADO' && onIniciarSeparacao && (
          <Button onClick={onIniciarSeparacao}>Iniciar Separação</Button>
        )}
        {pedido.status === 'EM_SEPARACAO' && onFinalizarSeparacao && (
          <Button onClick={onFinalizarSeparacao}>Finalizar Separação</Button>
        )}
        {pedido.status === 'SEPARADO' && onEnviarParaEntrega && (
          <Button onClick={onEnviarParaEntrega}>
            <Truck className="mr-2 h-4 w-4" />
            Enviar para Entrega
          </Button>
        )}
        {pedido.status === 'EM_ENTREGA' && onConfirmarEntrega && (
          <Button onClick={onConfirmarEntrega}>Confirmar Entrega</Button>
        )}
        {pedido.status === 'ENTREGUE' && onFaturar && (
          <Button onClick={onFaturar}>
            <DollarSign className="mr-2 h-4 w-4" />
            Faturar Pedido
          </Button>
        )}
        {pedido.status !== 'FATURADO' && pedido.status !== 'CANCELADO' && onCancelar && (
          <Button variant="destructive" onClick={onCancelar}>
            Cancelar Pedido
          </Button>
        )}
        {onClose && (
          <Button variant="ghost" onClick={onClose}>
            Fechar
          </Button>
        )}
      </div>
    </div>
  )
}
