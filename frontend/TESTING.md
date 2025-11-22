# Guia de Testes - Frontend

## 📋 Visão Geral

Este projeto utiliza **Jest** e **React Testing Library** para testes unitários e de integração do frontend Next.js.

### Stack de Testes

- **Jest**: Framework de testes
- **React Testing Library**: Testes de componentes React
- **@testing-library/user-event**: Simulação de interações do usuário
- **@testing-library/jest-dom**: Matchers customizados para Jest

## 🚀 Executar Testes

```bash
# Executar todos os testes
npm test

# Executar testes em modo watch
npm run test:watch

# Executar com cobertura
npm run test:coverage

# Executar no CI
npm run test:ci
```

## 📁 Estrutura de Testes

```
frontend/
├── __tests__/
│   └── test-utils.tsx          # Helpers e utilidades de teste
├── components/
│   ├── auth/
│   │   └── __tests__/
│   │       ├── permission-guard.test.tsx
│   │       └── protected-page.test.tsx
│   ├── navigation/
│   │   └── __tests__/
│   │       ├── sidebar.test.tsx
│   │       └── header.test.tsx
│   └── ui/
│       └── __tests__/
│           ├── button.test.tsx
│           ├── card.test.tsx
│           └── input.test.tsx
├── hooks/
│   └── __tests__/
│       └── usePermissions.test.ts
└── lib/
    └── __tests__/
        ├── utils.test.ts
        └── pdf-export.test.ts
```

## 📝 Convenções de Nomenclatura

### Arquivos de Teste

- Colocar testes no diretório `__tests__` dentro do módulo
- Nomenclatura: `[nome-do-arquivo].test.tsx` ou `[nome-do-arquivo].test.ts`
- Exemplo: `button.test.tsx`, `usePermissions.test.ts`

### Blocos de Teste

```typescript
describe('ComponentName', () => {
  describe('Feature/Functionality', () => {
    it('should do something specific', () => {
      // Test implementation
    })
  })
})
```

## 🛠️ Utilitários de Teste

### Test Utils (`__tests__/test-utils.tsx`)

Fornece helpers customizados e dados mock:

```typescript
import { render, screen } from '@/__tests__/test-utils'
import { mockUser, mockVendedor, mockEstoquista } from '@/__tests__/test-utils'

// Usar render customizado (com providers)
render(<Component />)

// Usar dados mock
mockUseUserStore.mockReturnValue({ user: mockUser, setUser: jest.fn(), logout: jest.fn() })
```

### Dados Mock Disponíveis

- **mockUser**: Usuário Admin com todas as permissões
- **mockVendedor**: Usuário Vendedor (permissões limitadas)
- **mockEstoquista**: Usuário Estoquista (permissões de estoque)

## 🧪 Exemplos de Testes

### Teste de Componente Simples

```typescript
import { render, screen } from '@/__tests__/test-utils'
import { Button } from '../button'

describe('Button', () => {
  it('should render correctly', () => {
    render(<Button>Click me</Button>)

    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('should handle click events', () => {
    const handleClick = jest.fn()
    render(<Button onClick={handleClick}>Click</Button>)

    fireEvent.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledTimes(1)
  })
})
```

### Teste com Permissões

```typescript
import { render, screen } from '@/__tests__/test-utils'
import { PermissionGuard } from '../permission-guard'
import { useUserStore } from '@/lib/store/user'
import { mockUser, mockVendedor } from '@/__tests__/test-utils'

jest.mock('@/lib/store/user')

const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('PermissionGuard', () => {
  it('should render when user has permission', () => {
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: jest.fn()
    })

    render(
      <PermissionGuard permission="produtos.view">
        <div>Protected Content</div>
      </PermissionGuard>
    )

    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('should not render when user lacks permission', () => {
    mockUseUserStore.mockReturnValue({
      user: mockVendedor,
      setUser: jest.fn(),
      logout: jest.fn()
    })

    render(
      <PermissionGuard permission="produtos.delete">
        <div>Protected Content</div>
      </PermissionGuard>
    )

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })
})
```

### Teste de Hook

```typescript
import { renderHook } from '@testing-library/react'
import { usePermission } from '../usePermissions'
import { useUserStore } from '@/lib/store/user'
import { mockUser } from '@/__tests__/test-utils'

jest.mock('@/lib/store/user')

const mockUseUserStore = useUserStore as jest.MockedFunction<typeof useUserStore>

describe('usePermission', () => {
  it('should return true when user has permission', () => {
    mockUseUserStore.mockReturnValue({
      user: mockUser,
      setUser: jest.fn(),
      logout: jest.fn()
    })

    const { result } = renderHook(() => usePermission('produtos.view'))

    expect(result.current).toBe(true)
  })
})
```

### Teste de Interações do Usuário

```typescript
import { render, screen, fireEvent } from '@/__tests__/test-utils'
import userEvent from '@testing-library/user-event'

describe('LoginForm', () => {
  it('should submit form with user input', async () => {
    const user = userEvent.setup()
    const handleSubmit = jest.fn()

    render(<LoginForm onSubmit={handleSubmit} />)

    // Digitar no campo de email
    await user.type(screen.getByLabelText(/email/i), 'test@example.com')

    // Digitar no campo de senha
    await user.type(screen.getByLabelText(/senha/i), 'password123')

    // Clicar no botão
    await user.click(screen.getByRole('button', { name: /entrar/i }))

    expect(handleSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123'
    })
  })
})
```

## 🎯 Boas Práticas

### 1. Testar Comportamento, Não Implementação

```typescript
// ❌ Ruim - Testa detalhes de implementação
expect(wrapper.find('.button-class')).toHaveLength(1)

// ✅ Bom - Testa comportamento do usuário
expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument()
```

### 2. Usar Queries Corretas

Ordem de prioridade (do mais acessível ao menos):

1. **getByRole**: `getByRole('button', { name: /submit/i })`
2. **getByLabelText**: `getByLabelText(/email/i)`
3. **getByPlaceholderText**: `getByPlaceholderText(/enter email/i)`
4. **getByText**: `getByText(/welcome/i)`
5. **getByTestId**: `getByTestId('custom-element')` (último recurso)

### 3. Usar Matchers Semânticos

```typescript
// ✅ Bom
expect(element).toBeInTheDocument()
expect(element).toBeVisible()
expect(element).toBeDisabled()
expect(element).toHaveClass('active')
expect(element).toHaveAttribute('href', '/home')
```

### 4. Limpar Mocks

```typescript
describe('Component', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })
})
```

### 5. Testar Estados de Erro

```typescript
it('should display error message when API fails', async () => {
  // Mock API error
  mockApi.getProdutos.mockRejectedValue(new Error('Network error'))

  render(<ProdutosList />)

  await waitFor(() => {
    expect(screen.getByText(/erro ao carregar produtos/i)).toBeInTheDocument()
  })
})
```

### 6. Testar Casos Extremos

```typescript
it('should handle empty list', () => {
  render(<ProdutosList produtos={[]} />)
  expect(screen.getByText(/nenhum produto encontrado/i)).toBeInTheDocument()
})

it('should handle null user', () => {
  mockUseUserStore.mockReturnValue({ user: null, setUser: jest.fn(), logout: jest.fn() })
  render(<Component />)
  // Assert expected behavior
})
```

## 📊 Cobertura de Código

### Meta de Cobertura

```javascript
// jest.config.js
coverageThreshold: {
  global: {
    branches: 70,
    functions: 70,
    lines: 70,
    statements: 70,
  },
}
```

### Visualizar Cobertura

```bash
npm run test:coverage
```

Relatório HTML será gerado em `coverage/lcov-report/index.html`.

### Arquivos Ignorados

- `*.d.ts` - Type definitions
- `node_modules/`
- `.next/`
- `jest.config.js`

## 🔧 Configuração

### jest.config.js

```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'app/**/*.{js,jsx,ts,tsx}',
    'components/**/*.{js,jsx,ts,tsx}',
    'hooks/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
  ],
}

module.exports = createJestConfig(customJestConfig)
```

### jest.setup.js

Configurações globais:
- Mocks de `next/navigation`
- Mocks de `next/image`
- Polyfills (IntersectionObserver, ResizeObserver, matchMedia)

## 🐛 Troubleshooting

### Problema: "Cannot find module '@/components/...'"

**Solução**: Verificar `moduleNameMapper` em `jest.config.js`

### Problema: "window is not defined"

**Solução**: Adicionar polyfill em `jest.setup.js` ou usar `testEnvironment: 'jsdom'`

### Problema: "Cannot access 'X' before initialization"

**Solução**: Mover imports de mocks para antes dos imports do componente

### Problema: Testes assíncronos não finalizam

**Solução**: Usar `waitFor`, `findBy*` queries ou retornar promises

```typescript
// ✅ Correto
await waitFor(() => {
  expect(screen.getByText('Data loaded')).toBeInTheDocument()
})

// ou
const element = await screen.findByText('Data loaded')
expect(element).toBeInTheDocument()
```

## 📚 Recursos Adicionais

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [Common Mistakes](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

## ✅ Checklist de Testes

Ao criar um novo componente:

- [ ] Testes de renderização básica
- [ ] Testes de props
- [ ] Testes de eventos (onClick, onChange, etc.)
- [ ] Testes de estados (loading, error, success)
- [ ] Testes de permissões (se aplicável)
- [ ] Testes de edge cases (null, undefined, empty)
- [ ] Testes de acessibilidade básica

Ao criar um novo hook:

- [ ] Testes de retorno padrão
- [ ] Testes de diferentes inputs
- [ ] Testes de edge cases
- [ ] Testes de estados internos
- [ ] Testes de efeitos colaterais

---

**Última atualização**: 2025-11-22
