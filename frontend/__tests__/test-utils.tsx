import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Create a custom render function that includes providers
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })

interface AllTheProvidersProps {
  children: React.ReactNode
}

const AllTheProviders = ({ children }: AllTheProvidersProps) => {
  const testQueryClient = createTestQueryClient()

  return (
    <QueryClientProvider client={testQueryClient}>
      {children}
    </QueryClientProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

// Re-export everything
export * from '@testing-library/react'
export { customRender as render }

// Mock user data for tests
export const mockUser = {
  id: 1,
  email: 'test@example.com',
  nome: 'Test User',
  role: {
    id: 1,
    name: 'Admin',
    permissions: [
      { id: 1, name: 'produtos.view', description: 'Ver produtos' },
      { id: 2, name: 'produtos.create', description: 'Criar produtos' },
      { id: 3, name: 'produtos.update', description: 'Atualizar produtos' },
      { id: 4, name: 'produtos.delete', description: 'Deletar produtos' },
      { id: 5, name: 'vendas.view', description: 'Ver vendas' },
      { id: 6, name: 'vendas.create', description: 'Criar vendas' },
      { id: 7, name: 'vendas.update', description: 'Atualizar vendas' },
      { id: 8, name: 'vendas.cancel', description: 'Cancelar vendas' },
      { id: 9, name: 'estoque.view', description: 'Ver estoque' },
      { id: 10, name: 'estoque.create', description: 'Criar movimentações' },
      { id: 11, name: 'financeiro.view', description: 'Ver financeiro' },
      { id: 12, name: 'financeiro.update', description: 'Atualizar financeiro' },
    ],
  },
}

export const mockVendedor = {
  id: 2,
  email: 'vendedor@example.com',
  nome: 'Vendedor Test',
  role: {
    id: 2,
    name: 'Vendedor',
    permissions: [
      { id: 1, name: 'produtos.view', description: 'Ver produtos' },
      { id: 5, name: 'vendas.view', description: 'Ver vendas' },
      { id: 6, name: 'vendas.create', description: 'Criar vendas' },
    ],
  },
}

export const mockEstoquista = {
  id: 3,
  email: 'estoquista@example.com',
  nome: 'Estoquista Test',
  role: {
    id: 3,
    name: 'Estoquista',
    permissions: [
      { id: 1, name: 'produtos.view', description: 'Ver produtos' },
      { id: 9, name: 'estoque.view', description: 'Ver estoque' },
      { id: 10, name: 'estoque.create', description: 'Criar movimentações' },
    ],
  },
}
