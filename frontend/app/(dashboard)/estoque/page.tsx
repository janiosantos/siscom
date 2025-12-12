"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  Warehouse,
  Plus,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Package,
  Search,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Select, SelectItem } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { ProtectedPage } from "@/components/auth/protected-page"
import { PermissionGuard } from "@/components/auth/permission-guard"
import { estoqueApi } from "@/lib/api/estoque"
import { produtosApi } from "@/lib/api/produtos"
import { formatCurrency } from "@/lib/utils"
import { toast } from "sonner"
import { MovimentacaoEstoqueCreate, TipoMovimentacao } from "@/types"

const tipoMovimentacaoOptions = [
  { value: "", label: "Todos os tipos" },
  { value: "entrada", label: "Entrada" },
  { value: "saida", label: "Saída" },
  { value: "ajuste", label: "Ajuste" },
  { value: "devolucao", label: "Devolução" },
]

export default function EstoquePage() {
  const [page, setPage] = useState(1)
  const [tipoFilter, setTipoFilter] = useState("")
  const [formOpen, setFormOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const [formData, setFormData] = useState<MovimentacaoEstoqueCreate>({
    produto_id: 0,
    tipo: TipoMovimentacao.ENTRADA,
    quantidade: 0,
    observacao: "",
  })

  // Load movimentações
  const { data: movimentacoes, refetch: refetchMovimentacoes } = useQuery({
    queryKey: ["estoque-movimentacoes", page, tipoFilter],
    queryFn: () =>
      estoqueApi.listMovimentacoes({
        page,
        page_size: 10,
        tipo: tipoFilter || undefined,
      }),
  })

  // Load produtos com estoque baixo
  const { data: produtosBaixoEstoque } = useQuery({
    queryKey: ["produtos-baixo-estoque"],
    queryFn: () => estoqueApi.produtosBaixoEstoque(),
  })

  // Load all produtos for select
  const { data: produtosData } = useQuery({
    queryKey: ["produtos-all"],
    queryFn: () => produtosApi.list({ page: 1, page_size: 1000 }),
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      if (formData.produto_id === 0) {
        toast.error("Selecione um produto")
        setIsLoading(false)
        return
      }

      if (formData.quantidade <= 0) {
        toast.error("Quantidade deve ser maior que zero")
        setIsLoading(false)
        return
      }

      await estoqueApi.createMovimentacao(formData)
      toast.success("Movimentação registrada com sucesso!")

      setFormOpen(false)
      setFormData({
        produto_id: 0,
        tipo: TipoMovimentacao.ENTRADA,
        quantidade: 0,
        observacao: "",
      })
      refetchMovimentacoes()
    } catch (error: any) {
      console.error("Erro ao criar movimentação:", error)
      toast.error(
        error.response?.data?.detail || "Erro ao criar movimentação"
      )
    } finally {
      setIsLoading(false)
    }
  }

  const getTipoIcon = (tipo: string) => {
    switch (tipo) {
      case "entrada":
        return <TrendingUp className="h-4 w-4 text-green-600" />
      case "saida":
        return <TrendingDown className="h-4 w-4 text-red-600" />
      default:
        return <Package className="h-4 w-4" />
    }
  }

  const getTipoBadgeVariant = (tipo: string) => {
    switch (tipo) {
      case "entrada":
        return "success"
      case "saida":
        return "destructive"
      default:
        return "default"
    }
  }

  return (
    <ProtectedPage permission="estoque.view">
      <div className="space-y-6">
        {/* Movimentação Form Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent>
          <DialogHeader onClose={() => setFormOpen(false)}>
            <DialogTitle>Nova Movimentação de Estoque</DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="produto">
                Produto <span className="text-red-500">*</span>
              </Label>
              <Select
                value={formData.produto_id.toString()}
                onValueChange={(value) =>
                  setFormData({ ...formData, produto_id: parseInt(value) })
                }
                disabled={isLoading}
              >
                {produtosData?.items?.map((produto) => (
                  <SelectItem key={produto.id} value={produto.id.toString()}>
                    {produto.descricao}
                  </SelectItem>
                ))}
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tipo">
                Tipo <span className="text-red-500">*</span>
              </Label>
              <Select
                value={formData.tipo}
                onValueChange={(value) =>
                  setFormData({ ...formData, tipo: value as TipoMovimentacao })
                }
                disabled={isLoading}
              >
                <SelectItem value={TipoMovimentacao.ENTRADA}>Entrada</SelectItem>
                <SelectItem value={TipoMovimentacao.SAIDA}>Saída</SelectItem>
                <SelectItem value={TipoMovimentacao.AJUSTE}>Ajuste</SelectItem>
                <SelectItem value={TipoMovimentacao.TRANSFERENCIA}>Transferência</SelectItem>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="quantidade">
                Quantidade <span className="text-red-500">*</span>
              </Label>
              <Input
                id="quantidade"
                type="number"
                step="0.01"
                min="0.01"
                value={formData.quantidade}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    quantidade: parseFloat(e.target.value) || 0,
                  })
                }
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="observacao">Observação</Label>
              <Input
                id="observacao"
                value={formData.observacao}
                onChange={(e) =>
                  setFormData({ ...formData, observacao: e.target.value })
                }
                placeholder="Digite uma observação (opcional)"
                disabled={isLoading}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setFormOpen(false)}
                disabled={isLoading}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "Salvando..." : "Salvar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Warehouse className="h-8 w-8" />
            Estoque
          </h1>
          <p className="text-muted-foreground">
            Gerencie o estoque e movimentações
          </p>
        </div>
        <PermissionGuard permission="estoque.create">
          <Button onClick={() => setFormOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Nova Movimentação
          </Button>
        </PermissionGuard>
      </div>

      {/* Alertas de Estoque Baixo */}
      {produtosBaixoEstoque && produtosBaixoEstoque.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-800">
              <AlertTriangle className="h-5 w-5" />
              Alertas de Estoque
            </CardTitle>
            <CardDescription className="text-orange-700">
              {produtosBaixoEstoque.length} produtos com estoque abaixo do
              mínimo
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {produtosBaixoEstoque.slice(0, 5).map((produto) => (
                <div
                  key={produto.id}
                  className="flex items-center justify-between p-2 bg-white rounded border border-orange-200"
                >
                  <div className="flex-1">
                    <p className="font-medium text-sm">
                      {produto.descricao}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Código: {produto.codigo_barras}
                    </p>
                  </div>
                  <div className="text-right">
                    <Badge variant="destructive">
                      {produto.estoque_atual} {produto.unidade}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-1">
                      Mín: {produto.estoque_minimo} {produto.unidade}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            {produtosBaixoEstoque.length > 5 && (
              <p className="text-sm text-orange-700 mt-3">
                E mais {produtosBaixoEstoque.length - 5} produtos...
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>Filtre as movimentações de estoque</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="w-48">
              <Select
                value={tipoFilter}
                onValueChange={(value) => setTipoFilter(value)}
              >
                {tipoMovimentacaoOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </Select>
            </div>
            <Button variant="outline" onClick={() => setTipoFilter("")}>
              Limpar Filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Movimentações Table */}
      <Card>
        <CardHeader>
          <CardTitle>Movimentações de Estoque</CardTitle>
          <CardDescription>
            {movimentacoes?.total || 0} movimentações encontradas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Produto</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead className="text-right">Quantidade</TableHead>
                <TableHead>Observação</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {movimentacoes?.items?.map((mov) => (
                <TableRow key={mov.id}>
                  <TableCell>
                    {new Date(mov.data_movimentacao).toLocaleDateString(
                      "pt-BR"
                    )}
                  </TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">
                        {mov.produto?.descricao}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {mov.produto?.codigo_barras}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getTipoBadgeVariant(mov.tipo)}>
                      <span className="flex items-center gap-1">
                        {getTipoIcon(mov.tipo)}
                        {mov.tipo.charAt(0).toUpperCase() +
                          mov.tipo.slice(1)}
                      </span>
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {mov.quantidade} {mov.produto?.unidade}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {mov.observacao || "-"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          {movimentacoes && movimentacoes.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                Página {movimentacoes.page} de {movimentacoes.pages}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page >= movimentacoes.pages}
                >
                  Próxima
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      </div>
    </ProtectedPage>
  )
}
