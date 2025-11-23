/**
 * Schema de validação para Pedidos de Venda usando Zod
 */
import { z } from 'zod'

export const itemPedidoSchema = z.object({
  produto_id: z.number({
    required_error: 'Produto é obrigatório',
  }).positive('Produto inválido'),

  quantidade: z.number({
    required_error: 'Quantidade é obrigatória',
  }).positive('Quantidade deve ser maior que zero'),

  preco_unitario: z.number({
    required_error: 'Preço unitário é obrigatório',
  }).positive('Preço deve ser maior que zero'),

  desconto_item: z.number()
    .min(0, 'Desconto não pode ser negativo')
    .default(0),

  observacao_item: z.string()
    .max(500, 'Observação limitada a 500 caracteres')
    .optional(),
})

export const pedidoVendaCreateSchema = z.object({
  cliente_id: z.number({
    required_error: 'Cliente é obrigatório',
  }).positive('Cliente inválido'),

  orcamento_id: z.number().positive().optional(),

  data_entrega_prevista: z.string({
    required_error: 'Data de entrega prevista é obrigatória',
  }).refine((date) => {
    const entrega = new Date(date)
    const hoje = new Date()
    hoje.setHours(0, 0, 0, 0)
    return entrega >= hoje
  }, 'Data de entrega não pode ser no passado'),

  tipo_entrega: z.enum(['RETIRADA', 'ENTREGA', 'TRANSPORTADORA'], {
    required_error: 'Tipo de entrega é obrigatório',
  }),

  endereco_entrega: z.string()
    .max(500, 'Endereço limitado a 500 caracteres')
    .optional()
    .refine((val, ctx) => {
      // Se tipo_entrega for ENTREGA, endereco é obrigatório
      const tipoEntrega = (ctx as any).parent?.tipo_entrega
      if (tipoEntrega === 'ENTREGA' && !val) {
        return false
      }
      return true
    }, 'Endereço de entrega é obrigatório quando tipo é ENTREGA'),

  desconto: z.number()
    .min(0, 'Desconto não pode ser negativo')
    .default(0),

  valor_frete: z.number()
    .min(0, 'Valor do frete não pode ser negativo')
    .default(0),

  outras_despesas: z.number()
    .min(0, 'Outras despesas não podem ser negativas')
    .default(0),

  condicao_pagamento_id: z.number().positive().optional(),

  forma_pagamento: z.string()
    .max(50, 'Forma de pagamento limitada a 50 caracteres')
    .optional(),

  observacoes: z.string()
    .max(500, 'Observações limitadas a 500 caracteres')
    .optional(),

  itens: z.array(itemPedidoSchema)
    .min(1, 'Pedido deve ter pelo menos um item')
    .max(200, 'Pedido limitado a 200 itens'),
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

export const pedidoVendaUpdateSchema = pedidoVendaCreateSchema
  .partial()
  .omit({ itens: true, cliente_id: true })

export const confirmarPedidoSchema = z.object({
  observacao: z.string()
    .max(500, 'Observação limitada a 500 caracteres')
    .optional(),
})

export const separarPedidoSchema = z.object({
  itens_separados: z.array(
    z.object({
      produto_id: z.number().positive(),
      quantidade_separada: z.number().positive(),
    })
  ).min(1, 'Deve separar pelo menos um item'),
})

export const faturarPedidoSchema = z.object({
  gerar_nfe: z.boolean().default(false),
  observacao: z.string()
    .max(500, 'Observação limitada a 500 caracteres')
    .optional(),
})

export const cancelarPedidoSchema = z.object({
  motivo: z.string({
    required_error: 'Motivo do cancelamento é obrigatório',
  }).min(10, 'Motivo deve ter pelo menos 10 caracteres')
    .max(500, 'Motivo limitado a 500 caracteres'),
})

export type PedidoVendaCreateInput = z.infer<typeof pedidoVendaCreateSchema>
export type PedidoVendaUpdateInput = z.infer<typeof pedidoVendaUpdateSchema>
export type ItemPedidoInput = z.infer<typeof itemPedidoSchema>
export type ConfirmarPedidoInput = z.infer<typeof confirmarPedidoSchema>
export type SepararPedidoInput = z.infer<typeof separarPedidoSchema>
export type FaturarPedidoInput = z.infer<typeof faturarPedidoSchema>
export type CancelarPedidoInput = z.infer<typeof cancelarPedidoSchema>
