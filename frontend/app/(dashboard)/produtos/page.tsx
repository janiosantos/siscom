"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Plus, Search, Pencil, Trash2, Package, Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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
import { ProdutoForm } from "@/components/forms/produto-form"
import { ProtectedPage } from "@/components/auth/protected-page"
import { PermissionGuard } from "@/components/auth/permission-guard"
import { produtosApi } from "@/lib/api/produtos"
import { exportProdutosToPDF } from "@/lib/pdf-export"
import { formatCurrency } from "@/lib/utils"
import { toast } from "sonner"
import { Produto } from "@/types"

export default function ProdutosPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [formOpen, setFormOpen] = useState(false)
  const [selectedProduto, setSelectedProduto] = useState<Produto | undefined>(
    undefined
  )

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["produtos", page, search],
    queryFn: () =>
      produtosApi.list({
        page,
        page_size: 10,
        search: search || undefined,
      }),
  })

  const handleDelete = async (id: number) => {
    if (!confirm("Tem certeza que deseja excluir este produto?")) return

    try {
      await produtosApi.delete(id)
      toast.success("Produto excluído com sucesso!")
      refetch()
    } catch (error) {
      toast.error("Erro ao excluir produto")
    }
  }

  const handleNew = () => {
    setSelectedProduto(undefined)
    setFormOpen(true)
  }

  const handleEdit = (produto: Produto) => {
    setSelectedProduto(produto)
    setFormOpen(true)
  }

  const handleSuccess = () => {
    refetch()
  }

  const handleExportPDF = () => {
    if (!data?.items || data.items.length === 0) {
      toast.error("Não há produtos para exportar")
      return
    }

    try {
      exportProdutosToPDF(data.items)
      toast.success("Relatório PDF exportado com sucesso!")
    } catch (error) {
      toast.error("Erro ao exportar PDF")
    }
  }

  return (
    <ProtectedPage permission="produtos.view">
      <div className="space-y-6">
        {/* Product Form Dialog */}
        <ProdutoForm
          open={formOpen}
          onOpenChange={setFormOpen}
          produto={selectedProduto}
          onSuccess={handleSuccess}
        />

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Package className="h-8 w-8" />
              Produtos
            </h1>
            <p className="text-muted-foreground">
              Gerencie o catálogo de produtos
            </p>
          </div>
          <div className="flex gap-2">
            <PermissionGuard permission="produtos.view">
              <Button variant="outline" onClick={handleExportPDF}>
                <Download className="mr-2 h-4 w-4" />
                Exportar PDF
              </Button>
            </PermissionGuard>
            <PermissionGuard permission="produtos.create">
              <Button onClick={handleNew}>
                <Plus className="mr-2 h-4 w-4" />
                Novo Produto
              </Button>
            </PermissionGuard>
          </div>
        </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>Busque e filtre produtos</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por código, descrição..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            <Button variant="outline">Limpar Filtros</Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Produtos</CardTitle>
          <CardDescription>
            {data?.total || 0} produtos encontrados
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Código</TableHead>
                    <TableHead>Descrição</TableHead>
                    <TableHead>Categoria</TableHead>
                    <TableHead className="text-right">Preço Custo</TableHead>
                    <TableHead className="text-right">Preço Venda</TableHead>
                    <TableHead className="text-right">Estoque</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.items?.map((produto) => (
                    <TableRow key={produto.id}>
                      <TableCell className="font-mono text-sm">
                        {produto.codigo_barras}
                      </TableCell>
                      <TableCell className="font-medium">
                        {produto.descricao}
                      </TableCell>
                      <TableCell>
                        {produto.categoria?.nome || "N/A"}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(produto.preco_custo)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(produto.preco_venda)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge
                          variant={
                            produto.estoque_atual <= produto.estoque_minimo
                              ? "destructive"
                              : "success"
                          }
                        >
                          {produto.estoque_atual} {produto.unidade}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={produto.ativo ? "success" : "destructive"}>
                          {produto.ativo ? "Ativo" : "Inativo"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <PermissionGuard permission="produtos.update">
                            <Button
                              variant="ghost"
                              size="icon"
                              title="Editar"
                              onClick={() => handleEdit(produto)}
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                          </PermissionGuard>
                          <PermissionGuard permission="produtos.delete">
                            <Button
                              variant="ghost"
                              size="icon"
                              title="Excluir"
                              onClick={() => handleDelete(produto.id)}
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </Button>
                          </PermissionGuard>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {data && data.pages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-muted-foreground">
                    Página {data.page} de {data.pages}
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
                      disabled={page >= data.pages}
                    >
                      Próxima
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
      </div>
    </ProtectedPage>
  )
}
