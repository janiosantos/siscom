/**
 * MSW (Mock Service Worker) Handlers
 *
 * Mocks de API para testes de integração
 */

import { http, HttpResponse } from 'msw'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

// Mock Data
export const mockProdutos = [
  {
    id: 1,
    codigo: 'CIM-001',
    descricao: 'Cimento CP-II 50kg',
    preco_venda: 32.90,
    categoria_id: 1,
    estoque_atual: 100,
    created_at: '2025-01-01T10:00:00',
    updated_at: '2025-01-01T10:00:00',
  },
  {
    id: 2,
    codigo: 'ARE-001',
    descricao: 'Areia Média m³',
    preco_venda: 85.00,
    categoria_id: 2,
    estoque_atual: 50,
    created_at: '2025-01-01T10:00:00',
    updated_at: '2025-01-01T10:00:00',
  },
]

export const mockVendas = [
  {
    id: 1,
    numero: 'VND-00001',
    cliente_id: 1,
    cliente_nome: 'João Silva',
    valor_total: 329.00,
    desconto: 0,
    valor_final: 329.00,
    status: 'finalizada',
    data_venda: '2025-01-15T14:30:00',
    items: [
      {
        id: 1,
        produto_id: 1,
        produto_descricao: 'Cimento CP-II 50kg',
        quantidade: 10,
        preco_unitario: 32.90,
        subtotal: 329.00,
      },
    ],
  },
  {
    id: 2,
    numero: 'VND-00002',
    cliente_id: 2,
    cliente_nome: 'Maria Santos',
    valor_total: 170.00,
    desconto: 10.00,
    valor_final: 160.00,
    status: 'finalizada',
    data_venda: '2025-01-16T10:15:00',
    items: [
      {
        id: 2,
        produto_id: 2,
        produto_descricao: 'Areia Média m³',
        quantidade: 2,
        preco_unitario: 85.00,
        subtotal: 170.00,
      },
    ],
  },
]

export const mockEstoque = [
  {
    id: 1,
    produto_id: 1,
    produto_codigo: 'CIM-001',
    produto_descricao: 'Cimento CP-II 50kg',
    quantidade_atual: 100,
    quantidade_minima: 20,
    quantidade_maxima: 200,
    localizacao: 'A1-01',
    ultima_movimentacao: '2025-01-15T14:30:00',
  },
  {
    id: 2,
    produto_id: 2,
    produto_codigo: 'ARE-001',
    produto_descricao: 'Areia Média m³',
    quantidade_atual: 50,
    quantidade_minima: 10,
    quantidade_maxima: 100,
    localizacao: 'B2-03',
    ultima_movimentacao: '2025-01-16T10:15:00',
  },
]

export const mockFinanceiro = {
  contas_receber: [
    {
      id: 1,
      descricao: 'Venda #VND-00001',
      venda_id: 1,
      valor: 329.00,
      valor_pago: 329.00,
      valor_pendente: 0,
      status: 'paga',
      data_vencimento: '2025-01-15',
      data_pagamento: '2025-01-15',
    },
    {
      id: 2,
      descricao: 'Venda #VND-00002',
      venda_id: 2,
      valor: 160.00,
      valor_pago: 0,
      valor_pendente: 160.00,
      status: 'pendente',
      data_vencimento: '2025-02-15',
      data_pagamento: null,
    },
  ],
  contas_pagar: [
    {
      id: 1,
      descricao: 'Fornecedor ABC - Compra #001',
      fornecedor_id: 1,
      valor: 5000.00,
      valor_pago: 5000.00,
      valor_pendente: 0,
      status: 'paga',
      data_vencimento: '2025-01-10',
      data_pagamento: '2025-01-10',
    },
  ],
  resumo: {
    total_receber: 489.00,
    total_recebido: 329.00,
    total_pendente_receber: 160.00,
    total_pagar: 5000.00,
    total_pago: 5000.00,
    total_pendente_pagar: 0,
    saldo_liquido: -4511.00,
  },
}

export const mockDashboardStats = {
  vendas_hoje: 489.00,
  vendas_mes: 15340.00,
  produtos_estoque_baixo: 5,
  pedidos_pendentes: 12,
  vendas_chart: [
    { data: '2025-01-01', valor: 1200 },
    { data: '2025-01-02', valor: 1500 },
    { data: '2025-01-03', valor: 1800 },
    { data: '2025-01-04', valor: 1400 },
    { data: '2025-01-05', valor: 2100 },
  ],
  produtos_mais_vendidos: [
    { produto: 'Cimento CP-II 50kg', quantidade: 120, valor: 3948.00 },
    { produto: 'Areia Média m³', quantidade: 85, valor: 7225.00 },
    { produto: 'Brita 1 m³', quantidade: 62, valor: 5890.00 },
  ],
}

// Handlers
export const handlers = [
  // Auth
  http.post(`${API_BASE_URL}/auth/login`, async () => {
    return HttpResponse.json({
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'Bearer',
      expires_in: 1800,
      user: {
        id: 1,
        username: 'admin',
        email: 'admin@siscom.com',
        role: {
          name: 'Admin',
          permissions: ['produtos.view', 'produtos.create', 'produtos.update', 'produtos.delete'],
        },
      },
    })
  }),

  // Produtos
  http.get(`${API_BASE_URL}/produtos`, () => {
    return HttpResponse.json(mockProdutos)
  }),

  http.get(`${API_BASE_URL}/produtos/:id`, ({ params }) => {
    const { id } = params
    const produto = mockProdutos.find((p) => p.id === Number(id))
    if (!produto) {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json(produto)
  }),

  http.post(`${API_BASE_URL}/produtos`, async ({ request }) => {
    const body = await request.json() as any
    const novoProduto = {
      id: mockProdutos.length + 1,
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    return HttpResponse.json(novoProduto, { status: 201 })
  }),

  http.put(`${API_BASE_URL}/produtos/:id`, async ({ params, request }) => {
    const { id } = params
    const body = await request.json() as any
    const produto = mockProdutos.find((p) => p.id === Number(id))
    if (!produto) {
      return new HttpResponse(null, { status: 404 })
    }
    const produtoAtualizado = {
      ...produto,
      ...body,
      updated_at: new Date().toISOString(),
    }
    return HttpResponse.json(produtoAtualizado)
  }),

  http.delete(`${API_BASE_URL}/produtos/:id`, ({ params }) => {
    const { id } = params
    const produto = mockProdutos.find((p) => p.id === Number(id))
    if (!produto) {
      return new HttpResponse(null, { status: 404 })
    }
    return new HttpResponse(null, { status: 204 })
  }),

  // Vendas
  http.get(`${API_BASE_URL}/vendas`, () => {
    return HttpResponse.json(mockVendas)
  }),

  http.get(`${API_BASE_URL}/vendas/:id`, ({ params }) => {
    const { id } = params
    const venda = mockVendas.find((v) => v.id === Number(id))
    if (!venda) {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json(venda)
  }),

  http.post(`${API_BASE_URL}/vendas`, async ({ request }) => {
    const body = await request.json() as any
    const novaVenda = {
      id: mockVendas.length + 1,
      numero: `VND-${String(mockVendas.length + 1).padStart(5, '0')}`,
      ...body,
      status: 'finalizada',
      data_venda: new Date().toISOString(),
    }
    return HttpResponse.json(novaVenda, { status: 201 })
  }),

  // Estoque
  http.get(`${API_BASE_URL}/estoque`, () => {
    return HttpResponse.json(mockEstoque)
  }),

  http.get(`${API_BASE_URL}/estoque/produto/:produto_id`, ({ params }) => {
    const { produto_id } = params
    const estoque = mockEstoque.find((e) => e.produto_id === Number(produto_id))
    if (!estoque) {
      return new HttpResponse(null, { status: 404 })
    }
    return HttpResponse.json(estoque)
  }),

  // Financeiro
  http.get(`${API_BASE_URL}/financeiro/resumo`, () => {
    return HttpResponse.json(mockFinanceiro)
  }),

  http.get(`${API_BASE_URL}/financeiro/contas-receber`, () => {
    return HttpResponse.json(mockFinanceiro.contas_receber)
  }),

  http.get(`${API_BASE_URL}/financeiro/contas-pagar`, () => {
    return HttpResponse.json(mockFinanceiro.contas_pagar)
  }),

  // Dashboard
  http.get(`${API_BASE_URL}/dashboard/stats`, () => {
    return HttpResponse.json(mockDashboardStats)
  }),
]
