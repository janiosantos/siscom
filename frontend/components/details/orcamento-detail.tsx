'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
  XCircle,
  Clock,
  Printer,
  Download,
} from 'lucide-react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'

interface OrcamentoDetalhado {
  id: number
  numero_orcamento: string
  cliente_id: number
  cliente_nome: string
  cliente_documento: string
  cliente_email?: string
  cliente_telefone?: string
  vendedor_id: number
  vendedor_nome: string
  data_orcamento: string
  data_validade: string
  status: 'ABERTO' | 'APROVADO' | 'CONVERTIDO' | 'PERDIDO'
  desconto: number
  outras_despesas: number
  valor_total: number
  observacoes?: string
  itens: Array<{
    id: number
    produto_id: number
    produto_nome: string
    produto_codigo: string
    quantidade: number
    preco_unitario: number
    desconto_item: number
    observacao_item?: string
  }>
  historico?: Array<{
    data: string
    acao: string
    usuario: string
    observacao?: string
  }>
}

interface OrcamentoDetailProps {
  orcamento: OrcamentoDetalhado
  onClose?: () => void
  onEdit?: () => void
  onAprovar?: () => void
  onConverter?: () => void
  onRejeitar?: () => void
}

export function OrcamentoDetail({
  orcamento,
  onClose,
  onEdit,
  onAprovar,
  onConverter,
  onRejeitar,
}: OrcamentoDetailProps) {
  const subtotal = orcamento.itens.reduce(
    (sum, item) => sum + (item.quantidade * item.preco_unitario - item.desconto_item),
    0
  )

  const getStatusBadge = (status: string) => {
    const configs = {
      ABERTO: { label: 'Aberto', variant: 'default' as const, icon: Clock },
      APROVADO: { label: 'Aprovado', variant: 'default' as const, icon: CheckCircle },
      CONVERTIDO: { label: 'Convertido', variant: 'secondary' as const, icon: CheckCircle },
      PERDIDO: { label: 'Perdido', variant: 'destructive' as const, icon: XCircle },
    }
    const config = configs[status as keyof typeof configs] || configs.ABERTO
    const Icon = config.icon
    return (
      <Badge variant={config.variant} className="flex items-center gap-1 w-fit">
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold">{orcamento.numero_orcamento}</h2>
          <p className="text-muted-foreground mt-1">
            Criado em {format(new Date(orcamento.data_orcamento), "dd 'de' MMMM 'de' yyyy", { locale: ptBR })}
          </p>
        </div>
        {getStatusBadge(orcamento.status)}
      </div>

      {/* Info Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cliente</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{orcamento.cliente_nome}</div>
            <p className="text-xs text-muted-foreground mt-1">{orcamento.cliente_documento}</p>
            {orcamento.cliente_email && (
              <p className="text-xs text-muted-foreground">{orcamento.cliente_email}</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Vendedor</CardTitle>
            <User className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{orcamento.vendedor_nome}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Validade</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {format(new Date(orcamento.data_validade), 'dd/MM/yyyy')}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {new Date(orcamento.data_validade) < new Date() ? 'Vencido' : 'Válido'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Valor Total</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {orcamento.valor_total.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL',
              })}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {orcamento.itens.length} {orcamento.itens.length === 1 ? 'item' : 'itens'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Items Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Itens do Orçamento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[60px]">Cód.</TableHead>
                <TableHead>Produto</TableHead>
                <TableHead className="text-right">Qtd.</TableHead>
                <TableHead className="text-right">Preço Unit.</TableHead>
                <TableHead className="text-right">Desconto</TableHead>
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {orcamento.itens.map((item) => {
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
            {orcamento.desconto > 0 && (
              <div className="flex justify-between text-red-600">
                <span>Desconto:</span>
                <span className="font-medium">
                  -{orcamento.desconto.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </span>
              </div>
            )}
            {orcamento.outras_despesas > 0 && (
              <div className="flex justify-between">
                <span>Outras Despesas:</span>
                <span className="font-medium">
                  +{orcamento.outras_despesas.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                </span>
              </div>
            )}
            <Separator />
            <div className="flex justify-between text-lg font-bold">
              <span>TOTAL:</span>
              <span className="text-primary">
                {orcamento.valor_total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Observations */}
      {orcamento.observacoes && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Observações
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm whitespace-pre-wrap">{orcamento.observacoes}</p>
          </CardContent>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={() => window.print()}>
          <Printer className="mr-2 h-4 w-4" />
          Imprimir
        </Button>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          PDF
        </Button>
        {orcamento.status === 'ABERTO' && onEdit && (
          <Button variant="outline" onClick={onEdit}>
            Editar
          </Button>
        )}
        {orcamento.status === 'ABERTO' && onAprovar && (
          <Button onClick={onAprovar}>
            <CheckCircle className="mr-2 h-4 w-4" />
            Aprovar
          </Button>
        )}
        {orcamento.status === 'APROVADO' && onConverter && (
          <Button onClick={onConverter}>Converter em Pedido</Button>
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
