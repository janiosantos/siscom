"use client"

import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectItem } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { produtosApi } from "@/lib/api/produtos"
import { categoriasApi } from "@/lib/api/categorias"
import { Produto, ProdutoCreate, ProdutoUpdate } from "@/types"
import { toast } from "sonner"

interface ProdutoFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  produto?: Produto
  onSuccess: () => void
}

export function ProdutoForm({
  open,
  onOpenChange,
  produto,
  onSuccess,
}: ProdutoFormProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState<ProdutoCreate>({
    codigo_barras: "",
    descricao: "",
    categoria_id: 0,
    preco_custo: 0,
    preco_venda: 0,
    estoque_atual: 0,
    estoque_minimo: 0,
    unidade: "UN",
    ncm: "",
    ativo: true,
  })

  // Load categorias
  const { data: categorias } = useQuery({
    queryKey: ["categorias"],
    queryFn: () => categoriasApi.listAll(),
  })

  // Load produto data when editing
  useEffect(() => {
    if (produto) {
      setFormData({
        codigo_barras: produto.codigo_barras,
        descricao: produto.descricao,
        categoria_id: produto.categoria_id,
        preco_custo: produto.preco_custo,
        preco_venda: produto.preco_venda,
        estoque_atual: produto.estoque_atual,
        estoque_minimo: produto.estoque_minimo,
        unidade: produto.unidade,
        ncm: produto.ncm || "",
        ativo: produto.ativo,
      })
    } else {
      // Reset form for new produto
      setFormData({
        codigo_barras: "",
        descricao: "",
        categoria_id: 0,
        preco_custo: 0,
        preco_venda: 0,
        estoque_atual: 0,
        estoque_minimo: 0,
        unidade: "UN",
        ncm: "",
        ativo: true,
      })
    }
  }, [produto, open])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      // Validate
      if (!formData.codigo_barras || !formData.descricao) {
        toast.error("Preencha os campos obrigatórios")
        setIsLoading(false)
        return
      }

      if (formData.categoria_id === 0) {
        toast.error("Selecione uma categoria")
        setIsLoading(false)
        return
      }

      if (formData.preco_venda <= 0) {
        toast.error("Preço de venda deve ser maior que zero")
        setIsLoading(false)
        return
      }

      if (produto) {
        // Update existing produto
        const updateData: ProdutoUpdate = {}
        Object.keys(formData).forEach((key) => {
          const k = key as keyof ProdutoCreate
          if (formData[k] !== undefined) {
            ;(updateData as any)[k] = formData[k]
          }
        })
        await produtosApi.update(produto.id, updateData)
        toast.success("Produto atualizado com sucesso!")
      } else {
        // Create new produto
        await produtosApi.create(formData)
        toast.success("Produto criado com sucesso!")
      }

      onSuccess()
      onOpenChange(false)
    } catch (error: any) {
      console.error("Erro ao salvar produto:", error)
      toast.error(
        error.response?.data?.detail || "Erro ao salvar produto"
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (field: keyof ProdutoCreate, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader onClose={() => onOpenChange(false)}>
          <DialogTitle>
            {produto ? "Editar Produto" : "Novo Produto"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Código de Barras */}
          <div className="space-y-2">
            <Label htmlFor="codigo_barras">
              Código de Barras <span className="text-red-500">*</span>
            </Label>
            <Input
              id="codigo_barras"
              value={formData.codigo_barras}
              onChange={(e) => handleChange("codigo_barras", e.target.value)}
              placeholder="Digite o código de barras"
              required
              disabled={isLoading}
            />
          </div>

          {/* Descrição */}
          <div className="space-y-2">
            <Label htmlFor="descricao">
              Descrição <span className="text-red-500">*</span>
            </Label>
            <Input
              id="descricao"
              value={formData.descricao}
              onChange={(e) => handleChange("descricao", e.target.value)}
              placeholder="Digite a descrição do produto"
              required
              disabled={isLoading}
            />
          </div>

          {/* Categoria */}
          <div className="space-y-2">
            <Label htmlFor="categoria">
              Categoria <span className="text-red-500">*</span>
            </Label>
            <Select
              value={formData.categoria_id}
              onValueChange={(value) =>
                handleChange("categoria_id", parseInt(value))
              }
              disabled={isLoading}
            >
              {categorias?.map((categoria) => (
                <SelectItem
                  key={categoria.id}
                  value={categoria.id.toString()}
                >
                  {categoria.nome}
                </SelectItem>
              ))}
            </Select>
          </div>

          {/* Preços */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="preco_custo">Preço Custo</Label>
              <Input
                id="preco_custo"
                type="number"
                step="0.01"
                min="0"
                value={formData.preco_custo}
                onChange={(e) =>
                  handleChange("preco_custo", parseFloat(e.target.value) || 0)
                }
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="preco_venda">
                Preço Venda <span className="text-red-500">*</span>
              </Label>
              <Input
                id="preco_venda"
                type="number"
                step="0.01"
                min="0.01"
                value={formData.preco_venda}
                onChange={(e) =>
                  handleChange("preco_venda", parseFloat(e.target.value) || 0)
                }
                required
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Estoque */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="estoque_atual">Estoque Atual</Label>
              <Input
                id="estoque_atual"
                type="number"
                step="0.01"
                min="0"
                value={formData.estoque_atual}
                onChange={(e) =>
                  handleChange("estoque_atual", parseFloat(e.target.value) || 0)
                }
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="estoque_minimo">Estoque Mínimo</Label>
              <Input
                id="estoque_minimo"
                type="number"
                step="0.01"
                min="0"
                value={formData.estoque_minimo}
                onChange={(e) =>
                  handleChange(
                    "estoque_minimo",
                    parseFloat(e.target.value) || 0
                  )
                }
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Unidade e NCM */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="unidade">Unidade</Label>
              <Select
                value={formData.unidade}
                onValueChange={(value) => handleChange("unidade", value)}
                disabled={isLoading}
              >
                <SelectItem value="UN">Unidade</SelectItem>
                <SelectItem value="CX">Caixa</SelectItem>
                <SelectItem value="PC">Peça</SelectItem>
                <SelectItem value="KG">Quilograma</SelectItem>
                <SelectItem value="M">Metro</SelectItem>
                <SelectItem value="M2">Metro Quadrado</SelectItem>
                <SelectItem value="M3">Metro Cúbico</SelectItem>
                <SelectItem value="L">Litro</SelectItem>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="ncm">NCM</Label>
              <Input
                id="ncm"
                value={formData.ncm}
                onChange={(e) => handleChange("ncm", e.target.value)}
                placeholder="00000000"
                maxLength={8}
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Ativo */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="ativo"
              checked={formData.ativo}
              onChange={(e) => handleChange("ativo", e.target.checked)}
              disabled={isLoading}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="ativo" className="cursor-pointer">
              Produto ativo
            </Label>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Salvando...
                </>
              ) : (
                "Salvar"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
