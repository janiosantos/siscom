"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Plus, Search, Eye, XCircle, CheckCircle, ShoppingCart } from "lucide-react"
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
import { Select, SelectItem } from "@/components/ui/select"
import { ProtectedPage } from "@/components/auth/protected-page"
import { PermissionGuard } from "@/components/auth/permission-guard"
import { vendasApi } from "@/lib/api/vendas"
import { formatCurrency } from "@/lib/utils"
import { toast } from "sonner"
import { useRouter } from "next/navigation"

const statusOptions = [
  { value: "", label: "Todos os status" },
  { value: "orcamento", label: "Orçamento" },
  { value: "pendente", label: "Pendente" },
  { value: "finalizada", label: "Finalizada" },
  { value: "cancelada", label: "Cancelada" },
]

const getStatusVariant = (status: string) => {
  switch (status) {
    case "finalizada":
      return "success"
    case "cancelada":
      return "destructive"
    case "orcamento":
      return "warning"
    default:
      return "default"
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case "finalizada":
      return "Finalizada"
    case "cancelada":
      return "Cancelada"
    case "orcamento":
      return "Orçamento"
    case "pendente":
      return "Pendente"
    default:
      return status
  }
}

export default function VendasPage() {
  const router = useRouter()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("")

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["vendas", page, search, statusFilter],
    queryFn: () =>
      vendasApi.list({
        page,
        page_size: 10,
        status: statusFilter || undefined,
      }),
  })

  const handleCancel = async (id: number) => {
    if (!confirm("Tem certeza que deseja cancelar esta venda?")) return

    try {
      await vendasApi.cancel(id)
      toast.success("Venda cancelada com sucesso!")
      refetch()
    } catch (error) {
      toast.error("Erro ao cancelar venda")
    }
  }

  const handleFinalize = async (id: number) => {
    if (!confirm("Tem certeza que deseja finalizar esta venda?")) return

    try {
      await vendasApi.finalize(id)
      toast.success("Venda finalizada com sucesso!")
      refetch()
    } catch (error) {
      toast.error("Erro ao finalizar venda")
    }
  }

  const handleView = (id: number) => {
    router.push(`/vendas/${id}`)
  }

  const handleNewSale = () => {
    router.push("/pdv")
  }

  return (
    <ProtectedPage permission="vendas.view">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <ShoppingCart className="h-8 w-8" />
              Vendas
            </h1>
            <p className="text-muted-foreground">
              Gerencie as vendas e orçamentos
            </p>
          </div>
          <PermissionGuard permission="vendas.create">
            <Button onClick={handleNewSale}>
              <Plus className="mr-2 h-4 w-4" />
              Nova Venda (PDV)
            </Button>
          </PermissionGuard>
        </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>Busque e filtre vendas</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por número, cliente..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>
            <div className="w-48">
              <Select
                value={statusFilter}
                onValueChange={(value) => setStatusFilter(value)}
              >
                {statusOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </Select>
            </div>
            <Button
              variant="outline"
              onClick={() => {
                setSearch("")
                setStatusFilter("")
              }}
            >
              Limpar Filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>Lista de Vendas</CardTitle>
          <CardDescription>
            {data?.total || 0} vendas encontradas
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
                    <TableHead>Número</TableHead>
                    <TableHead>Data</TableHead>
                    <TableHead>Cliente</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                    <TableHead className="text-right">Desconto</TableHead>
                    <TableHead className="text-right">Total Final</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data?.items?.map((venda) => (
                    <TableRow key={venda.id}>
                      <TableCell className="font-mono text-sm">
                        #{venda.id.toString().padStart(6, "0")}
                      </TableCell>
                      <TableCell>
                        {new Date(venda.data_venda).toLocaleDateString(
                          "pt-BR"
                        )}
                      </TableCell>
                      <TableCell>
                        {venda.cliente?.nome || "Cliente Avulso"}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(venda.total_produtos)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(venda.desconto)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(venda.total_final)}
                      </TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(venda.status)}>
                          {getStatusLabel(venda.status)}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Visualizar"
                            onClick={() => handleView(venda.id)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {venda.status === "pendente" && (
                            <>
                              <PermissionGuard permission="vendas.update">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  title="Finalizar"
                                  onClick={() => handleFinalize(venda.id)}
                                >
                                  <CheckCircle className="h-4 w-4 text-green-600" />
                                </Button>
                              </PermissionGuard>
                              <PermissionGuard permission="vendas.cancel">
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  title="Cancelar"
                                  onClick={() => handleCancel(venda.id)}
                                >
                                  <XCircle className="h-4 w-4 text-red-600" />
                                </Button>
                              </PermissionGuard>
                            </>
                          )}
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
