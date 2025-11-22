"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  Search,
  Plus,
  Minus,
  Trash2,
  ShoppingCart,
  User,
  DollarSign,
  Percent,
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
import { Select, SelectItem } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { ProtectedPage } from "@/components/auth/protected-page"
import { produtosApi } from "@/lib/api/produtos"
import { clientesApi } from "@/lib/api/clientes"
import { vendasApi } from "@/lib/api/vendas"
import { formatCurrency } from "@/lib/utils"
import { toast } from "sonner"
import { Produto, VendaItemCreate } from "@/types"
import { useRouter } from "next/navigation"

interface CartItem {
  produto: Produto
  quantidade: number
  preco_unitario: number
  desconto_item: number
  total: number
}

export default function PDVPage() {
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState("")
  const [cart, setCart] = useState<CartItem[]>([])
  const [clienteId, setClienteId] = useState<number | undefined>()
  const [descontoGeral, setDescontoGeral] = useState(0)
  const [isProcessing, setIsProcessing] = useState(false)

  // Load produtos
  const { data: produtosData } = useQuery({
    queryKey: ["produtos-search", searchTerm],
    queryFn: () =>
      produtosApi.list({
        page: 1,
        page_size: 10,
        search: searchTerm || undefined,
      }),
    enabled: searchTerm.length >= 2,
  })

  // Load clientes
  const { data: clientesData } = useQuery({
    queryKey: ["clientes"],
    queryFn: () => clientesApi.listAll(),
  })

  const addToCart = (produto: Produto) => {
    const existingItem = cart.find((item) => item.produto.id === produto.id)

    if (existingItem) {
      updateQuantity(produto.id, existingItem.quantidade + 1)
    } else {
      const newItem: CartItem = {
        produto,
        quantidade: 1,
        preco_unitario: produto.preco_venda,
        desconto_item: 0,
        total: produto.preco_venda,
      }
      setCart([...cart, newItem])
      toast.success(`${produto.descricao} adicionado ao carrinho`)
    }
  }

  const updateQuantity = (produtoId: number, quantidade: number) => {
    if (quantidade <= 0) {
      removeFromCart(produtoId)
      return
    }

    setCart(
      cart.map((item) => {
        if (item.produto.id === produtoId) {
          const total =
            item.preco_unitario * quantidade - item.desconto_item
          return { ...item, quantidade, total }
        }
        return item
      })
    )
  }

  const updateItemDiscount = (produtoId: number, desconto: number) => {
    setCart(
      cart.map((item) => {
        if (item.produto.id === produtoId) {
          const total = item.preco_unitario * item.quantidade - desconto
          return { ...item, desconto_item: desconto, total }
        }
        return item
      })
    )
  }

  const removeFromCart = (produtoId: number) => {
    setCart(cart.filter((item) => item.produto.id !== produtoId))
  }

  const clearCart = () => {
    setCart([])
    setClienteId(undefined)
    setDescontoGeral(0)
    setSearchTerm("")
  }

  const calculateTotals = () => {
    const totalProdutos = cart.reduce((sum, item) => sum + item.total, 0)
    const totalFinal = totalProdutos - descontoGeral
    return { totalProdutos, totalFinal }
  }

  const handleFinalizeSale = async () => {
    if (cart.length === 0) {
      toast.error("Adicione produtos ao carrinho")
      return
    }

    setIsProcessing(true)

    try {
      const { totalProdutos, totalFinal } = calculateTotals()

      const items: VendaItemCreate[] = cart.map((item) => ({
        produto_id: item.produto.id,
        quantidade: item.quantidade,
        preco_unitario: item.preco_unitario,
        desconto_item: item.desconto_item,
        total: item.total,
      }))

      const vendaData = {
        cliente_id: clienteId,
        data_venda: new Date().toISOString(),
        total_produtos: totalProdutos,
        desconto: descontoGeral,
        total_final: totalFinal,
        status: "pendente",
        items,
      }

      const venda = await vendasApi.create(vendaData)
      toast.success(`Venda #${venda.id} criada com sucesso!`)

      // Clear cart and redirect
      clearCart()
      router.push(`/vendas/${venda.id}`)
    } catch (error: any) {
      console.error("Erro ao finalizar venda:", error)
      toast.error(
        error.response?.data?.detail || "Erro ao finalizar venda"
      )
    } finally {
      setIsProcessing(false)
    }
  }

  const { totalProdutos, totalFinal } = calculateTotals()

  return (
    <ProtectedPage permission="vendas.create">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-8rem)]">
      {/* Left Column - Product Search */}
      <div className="lg:col-span-2 space-y-4 overflow-y-auto">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              Buscar Produtos
            </CardTitle>
            <CardDescription>
              Digite o código ou descrição do produto
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar produto..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
                autoFocus
              />
            </div>

            {/* Product Results */}
            {searchTerm.length >= 2 && produtosData && (
              <div className="mt-4 space-y-2 max-h-96 overflow-y-auto">
                {produtosData.items.map((produto) => (
                  <div
                    key={produto.id}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent cursor-pointer"
                    onClick={() => addToCart(produto)}
                  >
                    <div className="flex-1">
                      <p className="font-medium">{produto.descricao}</p>
                      <p className="text-sm text-muted-foreground">
                        Código: {produto.codigo_barras}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge
                          variant={
                            produto.estoque_atual <=
                            produto.estoque_minimo
                              ? "destructive"
                              : "success"
                          }
                        >
                          Estoque: {produto.estoque_atual}{" "}
                          {produto.unidade}
                        </Badge>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold">
                        {formatCurrency(produto.preco_venda)}
                      </p>
                      <Button size="sm">
                        <Plus className="h-4 w-4 mr-1" />
                        Adicionar
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Right Column - Cart */}
      <div className="space-y-4">
        <Card className="h-full flex flex-col">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5" />
              Carrinho ({cart.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            {/* Cliente Selection */}
            <div className="space-y-2 mb-4">
              <Label htmlFor="cliente">
                <User className="inline h-4 w-4 mr-1" />
                Cliente
              </Label>
              <Select
                value={clienteId?.toString() || ""}
                onValueChange={(value) =>
                  setClienteId(value ? parseInt(value) : undefined)
                }
              >
                <SelectItem value="">Cliente Avulso</SelectItem>
                {clientesData?.map((cliente) => (
                  <SelectItem
                    key={cliente.id}
                    value={cliente.id.toString()}
                  >
                    {cliente.nome}
                  </SelectItem>
                ))}
              </Select>
            </div>

            {/* Cart Items */}
            <div className="flex-1 overflow-y-auto space-y-2 mb-4">
              {cart.length === 0 ? (
                <div className="flex items-center justify-center h-32 text-muted-foreground">
                  <p>Carrinho vazio</p>
                </div>
              ) : (
                cart.map((item) => (
                  <div
                    key={item.produto.id}
                    className="border rounded-lg p-3 space-y-2"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="font-medium text-sm">
                          {item.produto.descricao}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatCurrency(item.preco_unitario)} / un
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeFromCart(item.produto.id)}
                        className="h-6 w-6"
                      >
                        <Trash2 className="h-3 w-3 text-red-600" />
                      </Button>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() =>
                          updateQuantity(
                            item.produto.id,
                            item.quantidade - 1
                          )
                        }
                        className="h-7 w-7"
                      >
                        <Minus className="h-3 w-3" />
                      </Button>
                      <Input
                        type="number"
                        min="1"
                        value={item.quantidade}
                        onChange={(e) =>
                          updateQuantity(
                            item.produto.id,
                            parseInt(e.target.value) || 1
                          )
                        }
                        className="h-7 w-16 text-center"
                      />
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() =>
                          updateQuantity(
                            item.produto.id,
                            item.quantidade + 1
                          )
                        }
                        className="h-7 w-7"
                      >
                        <Plus className="h-3 w-3" />
                      </Button>
                      <div className="flex-1 text-right">
                        <p className="font-bold">
                          {formatCurrency(item.total)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Totals */}
            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Subtotal:</span>
                <span>{formatCurrency(totalProdutos)}</span>
              </div>

              <div className="flex items-center gap-2">
                <Label htmlFor="desconto" className="flex items-center gap-1">
                  <Percent className="h-3 w-3" />
                  Desconto:
                </Label>
                <Input
                  id="desconto"
                  type="number"
                  min="0"
                  step="0.01"
                  value={descontoGeral}
                  onChange={(e) =>
                    setDescontoGeral(parseFloat(e.target.value) || 0)
                  }
                  className="h-8 w-24 text-right"
                />
              </div>

              <div className="flex justify-between text-lg font-bold pt-2 border-t">
                <span>Total:</span>
                <span className="text-primary">
                  {formatCurrency(totalFinal)}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-2 mt-4">
              <Button
                className="w-full"
                onClick={handleFinalizeSale}
                disabled={cart.length === 0 || isProcessing}
              >
                <DollarSign className="mr-2 h-4 w-4" />
                {isProcessing ? "Processando..." : "Finalizar Venda"}
              </Button>
              <Button
                variant="outline"
                className="w-full"
                onClick={clearCart}
                disabled={cart.length === 0}
              >
                Limpar Carrinho
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
      </div>
    </ProtectedPage>
  )
}
