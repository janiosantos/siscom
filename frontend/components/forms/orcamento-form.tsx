'use client'

import { useState } from 'react'
import { useForm, useFieldArray } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Plus, Trash2, Save, X } from 'lucide-react'
import { orcamentoCreateSchema, type OrcamentoCreateInput } from '@/lib/validations/orcamento-schema'
import { criarOrcamento, atualizarOrcamento } from '@/lib/hooks/use-orcamentos'
import { useToast } from '@/components/ui/use-toast'

interface OrcamentoFormProps {
  orcamentoId?: number
  initialData?: Partial<OrcamentoCreateInput>
  onSuccess?: (orcamento: any) => void
  onCancel?: () => void
}

export function OrcamentoForm({
  orcamentoId,
  initialData,
  onSuccess,
  onCancel,
}: OrcamentoFormProps) {
  const { toast } = useToast()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm<OrcamentoCreateInput>({
    resolver: zodResolver(orcamentoCreateSchema),
    defaultValues: initialData || {
      cliente_id: 0,
      vendedor_id: 1,
      data_validade: '',
      desconto: 0,
      outras_despesas: 0,
      observacoes: '',
      itens: [
        {
          produto_id: 0,
          quantidade: 1,
          preco_unitario: 0,
          desconto_item: 0,
          observacao_item: '',
        },
      ],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'itens',
  })

  const calcularSubtotal = () => {
    const itens = form.watch('itens')
    return itens.reduce((sum, item) => {
      const subtotal = item.quantidade * item.preco_unitario
      return sum + (subtotal - item.desconto_item)
    }, 0)
  }

  const calcularTotal = () => {
    const subtotal = calcularSubtotal()
    const desconto = form.watch('desconto') || 0
    const outrasDespesas = form.watch('outras_despesas') || 0
    return subtotal - desconto + outrasDespesas
  }

  const onSubmit = async (data: OrcamentoCreateInput) => {
    setIsSubmitting(true)
    try {
      let result
      if (orcamentoId) {
        result = await atualizarOrcamento(orcamentoId, data)
        toast({
          title: 'Sucesso',
          description: 'Orçamento atualizado com sucesso',
        })
      } else {
        result = await criarOrcamento(data)
        toast({
          title: 'Sucesso',
          description: 'Orçamento criado com sucesso',
        })
      }

      if (onSuccess) {
        onSuccess(result)
      }
    } catch (error: any) {
      toast({
        title: 'Erro',
        description: error.message || 'Erro ao salvar orçamento',
        variant: 'destructive',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Informações Gerais */}
        <Card>
          <CardHeader>
            <CardTitle>Informações Gerais</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Cliente */}
              <FormField
                control={form.control}
                name="cliente_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cliente *</FormLabel>
                    <Select
                      onValueChange={(value) => field.onChange(parseInt(value))}
                      value={field.value?.toString()}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione o cliente" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="1">João Silva Construções</SelectItem>
                        <SelectItem value="2">Reforma Total Ltda</SelectItem>
                        <SelectItem value="3">Construtora ABC</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Vendedor */}
              <FormField
                control={form.control}
                name="vendedor_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Vendedor *</FormLabel>
                    <Select
                      onValueChange={(value) => field.onChange(parseInt(value))}
                      value={field.value?.toString()}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione o vendedor" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="1">Maria Santos</SelectItem>
                        <SelectItem value="2">Pedro Costa</SelectItem>
                        <SelectItem value="3">Ana Paula</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Data de Validade */}
              <FormField
                control={form.control}
                name="data_validade"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Data de Validade *</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormDescription>
                      Prazo de validade do orçamento
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Condição de Pagamento */}
              <FormField
                control={form.control}
                name="condicao_pagamento_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Condição de Pagamento</FormLabel>
                    <Select
                      onValueChange={(value) => field.onChange(parseInt(value))}
                      value={field.value?.toString()}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Selecione a condição" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="1">À Vista</SelectItem>
                        <SelectItem value="2">30 dias</SelectItem>
                        <SelectItem value="3">3x sem juros</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Observações */}
            <FormField
              control={form.control}
              name="observacoes"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Observações</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="Observações gerais do orçamento"
                      rows={3}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </CardContent>
        </Card>

        {/* Itens do Orçamento */}
        <Card>
          <CardHeader>
            <CardTitle>Itens do Orçamento</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {fields.map((field, index) => (
              <Card key={field.id} className="border-2">
                <CardContent className="pt-6">
                  <div className="flex justify-between items-center mb-4">
                    <h4 className="font-semibold">Item {index + 1}</h4>
                    {fields.length > 1 && (
                      <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        onClick={() => remove(index)}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Remover
                      </Button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Produto */}
                    <FormField
                      control={form.control}
                      name={`itens.${index}.produto_id`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Produto *</FormLabel>
                          <Select
                            onValueChange={(value) => field.onChange(parseInt(value))}
                            value={field.value?.toString()}
                          >
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Selecione" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="1">Cimento CP-II 50kg</SelectItem>
                              <SelectItem value="2">Areia Média m³</SelectItem>
                              <SelectItem value="3">Tijolo Baiano</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Quantidade */}
                    <FormField
                      control={form.control}
                      name={`itens.${index}.quantidade`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Quantidade *</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              step="0.01"
                              {...field}
                              onChange={(e) => field.onChange(parseFloat(e.target.value))}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Preço Unitário */}
                    <FormField
                      control={form.control}
                      name={`itens.${index}.preco_unitario`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Preço Unit. *</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              step="0.01"
                              {...field}
                              onChange={(e) => field.onChange(parseFloat(e.target.value))}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    {/* Desconto */}
                    <FormField
                      control={form.control}
                      name={`itens.${index}.desconto_item`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Desconto</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              step="0.01"
                              {...field}
                              onChange={(e) => field.onChange(parseFloat(e.target.value))}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  {/* Observação do Item */}
                  <FormField
                    control={form.control}
                    name={`itens.${index}.observacao_item`}
                    render={({ field }) => (
                      <FormItem className="mt-4">
                        <FormLabel>Observação do Item</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="Observações específicas do item" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Subtotal do Item */}
                  <div className="mt-4 text-right">
                    <span className="text-sm font-medium">
                      Subtotal: R${' '}
                      {(
                        form.watch(`itens.${index}.quantidade`) *
                          form.watch(`itens.${index}.preco_unitario`) -
                        form.watch(`itens.${index}.desconto_item`)
                      ).toFixed(2)}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}

            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={() =>
                append({
                  produto_id: 0,
                  quantidade: 1,
                  preco_unitario: 0,
                  desconto_item: 0,
                  observacao_item: '',
                })
              }
            >
              <Plus className="h-4 w-4 mr-2" />
              Adicionar Item
            </Button>
          </CardContent>
        </Card>

        {/* Totalizadores */}
        <Card>
          <CardHeader>
            <CardTitle>Totalizadores</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Desconto Geral */}
              <FormField
                control={form.control}
                name="desconto"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Desconto Geral</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        {...field}
                        onChange={(e) => field.onChange(parseFloat(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Outras Despesas */}
              <FormField
                control={form.control}
                name="outras_despesas"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Outras Despesas</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        {...field}
                        onChange={(e) => field.onChange(parseFloat(e.target.value))}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Resumo de Valores */}
            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Subtotal dos Itens:</span>
                <span className="font-medium">R$ {calcularSubtotal().toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Desconto Geral:</span>
                <span className="font-medium text-red-600">
                  - R$ {(form.watch('desconto') || 0).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Outras Despesas:</span>
                <span className="font-medium">
                  + R$ {(form.watch('outras_despesas') || 0).toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-lg font-bold border-t pt-2">
                <span>VALOR TOTAL:</span>
                <span className="text-primary">R$ {calcularTotal().toFixed(2)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Botões de Ação */}
        <div className="flex justify-end gap-4">
          {onCancel && (
            <Button type="button" variant="outline" onClick={onCancel}>
              <X className="h-4 w-4 mr-2" />
              Cancelar
            </Button>
          )}
          <Button type="submit" disabled={isSubmitting}>
            <Save className="h-4 w-4 mr-2" />
            {isSubmitting ? 'Salvando...' : orcamentoId ? 'Atualizar' : 'Salvar'}
          </Button>
        </div>
      </form>
    </Form>
  )
}
