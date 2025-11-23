import {
  orcamentoCreateSchema,
  itemOrcamentoSchema,
  aprovarOrcamentoSchema,
  converterOrcamentoSchema,
} from '@/lib/validations/orcamento-schema'

describe('Orçamento Validation Schemas', () => {
  describe('itemOrcamentoSchema', () => {
    it('should validate valid item', () => {
      const validItem = {
        produto_id: 1,
        quantidade: 10,
        preco_unitario: 50.00,
        desconto_item: 2.50,
        observacao_item: 'Item de teste',
      }

      const result = itemOrcamentoSchema.safeParse(validItem)
      expect(result.success).toBe(true)
    })

    it('should apply default desconto_item as 0', () => {
      const item = {
        produto_id: 1,
        quantidade: 10,
        preco_unitario: 50.00,
      }

      const result = itemOrcamentoSchema.safeParse(item)
      if (result.success) {
        expect(result.data.desconto_item).toBe(0)
      }
    })

    it('should reject invalid produto_id', () => {
      const invalidItem = {
        produto_id: 0,
        quantidade: 10,
        preco_unitario: 50.00,
        desconto_item: 0,
      }

      const result = itemOrcamentoSchema.safeParse(invalidItem)
      expect(result.success).toBe(false)
    })

    it('should limit observacao_item to 500 characters', () => {
      const invalidItem = {
        produto_id: 1,
        quantidade: 10,
        preco_unitario: 50.00,
        desconto_item: 0,
        observacao_item: 'a'.repeat(501),
      }

      const result = itemOrcamentoSchema.safeParse(invalidItem)
      expect(result.success).toBe(false)
    })
  })

  describe('orcamentoCreateSchema', () => {
    const validOrcamento = {
      cliente_id: 1,
      vendedor_id: 1,
      data_validade: '2025-12-31',
      desconto: 0,
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

    it('should validate valid orcamento', () => {
      const result = orcamentoCreateSchema.safeParse(validOrcamento)
      expect(result.success).toBe(true)
    })

    it('should require at least one item', () => {
      const invalidOrcamento = {
        ...validOrcamento,
        itens: [],
      }

      const result = orcamentoCreateSchema.safeParse(invalidOrcamento)
      expect(result.success).toBe(false)
    })

    it('should reject past data_validade', () => {
      const invalidOrcamento = {
        ...validOrcamento,
        data_validade: '2020-01-01',
      }

      const result = orcamentoCreateSchema.safeParse(invalidOrcamento)
      expect(result.success).toBe(false)
    })

    it('should reject discount greater than subtotal', () => {
      const invalidOrcamento = {
        ...validOrcamento,
        desconto: 2000, // Greater than subtotal (10 * 100 = 1000)
      }

      const result = orcamentoCreateSchema.safeParse(invalidOrcamento)
      expect(result.success).toBe(false)
    })

    it('should accept discount less than subtotal', () => {
      const validOrcamentoWithDiscount = {
        ...validOrcamento,
        desconto: 500, // Less than subtotal (10 * 100 = 1000)
      }

      const result = orcamentoCreateSchema.safeParse(validOrcamentoWithDiscount)
      expect(result.success).toBe(true)
    })

    it('should limit items to 200', () => {
      const tooManyItems = Array(201).fill({
        produto_id: 1,
        quantidade: 1,
        preco_unitario: 10,
        desconto_item: 0,
      })

      const invalidOrcamento = {
        ...validOrcamento,
        itens: tooManyItems,
      }

      const result = orcamentoCreateSchema.safeParse(invalidOrcamento)
      expect(result.success).toBe(false)
    })

    it('should apply default values', () => {
      const minimalOrcamento = {
        cliente_id: 1,
        vendedor_id: 1,
        data_validade: '2025-12-31',
        itens: [
          {
            produto_id: 1,
            quantidade: 1,
            preco_unitario: 10,
          },
        ],
      }

      const result = orcamentoCreateSchema.safeParse(minimalOrcamento)
      if (result.success) {
        expect(result.data.desconto).toBe(0)
        expect(result.data.outras_despesas).toBe(0)
      }
    })

    it('should reject negative outras_despesas', () => {
      const invalidOrcamento = {
        ...validOrcamento,
        outras_despesas: -10,
      }

      const result = orcamentoCreateSchema.safeParse(invalidOrcamento)
      expect(result.success).toBe(false)
    })

    it('should accept optional observacoes', () => {
      const orcamentoWithObs = {
        ...validOrcamento,
        observacoes: 'Orçamento com prazo diferenciado',
      }

      const result = orcamentoCreateSchema.safeParse(orcamentoWithObs)
      expect(result.success).toBe(true)
    })

    it('should limit observacoes to 500 characters', () => {
      const invalidOrcamento = {
        ...validOrcamento,
        observacoes: 'a'.repeat(501),
      }

      const result = orcamentoCreateSchema.safeParse(invalidOrcamento)
      expect(result.success).toBe(false)
    })
  })

  describe('aprovarOrcamentoSchema', () => {
    it('should validate with optional observacao', () => {
      const valid = { observacao: 'Aprovado pelo cliente em reunião' }
      const result = aprovarOrcamentoSchema.safeParse(valid)
      expect(result.success).toBe(true)
    })

    it('should validate without observacao', () => {
      const valid = {}
      const result = aprovarOrcamentoSchema.safeParse(valid)
      expect(result.success).toBe(true)
    })

    it('should reject observacao longer than 500 chars', () => {
      const invalid = { observacao: 'a'.repeat(501) }
      const result = aprovarOrcamentoSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })
  })

  describe('converterOrcamentoSchema', () => {
    it('should validate with optional pedido_venda_id', () => {
      const valid = { pedido_venda_id: 123 }
      const result = converterOrcamentoSchema.safeParse(valid)
      expect(result.success).toBe(true)
    })

    it('should validate without pedido_venda_id', () => {
      const valid = {}
      const result = converterOrcamentoSchema.safeParse(valid)
      expect(result.success).toBe(true)
    })

    it('should reject negative pedido_venda_id', () => {
      const invalid = { pedido_venda_id: -1 }
      const result = converterOrcamentoSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })

    it('should reject zero pedido_venda_id', () => {
      const invalid = { pedido_venda_id: 0 }
      const result = converterOrcamentoSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })
  })
})
