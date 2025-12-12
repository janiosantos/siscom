/**
 * Schema de validação para Orçamentos usando Zod
 */
import { z } from 'zod'

export const itemOrcamentoSchema = z.object({
  produto_id: z.number({ message: 'Produto é obrigatório' })
    .positive('Produto inválido'),

  quantidade: z.number({ message: 'Quantidade é obrigatória' })
    .positive('Quantidade deve ser maior que zero'),

  preco_unitario: z.number({ message: 'Preço unitário é obrigatório' })
    .positive('Preço deve ser maior que zero'),

  desconto_item: z.number().min(0, 'Desconto não pode ser negativo').default(0),
})

export const orcamentoCreateSchema = z.object({
  cliente_id: z.number({ message: 'Cliente é obrigatório' })
    .positive('Cliente inválido'),

  validade_dias: z.number({ message: 'Validade é obrigatória' })
    .int('Deve ser um número inteiro')
    .min(1, 'Validade deve ser no mínimo 1 dia')
    .max(365, 'Validade não pode exceder 365 dias')
    .default(7),

  desconto: z.number()
    .min(0, 'Desconto não pode ser negativo')
    .default(0),

  observacoes: z.string().max(500, 'Observações limitadas a 500 caracteres').optional(),

  itens: z.array(itemOrcamentoSchema)
    .min(1, 'Orçamento deve ter pelo menos um item')
    .max(100, 'Orçamento limitado a 100 itens'),
}).refine(
  (data) => {
    // Validação: desconto não pode ser maior que o subtotal
    const subtotal = data.itens.reduce((sum, item) => {
      return sum + (item.quantidade * item.preco_unitario - item.desconto_item)
    }, 0)
    return data.desconto <= subtotal
  },
  {
    message: 'Desconto não pode ser maior que o subtotal',
    path: ['desconto'],
  }
)

export const orcamentoUpdateSchema = orcamentoCreateSchema.partial().omit({ itens: true })

export const aprovarOrcamentoSchema = z.object({
  id: z.number({ message: 'ID do orçamento é obrigatório' }),
})

export const converterOrcamentoSchema = z.object({
  id: z.number({ message: 'ID do orçamento é obrigatório' }),
})

export type OrcamentoCreateInput = z.infer<typeof orcamentoCreateSchema>
export type OrcamentoUpdateInput = z.infer<typeof orcamentoUpdateSchema>
export type ItemOrcamentoInput = z.infer<typeof itemOrcamentoSchema>
