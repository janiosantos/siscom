import {
  pedidoVendaCreateSchema,
  itemPedidoSchema,
  confirmarPedidoSchema,
  cancelarPedidoSchema,
} from '@/lib/validations/pedido-schema'

describe('Pedido de Venda Validation Schemas', () => {
  describe('itemPedidoSchema', () => {
    it('should validate valid item', () => {
      const validItem = {
        produto_id: 1,
        quantidade: 10,
        preco_unitario: 100.50,
        desconto_item: 5.00,
        observacao_item: 'Item de teste',
      }

      const result = itemPedidoSchema.safeParse(validItem)
      expect(result.success).toBe(true)
    })

    it('should reject negative quantity', () => {
      const invalidItem = {
        produto_id: 1,
        quantidade: -5,
        preco_unitario: 100,
        desconto_item: 0,
      }

      const result = itemPedidoSchema.safeParse(invalidItem)
      expect(result.success).toBe(false)
    })

    it('should reject zero price', () => {
      const invalidItem = {
        produto_id: 1,
        quantidade: 10,
        preco_unitario: 0,
        desconto_item: 0,
      }

      const result = itemPedidoSchema.safeParse(invalidItem)
      expect(result.success).toBe(false)
    })

    it('should reject negative discount', () => {
      const invalidItem = {
        produto_id: 1,
        quantidade: 10,
        preco_unitario: 100,
        desconto_item: -10,
      }

      const result = itemPedidoSchema.safeParse(invalidItem)
      expect(result.success).toBe(false)
    })
  })

  describe('pedidoVendaCreateSchema', () => {
    const validPedido = {
      cliente_id: 1,
      data_entrega_prevista: '2025-12-31',
      tipo_entrega: 'RETIRADA' as const,
      desconto: 0,
      valor_frete: 0,
      outras_despesas: 0,
      itens: [
        {
          produto_id: 1,
          quantidade: 10,
          preco_unitario: 100,
          desconto_item: 0,
        },
      ],
    }

    it('should validate valid pedido', () => {
      const result = pedidoVendaCreateSchema.safeParse(validPedido)
      expect(result.success).toBe(true)
    })

    it('should require at least one item', () => {
      const invalidPedido = {
        ...validPedido,
        itens: [],
      }

      const result = pedidoVendaCreateSchema.safeParse(invalidPedido)
      expect(result.success).toBe(false)
    })

    it('should reject past delivery date', () => {
      const invalidPedido = {
        ...validPedido,
        data_entrega_prevista: '2020-01-01',
      }

      const result = pedidoVendaCreateSchema.safeParse(invalidPedido)
      expect(result.success).toBe(false)
    })

    it('should require endereco_entrega when tipo_entrega is ENTREGA', () => {
      const pedidoComEntrega = {
        ...validPedido,
        tipo_entrega: 'ENTREGA' as const,
        endereco_entrega: 'Rua Teste, 123',
      }

      const result = pedidoVendaCreateSchema.safeParse(pedidoComEntrega)
      expect(result.success).toBe(true)
    })

    it('should reject discount greater than subtotal', () => {
      const invalidPedido = {
        ...validPedido,
        desconto: 2000, // Greater than subtotal (10 * 100 = 1000)
      }

      const result = pedidoVendaCreateSchema.safeParse(invalidPedido)
      expect(result.success).toBe(false)
    })

    it('should limit items to 200', () => {
      const tooManyItems = Array(201).fill({
        produto_id: 1,
        quantidade: 1,
        preco_unitario: 10,
        desconto_item: 0,
      })

      const invalidPedido = {
        ...validPedido,
        itens: tooManyItems,
      }

      const result = pedidoVendaCreateSchema.safeParse(invalidPedido)
      expect(result.success).toBe(false)
    })

    it('should accept valid tipo_entrega values', () => {
      const tipos = ['RETIRADA', 'ENTREGA', 'TRANSPORTADORA'] as const

      tipos.forEach((tipo) => {
        const pedido = {
          ...validPedido,
          tipo_entrega: tipo,
        }

        const result = pedidoVendaCreateSchema.safeParse(pedido)
        expect(result.success).toBe(true)
      })
    })

    it('should reject invalid tipo_entrega', () => {
      const invalidPedido = {
        ...validPedido,
        tipo_entrega: 'INVALID',
      }

      const result = pedidoVendaCreateSchema.safeParse(invalidPedido)
      expect(result.success).toBe(false)
    })
  })

  describe('confirmarPedidoSchema', () => {
    it('should validate with optional observacao', () => {
      const valid = { observacao: 'Confirmado pelo cliente' }
      const result = confirmarPedidoSchema.safeParse(valid)
      expect(result.success).toBe(true)
    })

    it('should validate without observacao', () => {
      const valid = {}
      const result = confirmarPedidoSchema.safeParse(valid)
      expect(result.success).toBe(true)
    })

    it('should reject observacao longer than 500 chars', () => {
      const invalid = { observacao: 'a'.repeat(501) }
      const result = confirmarPedidoSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })
  })

  describe('cancelarPedidoSchema', () => {
    it('should validate with valid motivo', () => {
      const valid = { motivo: 'Cliente solicitou cancelamento' }
      const result = cancelarPedidoSchema.safeParse(valid)
      expect(result.success).toBe(true)
    })

    it('should require motivo', () => {
      const invalid = {}
      const result = cancelarPedidoSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })

    it('should require motivo with at least 10 characters', () => {
      const invalid = { motivo: 'curto' }
      const result = cancelarPedidoSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })

    it('should reject motivo longer than 500 chars', () => {
      const invalid = { motivo: 'a'.repeat(501) }
      const result = cancelarPedidoSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })
  })
})
