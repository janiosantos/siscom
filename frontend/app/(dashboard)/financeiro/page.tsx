"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react"
import { Button } from "@/components/ui/button"
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
import { financeiroApi } from "@/lib/api/financeiro"
import { formatCurrency } from "@/lib/utils"
import { toast } from "sonner"

const statusOptions = [
  { value: "", label: "Todos os status" },
  { value: "pendente", label: "Pendente" },
  { value: "pago", label: "Pago" },
  { value: "vencido", label: "Vencido" },
]

const getStatusVariant = (status: string) => {
  switch (status) {
    case "pago":
      return "success"
    case "vencido":
      return "destructive"
    case "pendente":
      return "warning"
    default:
      return "default"
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case "pago":
      return "Pago"
    case "vencido":
      return "Vencido"
    case "pendente":
      return "Pendente"
    default:
      return status
  }
}

export default function FinanceiroPage() {
  const [activeTab, setActiveTab] = useState<"pagar" | "receber">("receber")
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState("")

  // Load contas a pagar
  const { data: contasPagar, refetch: refetchPagar } = useQuery({
    queryKey: ["contas-pagar", page, statusFilter],
    queryFn: () =>
      financeiroApi.listContasPagar({
        page,
        page_size: 10,
        status: statusFilter || undefined,
      }),
    enabled: activeTab === "pagar",
  })

  // Load contas a receber
  const { data: contasReceber, refetch: refetchReceber } = useQuery({
    queryKey: ["contas-receber", page, statusFilter],
    queryFn: () =>
      financeiroApi.listContasReceber({
        page,
        page_size: 10,
        status: statusFilter || undefined,
      }),
    enabled: activeTab === "receber",
  })

  // Load dashboard data
  const { data: dashboardData } = useQuery({
    queryKey: ["financeiro-dashboard"],
    queryFn: () => financeiroApi.dashboard(),
  })

  const handlePagar = async (id: number) => {
    if (!confirm("Confirmar pagamento desta conta?")) return

    try {
      await financeiroApi.pagarConta(id)
      toast.success("Conta paga com sucesso!")
      refetchPagar()
    } catch (error) {
      toast.error("Erro ao pagar conta")
    }
  }

  const handleReceber = async (id: number) => {
    if (!confirm("Confirmar recebimento desta conta?")) return

    try {
      await financeiroApi.receberConta(id)
      toast.success("Conta recebida com sucesso!")
      refetchReceber()
    } catch (error) {
      toast.error("Erro ao receber conta")
    }
  }

  const currentData = activeTab === "pagar" ? contasPagar : contasReceber

  return (
    <ProtectedPage permission="financeiro.view">
      <div className="space-y-6">
        {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <DollarSign className="h-8 w-8" />
            Financeiro
          </h1>
          <p className="text-muted-foreground">
            Gerencie contas a pagar e receber
          </p>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              A Receber (Mês)
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(dashboardData?.total_receber_mes || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {dashboardData?.contas_receber_mes || 0} contas
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              A Pagar (Mês)
            </CardTitle>
            <TrendingDown className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(dashboardData?.total_pagar_mes || 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              {dashboardData?.contas_pagar_mes || 0} contas
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Contas Vencidas
            </CardTitle>
            <Calendar className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {dashboardData?.contas_vencidas || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(dashboardData?.total_vencidas || 0)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Saldo do Mês
            </CardTitle>
            <DollarSign className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(
                (dashboardData?.total_receber_mes || 0) -
                  (dashboardData?.total_pagar_mes || 0)
              )}
            </div>
            <p className="text-xs text-muted-foreground">
              Receitas - Despesas
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => {
            setActiveTab("receber")
            setPage(1)
          }}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "receber"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <TrendingUp className="inline h-4 w-4 mr-2" />
          Contas a Receber
        </button>
        <button
          onClick={() => {
            setActiveTab("pagar")
            setPage(1)
          }}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === "pagar"
              ? "border-b-2 border-primary text-primary"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          <TrendingDown className="inline h-4 w-4 mr-2" />
          Contas a Pagar
        </button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>Filtre as contas</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
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
            <Button variant="outline" onClick={() => setStatusFilter("")}>
              Limpar Filtros
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>
            {activeTab === "receber"
              ? "Contas a Receber"
              : "Contas a Pagar"}
          </CardTitle>
          <CardDescription>
            {currentData?.total || 0} contas encontradas
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Descrição</TableHead>
                <TableHead>Vencimento</TableHead>
                <TableHead className="text-right">Valor</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {currentData?.items?.map((conta) => (
                <TableRow key={conta.id}>
                  <TableCell>
                    <div>
                      <p className="font-medium">{conta.descricao}</p>
                      {activeTab === "receber" && conta.venda_id && (
                        <p className="text-xs text-muted-foreground">
                          Venda #{conta.venda_id}
                        </p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {new Date(conta.data_vencimento).toLocaleDateString(
                      "pt-BR"
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(conta.valor)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusVariant(conta.status)}>
                      {getStatusLabel(conta.status)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    {conta.status === "pendente" && (
                      <PermissionGuard permission="financeiro.update">
                        <Button
                          size="sm"
                          onClick={() =>
                            activeTab === "pagar"
                              ? handlePagar(conta.id)
                              : handleReceber(conta.id)
                          }
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          {activeTab === "pagar" ? "Pagar" : "Receber"}
                        </Button>
                      </PermissionGuard>
                    )}
                    {conta.status === "pago" && conta.data_pagamento && (
                      <p className="text-xs text-muted-foreground">
                        Pago em{" "}
                        {new Date(conta.data_pagamento).toLocaleDateString(
                          "pt-BR"
                        )}
                      </p>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          {currentData && currentData.pages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-muted-foreground">
                Página {currentData.page} de {currentData.pages}
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
                  disabled={page >= currentData.pages}
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
