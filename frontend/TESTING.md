# Guia de Testes - Frontend

## 📋 Visão Geral

Este projeto utiliza uma **suite completa de testes** com múltiplas ferramentas para garantir qualidade, acessibilidade e funcionamento correto do frontend Next.js.

### Stack de Testes Completa

#### Testes Unitários e de Componentes
- **Jest**: Framework de testes
- **React Testing Library**: Testes de componentes React
- **@testing-library/user-event**: Simulação de interações do usuário
- **@testing-library/jest-dom**: Matchers customizados para Jest

#### Testes de Integração com API
- **MSW (Mock Service Worker)**: Mock de APIs REST
- Handlers customizados para endpoints do backend
- Testes de integração completos

#### Testes E2E (End-to-End)
- **Playwright**: Testes end-to-end em múltiplos navegadores
- Suporte para Chrome, Firefox, Safari, Mobile
- Testes de fluxos completos de usuário

#### Testes de Acessibilidade
- **jest-axe**: Testes automatizados de acessibilidade
- **@axe-core/react**: Validação de WCAG 2.1
- Testes de navegação por teclado

#### Validação Local (CI/CD)
- **Script de validação local**: Similar ao backend
- 13 verificações automáticas
- Detecta erros antes do push

## 🚀 Executar Testes

### Testes Unitários e de Integração (Jest)

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

### Testes E2E (Playwright)

```bash
# Executar todos os testes E2E
npm run test:e2e

# Executar com UI interativa
npm run test:e2e:ui

# Executar com debug
npm run test:e2e:debug

# Ver relatório de testes
npm run test:e2e:report
```

### Executar Todos os Testes

```bash
# Testes unitários + E2E
npm run test:all
```

### 🔥 Validação Local (RECOMENDADO)

**⭐ EXECUTE ANTES DE FAZER COMMIT/PUSH!**

```bash
# Executar validação completa local
npm run validate:local

# Ou diretamente:
bash scripts/validate_frontend_local.sh
```

Este script executa **13 verificações** que o CI/CD também executa, permitindo detectar erros **ANTES** de fazer push!

## 📁 Estrutura de Testes

```
frontend/
├── __tests__/
│   ├── test-utils.tsx          # Helpers e utilidades de teste
│   └── mocks/
│       ├── handlers.ts          # MSW handlers (mock de API)
│       └── server.ts            # MSW server setup
│
├── app/
│   └── (dashboard)/
│       ├── produtos/
│       │   └── __tests__/
│       │       └── page.test.tsx
│       ├── vendas/
│       │   └── __tests__/
│       │       └── page.test.tsx
│       ├── estoque/
│       │   └── __tests__/
│       │       └── page.test.tsx
│       └── financeiro/
│           └── __tests__/
│               └── page.test.tsx
│
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
│
├── hooks/
│   └── __tests__/
│       └── usePermissions.test.ts
│
├── lib/
│   └── __tests__/
│       ├── utils.test.ts
│       └── pdf-export.test.ts
│
├── e2e/
│   ├── auth.spec.ts             # Testes E2E de autenticação
│   ├── produtos.spec.ts         # Testes E2E de produtos
│   └── vendas.spec.ts           # Testes E2E de vendas
│
├── scripts/
│   └── validate_frontend_local.sh  # Script de validação local
│
├── jest.config.js               # Configuração do Jest
├── jest.setup.js                # Setup global do Jest
└── playwright.config.ts         # Configuração do Playwright
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

## 🌐 Testes de Integração com API (MSW)

### O que é MSW?

**MSW (Mock Service Worker)** intercepta requisições HTTP e retorna respostas mockadas, permitindo testar integrações com API sem depender do backend real.

### Configuração

Os handlers MSW estão em `__tests__/mocks/handlers.ts`:

```typescript
import { http, HttpResponse } from 'msw'

export const handlers = [
  http.get('/api/v1/produtos', () => {
    return HttpResponse.json([
      { id: 1, codigo: 'CIM-001', descricao: 'Cimento' },
      { id: 2, codigo: 'ARE-001', descricao: 'Areia' },
    ])
  }),

  http.post('/api/v1/produtos', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({ id: 3, ...body }, { status: 201 })
  }),
]
```

### Exemplo de Teste com MSW

```typescript
import { render, screen, waitFor } from '@/__tests__/test-utils'
import ProdutosPage from '../page'

describe('ProdutosPage com API', () => {
  it('should load produtos from API', async () => {
    render(<ProdutosPage />)

    // MSW intercepta e retorna mock automaticamente
    await waitFor(() => {
      expect(screen.getByText('Cimento')).toBeInTheDocument()
      expect(screen.getByText('Areia')).toBeInTheDocument()
    })
  })

  it('should handle API error', async () => {
    const { server } = await import('@/__tests__/mocks/server')
    const { http, HttpResponse } = await import('msw')

    // Override handler para simular erro
    server.use(
      http.get('/api/v1/produtos', () => {
        return HttpResponse.json({ detail: 'Erro' }, { status: 500 })
      })
    )

    render(<ProdutosPage />)

    await waitFor(() => {
      expect(screen.getByText(/erro/i)).toBeInTheDocument()
    })
  })
})
```

### Dados Mock Disponíveis

Em `__tests__/mocks/handlers.ts`:

- `mockProdutos` - Lista de produtos
- `mockVendas` - Lista de vendas
- `mockEstoque` - Dados de estoque
- `mockFinanceiro` - Dados financeiros
- `mockDashboardStats` - Estatísticas do dashboard

## 🎭 Testes E2E com Playwright

### O que são Testes E2E?

Testes **End-to-End** simulam um usuário real interagindo com a aplicação completa, do frontend ao backend.

### Configuração do Playwright

O Playwright está configurado em `playwright.config.ts` para testar em:
- Chrome, Firefox, Safari (desktop)
- Mobile Chrome e Safari
- iPad

### Exemplo de Teste E2E

```typescript
// e2e/produtos.spec.ts
import { test, expect } from '@playwright/test'

test('should create new produto', async ({ page }) => {
  // Navegar para a página
  await page.goto('/produtos')

  // Login
  await page.getByLabel(/email/i).fill('admin@siscom.com')
  await page.getByLabel(/senha/i).fill('admin123')
  await page.getByRole('button', { name: /entrar/i }).click()

  // Criar produto
  await page.getByRole('button', { name: /novo produto/i }).click()
  await page.getByLabel(/código/i).fill('TEST-001')
  await page.getByLabel(/descrição/i).fill('Produto Teste')
  await page.getByRole('button', { name: /salvar/i }).click()

  // Verificar sucesso
  await expect(page.getByText('TEST-001')).toBeVisible()
})
```

### Executar Testes E2E

```bash
# Todos os testes em todos os navegadores
npm run test:e2e

# Com UI interativa (recomendado para debug)
npm run test:e2e:ui

# Apenas Chrome
npx playwright test --project=chromium

# Apenas Mobile
npx playwright test --project="Mobile Chrome"

# Modo debug
npm run test:e2e:debug
```

### Debug de Testes E2E

```bash
# Modo debug interativo
npx playwright test --debug

# Com UI mode (melhor opção)
npm run test:e2e:ui

# Ver trace de teste que falhou
npx playwright show-trace trace.zip
```

## ♿ Testes de Acessibilidade

### jest-axe

Todos os testes de página incluem validação de acessibilidade:

```typescript
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

describe('ProdutosPage', () => {
  it('should not have accessibility violations', async () => {
    const { container } = render(<ProdutosPage />)

    await waitFor(() => {
      expect(screen.getByText(/produtos/i)).toBeInTheDocument()
    })

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
```

### Testes de Navegação por Teclado

```typescript
it('should have keyboard navigation support', async () => {
  const { user } = render(<ProdutosPage />)

  const firstButton = screen.getAllByRole('button')[0]
  firstButton.focus()

  expect(document.activeElement).toBe(firstButton)

  // Tab para próximo elemento
  await user.tab()
  expect(document.activeElement).not.toBe(firstButton)
})
```

### Hierarquia de Headings

```typescript
it('should have proper heading hierarchy', async () => {
  render(<ProdutosPage />)

  const headings = screen.getAllByRole('heading')
  expect(headings.length).toBeGreaterThan(0)
  expect(headings[0].tagName).toBe('H1')
})
```

## 🔍 Script de Validação Local

### O que é?

Similar ao backend (`scripts/validate_ci_local.sh`), o frontend tem seu próprio script de validação que executa **TODAS** as verificações que o GitHub Actions faria.

### 13 Verificações Executadas

1. ✅ TypeScript Type Check
2. ✅ ESLint
3. ✅ Build do Next.js
4. ✅ Testes Jest com Cobertura
5. ✅ Testes E2E (opcional)
6. ✅ NPM Audit (vulnerabilidades)
7. ✅ Arquivos essenciais existem
8. ✅ Estrutura de pastas correta
9. ✅ Cobertura de testes adequada
10. ✅ Imports quebrados
11. ✅ console.log (limpeza)
12. ✅ Configuração MSW
13. ✅ Testes de acessibilidade

### Executar Validação

```bash
# Via npm script
npm run validate:local

# Diretamente
bash scripts/validate_frontend_local.sh
```

### Output do Script

```
🚀 Validação Local do Frontend - SISCOM
========================================

1️⃣  Verificação de Sintaxe e TypeScript
✅ TypeScript Type Check

2️⃣  Linting e Formatação
✅ ESLint

3️⃣  Build do Projeto
✅ Next.js Build

4️⃣  Testes Unitários e de Integração (Jest)
✅ Testes Jest com Cobertura

...

📊 RESUMO DA VALIDAÇÃO
Total de verificações: 13
Passou: 13
Falhou: 0

✅ TODAS AS VALIDAÇÕES PASSARAM!
Você pode fazer commit e push com segurança! 🚀
```

### Workflow Recomendado

```
1. Desenvolvimento Local
   ↓
2. npm run validate:local ⭐ (CRÍTICO)
   ↓
3. git commit && git push
   ↓
4. GitHub Actions (validação adicional)
```

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

## 📊 Resumo da Suite de Testes

### Tipos de Testes Implementados

| Tipo | Framework | Arquivos | Descrição |
|------|-----------|----------|-----------|
| **Unitários** | Jest + RTL | `**/*.test.tsx` | Componentes, hooks, utils |
| **Integração API** | MSW | `__tests__/mocks/` | Mocks de API REST |
| **E2E** | Playwright | `e2e/**/*.spec.ts` | Fluxos completos de usuário |
| **Acessibilidade** | jest-axe | Todos os testes de página | WCAG 2.1 compliance |
| **Visual (futuro)** | Percy/Chromatic | - | Regressão visual (planejado) |

### Cobertura de Testes Atual

```
Pages Testadas:
✅ Dashboard
✅ Produtos (unitário + E2E + acessibilidade)
✅ Vendas (unitário + E2E + acessibilidade)
✅ Estoque (unitário + acessibilidade)
✅ Financeiro (unitário + acessibilidade)
✅ PDV (E2E)

Components Testados:
✅ Auth (protected-page, permission-guard)
✅ Navigation (sidebar, header)
✅ UI (button, card, input)

Hooks Testados:
✅ usePermissions

Utils Testados:
✅ utils
✅ pdf-export
```

### Comandos Rápidos

```bash
# Desenvolvimento
npm test                    # Testes unitários
npm run test:watch          # Watch mode
npm run test:coverage       # Com cobertura

# E2E
npm run test:e2e            # Todos os navegadores
npm run test:e2e:ui         # UI interativa

# Validação Completa (antes de commit)
npm run validate:local      # ⭐ RECOMENDADO

# CI/CD
npm run test:ci             # Testes para CI
npm run test:all            # Todos os testes
```

### Próximos Passos (Roadmap)

- [ ] Adicionar visual regression testing com Percy ou Chromatic
- [ ] Aumentar cobertura de testes para > 80%
- [ ] Adicionar testes de performance com Lighthouse CI
- [ ] Testes de snapshot para componentes UI
- [ ] Testes de mutação com Stryker
- [ ] Integração com SonarQube para análise de qualidade

## 🎯 Metas de Qualidade

### Cobertura de Código

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

### Métricas de Sucesso

- ✅ **100%** das páginas principais com testes
- ✅ **100%** das páginas com testes de acessibilidade
- ✅ **Zero** violações de acessibilidade WCAG 2.1 AA
- ✅ Testes E2E para fluxos críticos (login, criar produto, venda)
- ✅ Script de validação local funcionando
- ⏳ **70%+** de cobertura de código (em progresso)

## 🆘 Troubleshooting

### MSW não está interceptando requisições

**Solução**: Verificar se `@/__tests__/mocks/server` está importado em `jest.setup.js`

```javascript
// jest.setup.js
import '@/__tests__/mocks/server'
```

### Playwright não consegue iniciar

**Solução**: Instalar navegadores

```bash
npx playwright install
```

### Testes E2E timeout

**Solução**: Aumentar timeout no `playwright.config.ts`

```typescript
use: {
  timeout: 60 * 1000, // 60 segundos
}
```

### jest-axe mostrando violações

**Solução**: Revisar elementos com problemas de acessibilidade:

```typescript
// Ver detalhes das violações
const results = await axe(container)
console.log(results.violations)
```

### Script de validação falhando

**Solução**: Executar checks individuais para identificar o problema:

```bash
npm run type-check
npm run lint
npm run build
npm test
```

## 📚 Recursos Adicionais

### Documentação Oficial

- [Jest](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright](https://playwright.dev/docs/intro)
- [MSW](https://mswjs.io/docs/)
- [jest-axe](https://github.com/nickcolley/jest-axe)

### Guias e Best Practices

- [Testing Library Queries](https://testing-library.com/docs/queries/about)
- [Common Mistakes with RTL](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### Scripts Backend Relacionados

Similar ao frontend, o backend também tem validação local:

```bash
# Backend (na raiz do projeto)
bash scripts/validate_ci_local.sh
```

---

**Última atualização**: 2025-11-22

**Versão**: 2.0.0 (Suite Completa de Testes)

**Novas Funcionalidades**:
- ✅ Testes de integração com MSW
- ✅ Testes E2E com Playwright
- ✅ Testes de acessibilidade com jest-axe
- ✅ Script de validação local (13 checks)
- ✅ Testes para páginas: Produtos, Vendas, Estoque, Financeiro

**Arquivos Criados**:
- `__tests__/mocks/handlers.ts` - MSW handlers
- `__tests__/mocks/server.ts` - MSW server setup
- `e2e/auth.spec.ts` - Testes E2E de autenticação
- `e2e/produtos.spec.ts` - Testes E2E de produtos
- `e2e/vendas.spec.ts` - Testes E2E de vendas
- `app/(dashboard)/produtos/__tests__/page.test.tsx`
- `app/(dashboard)/vendas/__tests__/page.test.tsx`
- `app/(dashboard)/estoque/__tests__/page.test.tsx`
- `app/(dashboard)/financeiro/__tests__/page.test.tsx`
- `playwright.config.ts` - Configuração do Playwright
- `scripts/validate_frontend_local.sh` - Script de validação

**Total de Arquivos de Teste**: 20+ arquivos

**Comandos Principais**:
```bash
npm test                    # Testes unitários
npm run test:e2e            # Testes E2E
npm run validate:local      # Validação completa ⭐
```
