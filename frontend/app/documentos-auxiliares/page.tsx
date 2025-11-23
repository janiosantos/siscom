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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  FileText,
  Download,
  Eye,
  Printer,
  FileCheck,
  Receipt,
  Package,
  Truck,
  ShoppingCart
} from 'lucide-react'

type TipoDocumento = 'PEDIDO_VENDA' | 'ORCAMENTO' | 'NOTA_ENTREGA' | 'ROMANEIO' | 'COMPROVANTE_ENTREGA' | 'RECIBO' | 'PEDIDO_COMPRA'

interface DocumentoAuxiliar {
  id: number
  tipo_documento: TipoDocumento
  numero_documento: string
  cliente_nome: string
  data_geracao: string
  arquivo_pdf: string
  gerado_por: string
}

export default function DocumentosAuxiliaresPage() {
  const [documentos, setDocumentos] = useState<DocumentoAuxiliar[]>([])
  const [loading, setLoading] = useState(true)
  const [filtroTipo, setFiltroTipo] = useState<TipoDocumento | 'TODOS'>('TODOS')
  const [stats, setStats] = useState({
    total: 0,
    pedidosVenda: 0,
    orcamentos: 0,
    notasEntrega: 0,
    romaneios: 0
  })

  useEffect(() => {
    fetchDocumentos()
  }, [filtroTipo])

  const fetchDocumentos = async () => {
    try {
      // TODO: Integrar com API real
      // const response = await fetch('/api/v1/documentos-auxiliares/')
      // const data = await response.json()

      // Mock data
      const mockData: DocumentoAuxiliar[] = [
        {
          id: 1,
          tipo_documento: 'PEDIDO_VENDA',
          numero_documento: 'PV000001',
          cliente_nome: 'Construtora XYZ Ltda',
          data_geracao: '2025-11-23 10:30:00',
          arquivo_pdf: '/storage/pedido_venda_PV000001.pdf',
          gerado_por: 'Maria Santos'
        },
        {
          id: 2,
          tipo_documento: 'ORCAMENTO',
          numero_documento: 'ORC-001',
          cliente_nome: 'João Silva Construções',
          data_geracao: '2025-11-22 15:20:00',
          arquivo_pdf: '/storage/orcamento_ORC001.pdf',
          gerado_por: 'Pedro Costa'
        },
        {
          id: 3,
          tipo_documento: 'NOTA_ENTREGA',
          numero_documento: 'PV000001',
          cliente_nome: 'Construtora XYZ Ltda',
          data_geracao: '2025-11-23 14:45:00',
          arquivo_pdf: '/storage/nota_entrega_PV000001.pdf',
          gerado_por: 'Ana Paula'
        },
        {
          id: 4,
          tipo_documento: 'ROMANEIO',
          numero_documento: 'PV000002',
          cliente_nome: 'Reforma Total S.A.',
          data_geracao: '2025-11-23 09:15:00',
          arquivo_pdf: '/storage/romaneio_PV000002.pdf',
          gerado_por: 'Carlos Lima'
        },
        {
          id: 5,
          tipo_documento: 'COMPROVANTE_ENTREGA',
          numero_documento: 'PV000001',
          cliente_nome: 'Construtora XYZ Ltda',
          data_geracao: '2025-11-23 16:30:00',
          arquivo_pdf: '/storage/comprovante_PV000001.pdf',
          gerado_por: 'Maria Santos'
        }
      ]

      const filtered = filtroTipo === 'TODOS'
        ? mockData
        : mockData.filter(d => d.tipo_documento === filtroTipo)

      setDocumentos(filtered)

      // Calcular estatísticas
      setStats({
        total: mockData.length,
        pedidosVenda: mockData.filter(d => d.tipo_documento === 'PEDIDO_VENDA').length,
        orcamentos: mockData.filter(d => d.tipo_documento === 'ORCAMENTO').length,
        notasEntrega: mockData.filter(d => d.tipo_documento === 'NOTA_ENTREGA').length,
        romaneios: mockData.filter(d => d.tipo_documento === 'ROMANEIO').length
      })
    } catch (error) {
      console.error('Erro ao carregar documentos:', error)
    } finally {
      setLoading(false)
    }
  }

  const getTipoConfig = (tipo: TipoDocumento) => {
    const configs: Record<TipoDocumento, { label: string; icon: any; color: string }> = {
      PEDIDO_VENDA: { label: 'Pedido de Venda', icon: FileText, color: 'text-blue-500' },
      ORCAMENTO: { label: 'Orçamento', icon: FileCheck, color: 'text-green-500' },
      NOTA_ENTREGA: { label: 'Nota de Entrega', icon: Package, color: 'text-orange-500' },
      ROMANEIO: { label: 'Romaneio', icon: Receipt, color: 'text-purple-500' },
      COMPROVANTE_ENTREGA: { label: 'Comprovante de Entrega', icon: Truck, color: 'text-cyan-500' },
      RECIBO: { label: 'Recibo', icon: Receipt, color: 'text-gray-500' },
      PEDIDO_COMPRA: { label: 'Pedido de Compra', icon: ShoppingCart, color: 'text-indigo-500' }
    }
    return configs[tipo]
  }

  const getTipoBadge = (tipo: TipoDocumento) => {
    const config = getTipoConfig(tipo)
    const Icon = config.icon

    return (
      <Badge variant="outline" className="flex items-center gap-1">
        <Icon className={`h-3 w-3 ${config.color}`} />
        {config.label}
      </Badge>
    )
  }

  const handleDownload = (documentoId: number) => {
    console.log(`Download documento ${documentoId}`)
    // TODO: Implementar download real
    // window.open(`/api/v1/documentos-auxiliares/${documentoId}/download`, '_blank')
  }

  const handleVisualizar = (documentoId: number) => {
    console.log(`Visualizar documento ${documentoId}`)
    // TODO: Implementar visualização
    // window.open(`/api/v1/documentos-auxiliares/${documentoId}/visualizar`, '_blank')
  }

  const handleImprimir = (documentoId: number) => {
    console.log(`Imprimir documento ${documentoId}`)
    // TODO: Implementar impressão
  }

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Carregando...</div>
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Documentos Auxiliares</h1>
          <p className="text-muted-foreground">Gerencie documentos não fiscais em PDF</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
            <p className="text-xs text-muted-foreground">Documentos gerados</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pedidos</CardTitle>
            <FileText className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.pedidosVenda}</div>
            <p className="text-xs text-muted-foreground">Pedidos de venda</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Orçamentos</CardTitle>
            <FileCheck className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.orcamentos}</div>
            <p className="text-xs text-muted-foreground">Orçamentos impressos</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Notas</CardTitle>
            <Package className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.notasEntrega}</div>
            <p className="text-xs text-muted-foreground">Notas de entrega</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Romaneios</CardTitle>
            <Receipt className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.romaneios}</div>
            <p className="text-xs text-muted-foreground">Listas de separação</p>
          </CardContent>
        </Card>
      </div>

      {/* Geração Rápida */}
      <Card>
        <CardHeader>
          <CardTitle>Gerar Novo Documento</CardTitle>
          <CardDescription>Selecione o tipo de documento e o pedido/orçamento</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo de Documento</label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="PEDIDO_VENDA">Pedido de Venda</SelectItem>
                  <SelectItem value="ORCAMENTO">Orçamento</SelectItem>
                  <SelectItem value="NOTA_ENTREGA">Nota de Entrega</SelectItem>
                  <SelectItem value="ROMANEIO">Romaneio</SelectItem>
                  <SelectItem value="COMPROVANTE_ENTREGA">Comprovante de Entrega</SelectItem>
                  <SelectItem value="RECIBO">Recibo</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Pedido/Orçamento</label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Selecione" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">PV000001 - Construtora XYZ</SelectItem>
                  <SelectItem value="2">PV000002 - João Silva</SelectItem>
                  <SelectItem value="3">ORC-001 - Reforma Total</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button className="w-full">
                <FileText className="mr-2 h-4 w-4" />
                Gerar Documento
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filtro */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Documentos Gerados</CardTitle>
              <CardDescription>Histórico de todos os documentos</CardDescription>
            </div>
            <Select value={filtroTipo} onValueChange={(value) => setFiltroTipo(value as any)}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Filtrar por tipo" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="TODOS">Todos os Tipos</SelectItem>
                <SelectItem value="PEDIDO_VENDA">Pedidos de Venda</SelectItem>
                <SelectItem value="ORCAMENTO">Orçamentos</SelectItem>
                <SelectItem value="NOTA_ENTREGA">Notas de Entrega</SelectItem>
                <SelectItem value="ROMANEIO">Romaneios</SelectItem>
                <SelectItem value="COMPROVANTE_ENTREGA">Comprovantes</SelectItem>
                <SelectItem value="RECIBO">Recibos</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Número</TableHead>
                <TableHead>Cliente</TableHead>
                <TableHead>Data Geração</TableHead>
                <TableHead>Gerado Por</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documentos.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                    Nenhum documento encontrado
                  </TableCell>
                </TableRow>
              ) : (
                documentos.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">#{doc.id}</TableCell>
                    <TableCell>{getTipoBadge(doc.tipo_documento)}</TableCell>
                    <TableCell className="font-medium">{doc.numero_documento}</TableCell>
                    <TableCell>{doc.cliente_nome}</TableCell>
                    <TableCell>{new Date(doc.data_geracao).toLocaleString('pt-BR')}</TableCell>
                    <TableCell>{doc.gerado_por}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleVisualizar(doc.id)}
                          title="Visualizar"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDownload(doc.id)}
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleImprimir(doc.id)}
                          title="Imprimir"
                        >
                          <Printer className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">💡 Sobre Documentos Auxiliares</CardTitle>
        </CardHeader>
        <CardContent className="text-blue-800 space-y-2">
          <p><strong>Documentos auxiliares são documentos não fiscais</strong> que acompanham as operações comerciais:</p>
          <ul className="list-disc list-inside space-y-1 ml-4">
            <li><strong>Pedido de Venda:</strong> Documento impresso do pedido para o cliente</li>
            <li><strong>Orçamento:</strong> Proposta comercial com validade definida</li>
            <li><strong>Nota de Entrega:</strong> Acompanha a mercadoria para conferência</li>
            <li><strong>Romaneio:</strong> Lista de produtos para separação no estoque</li>
            <li><strong>Comprovante de Entrega:</strong> Assinado pelo cliente ao receber</li>
            <li><strong>Recibo:</strong> Comprovante de pagamento simplificado</li>
          </ul>
          <p className="pt-2">
            ⚠️ <strong>Atenção:</strong> Estes documentos NÃO substituem documentos fiscais (NF-e/NFC-e)
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
