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
import { Plus, FileText, Check, X, Clock, DollarSign, Edit2, Loader2 } from 'lucide-react'
import { useOrcamentos } from '@/lib/hooks/use-orcamentos'
import { OrcamentoForm } from '@/components/forms/orcamento-form'

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
  const { orcamentos, isLoading, isError, mutate } = useOrcamentos()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [selectedOrcamento, setSelectedOrcamento] = useState<Orcamento | null>(null)

  // Calcular estatísticas
  const stats = orcamentos ? {
    total: orcamentos.length,
    abertos: orcamentos.filter((o: Orcamento) => o.status === 'ABERTO').length,
    aprovados: orcamentos.filter((o: Orcamento) => o.status === 'APROVADO').length,
    valorTotal: orcamentos.reduce((sum: number, o: Orcamento) => sum + o.valor_total, 0)
  } : {
    total: 0,
    abertos: 0,
    aprovados: 0,
    valorTotal: 0
  }

  const handleNovoOrcamento = () => {
    setSelectedOrcamento(null)
    setIsDialogOpen(true)
  }

  const handleEditarOrcamento = (orcamento: Orcamento) => {
    setSelectedOrcamento(orcamento)
    setIsDialogOpen(true)
  }

  const handleSuccess = () => {
    setIsDialogOpen(false)
    setSelectedOrcamento(null)
    mutate() // Revalidar dados
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Carregando orçamentos...</span>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <X className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Erro ao carregar orçamentos</h2>
          <p className="text-muted-foreground">Tente novamente mais tarde</p>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Dialog para Criar/Editar Orçamento */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {selectedOrcamento ? 'Editar Orçamento' : 'Novo Orçamento'}
            </DialogTitle>
            <DialogDescription>
              {selectedOrcamento
                ? `Editando orçamento ${selectedOrcamento.numero_orcamento}`
                : 'Preencha os dados abaixo para criar um novo orçamento'
              }
            </DialogDescription>
          </DialogHeader>
          <OrcamentoForm
            orcamentoId={selectedOrcamento?.id}
            initialData={selectedOrcamento || undefined}
            onSuccess={handleSuccess}
            onCancel={() => setIsDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Orçamentos</h1>
          <p className="text-muted-foreground">Gerencie orçamentos e propostas</p>
        </div>
        <Button className="flex items-center gap-2" onClick={handleNovoOrcamento}>
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
              {orcamentos && orcamentos.map((orc: Orcamento) => (
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
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="sm" onClick={() => handleEditarOrcamento(orc)}>
                        <Edit2 className="h-4 w-4 mr-2" />
                        Editar
                      </Button>
                      <Button variant="ghost" size="sm">
                        <FileText className="h-4 w-4 mr-2" />
                        Ver
                      </Button>
                    </div>
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
