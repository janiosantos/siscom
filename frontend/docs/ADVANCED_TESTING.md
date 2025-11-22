# Guia de Testes Avançados - Frontend SISCOM

## 📋 Visão Geral

Este guia documenta as técnicas avançadas de teste implementadas no frontend do SISCOM, indo além dos testes básicos unitários e de integração.

## 🎨 Visual Regression Testing

### O Que É?

Visual Regression Testing detecta mudanças visuais não intencionais na UI comparando screenshots.

### Implementação

✅ **Playwright Screenshots** (Built-in, gratuito)
⏳ **Chromatic** (Opcional, pago)

### Executar Testes Visuais

```bash
# Gerar baselines (primeira vez)
npm run test:visual

# Executar testes visuais
npm run test:visual

# Atualizar baselines (após revisar mudanças)
npm run test:visual:update
```

### Tipos de Testes Visuais

```typescript
// Página completa
await expect(page).toHaveScreenshot('page.png', { fullPage: true })

// Componente específico
const button = page.getByRole('button')
await expect(button).toHaveScreenshot('button.png')

// Mobile
await page.setViewportSize({ width: 375, height: 667 })
await expect(page).toHaveScreenshot('mobile.png')

// Dark mode
await page.emulateMedia({ colorScheme: 'dark' })
await expect(page).toHaveScreenshot('dark.png')

// Hover state
await button.hover()
await expect(button).toHaveScreenshot('button-hover.png')
```

### Configuração

Veja `docs/VISUAL_REGRESSION.md` para detalhes completos.

## 📸 Snapshot Testing

### O Que É?

Snapshot Testing captura a estrutura renderizada de componentes e detecta mudanças não intencionais.

### Quando Usar?

- ✅ Componentes de UI estáveis
- ✅ Layouts complexos
- ✅ Componentes de design system
- ❌ Componentes com dados dinâmicos
- ❌ Testes de lógica de negócio

### Exemplo

```typescript
it('should match button snapshot', () => {
  const { container } = render(<Button>Click me</Button>)
  expect(container.firstChild).toMatchSnapshot()
})
```

### Atualizar Snapshots

```bash
# Atualizar todos os snapshots
npm test -- --updateSnapshot

# Atualizar snapshots específicos
npm test button.test.tsx -- --updateSnapshot
```

### Boas Práticas

1. **Revisar mudanças** antes de atualizar snapshots
2. **Não commitar** snapshots quebrados
3. **Usar `toMatchSnapshot()`** para estrutura HTML
4. **Usar `toMatchInlineSnapshot()`** para pequenas estruturas
5. **Ignorar** dados dinâmicos (timestamps, IDs)

## ⚡ Performance Testing

### Lighthouse CI

Lighthouse CI automatiza auditorias de performance, acessibilidade, SEO e best practices.

#### Executar

```bash
# Executar todas as auditorias
npm run lighthouse

# Apenas coletar dados
npm run lighthouse:collect

# Apenas verificar thresholds
npm run lighthouse:assert
```

#### Métricas Monitoradas

**Core Web Vitals:**
- LCP (Largest Contentful Paint): < 2.5s
- FID (First Input Delay): < 100ms
- CLS (Cumulative Layout Shift): < 0.1

**Outras Métricas:**
- FCP (First Contentful Paint): < 1.8s
- TTI (Time to Interactive): < 3.8s
- TBT (Total Blocking Time): < 300ms
- Speed Index: < 3.4s

#### Configuração

```javascript
// lighthouserc.js
module.exports = {
  ci: {
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
      },
    },
  },
}
```

### Web Vitals Tracking

Monitora Core Web Vitals em tempo real durante desenvolvimento.

#### Setup

```typescript
// app/layout.tsx
import { initWebVitals } from '@/lib/web-vitals'

export default function RootLayout({ children }: { children: React.Node }) {
  useEffect(() => {
    initWebVitals()
  }, [])

  return (
    <html>
      <body>
        {children}
        {process.env.NODE_ENV === 'development' && <WebVitalsDebugger />}
      </body>
    </html>
  )
}
```

#### Next.js Integration

```typescript
// pages/_app.tsx
import { reportWebVitals } from '@/lib/web-vitals'

export { reportWebVitals }
```

#### Métricas Coletadas

- **LCP**: Largest Contentful Paint
- **FID**: First Input Delay
- **CLS**: Cumulative Layout Shift
- **FCP**: First Contentful Paint
- **INP**: Interaction to Next Paint
- **TTFB**: Time to First Byte

#### Enviar para Analytics

```typescript
// Configurar em .env
NEXT_PUBLIC_ANALYTICS_ENDPOINT=https://your-api.com/vitals
```

Métricas são automaticamente enviadas para:
1. Google Analytics (se configurado)
2. Custom endpoint (opcional)
3. localStorage (desenvolvimento)
4. Console (desenvolvimento)

## 🧬 Mutation Testing

### O Que É?

Mutation Testing testa a qualidade dos seus testes introduzindo "mutações" (bugs) no código e verificando se os testes detectam.

### Por Que Usar?

- ✅ Valida qualidade dos testes (não apenas cobertura)
- ✅ Detecta testes fracos
- ✅ Encontra código não testado
- ✅ Melhora confiança nos testes

### Executar

```bash
# Executar mutation testing
npm run test:mutation

# Ver relatório HTML
open reports/mutation/html/index.html
```

### Métricas

**Mutation Score**: % de mutantes mortos pelos testes

- **≥ 80%**: Excelente
- **60-80%**: Bom
- **< 60%**: Precisa melhorar

### Exemplo

```typescript
// Código original
function add(a: number, b: number) {
  return a + b
}

// Mutante 1: Operador aritmético
function add(a: number, b: number) {
  return a - b  // + mudado para -
}

// Mutante 2: Literal
function add(a: number, b: number) {
  return a + 0  // b mudado para 0
}

// Se os testes NÃO detectarem essas mutações,
// significa que os testes estão fracos!
```

### Configuração

```javascript
// stryker.config.mjs
export default {
  testRunner: 'jest',
  coverageAnalysis: 'perTest',
  mutate: [
    'components/**/*.{ts,tsx}',
    '!**/*.test.{ts,tsx}',
  ],
  thresholds: {
    high: 80,
    low: 60,
    break: 50,
  },
}
```

### Interpretar Resultados

```
Mutants:
  Killed: 85    // ✅ Testes detectaram
  Survived: 10  // ❌ Testes NÃO detectaram
  Timeout: 2    // ⏱️ Timeout
  No Coverage: 3 // 🔍 Sem cobertura

Mutation Score: 85% (85/98)
```

**O que fazer com mutantes sobreviventes:**
1. Adicionar testes específicos
2. Melhorar assertions existentes
3. Ou ignorar se intencional

## 📊 Comparação de Técnicas

| Técnica | O Que Testa | Quando Usar | Custo |
|---------|-------------|-------------|-------|
| **Unitário** | Lógica individual | Sempre | Baixo |
| **Integração** | Interação entre módulos | APIs, componentes complexos | Médio |
| **E2E** | Fluxos completos | User journeys críticos | Alto |
| **Visual Regression** | Aparência visual | UI components, layouts | Médio |
| **Snapshot** | Estrutura renderizada | Componentes estáveis | Baixo |
| **Performance** | Velocidade, métricas | Antes de releases | Médio |
| **Mutation** | Qualidade dos testes | Periodicamente | Alto |
| **Acessibilidade** | WCAG compliance | Todas as páginas | Baixo |

## 🎯 Estratégia de Testes Recomendada

### Pirâmide de Testes

```
      /\
     /  \      E2E (10%)
    /____\
   /      \    Integração (30%)
  /________\
 /          \  Unitários (60%)
/____________\
```

### Coverage Targets

- **Unitários**: 80%+ coverage
- **Integração**: Endpoints críticos
- **E2E**: Fluxos principais
- **Visual**: Componentes chave
- **Performance**: Páginas principais
- **Mutation**: 70%+ mutation score
- **Acessibilidade**: 100% das páginas

### Workflow Completo

```
1. Desenvolvimento
   ├─ Escrever código
   ├─ Testes unitários (TDD)
   └─ Testes de snapshot

2. Feature Completa
   ├─ Testes de integração
   ├─ Testes E2E
   └─ Testes visuais

3. Antes do Commit
   ├─ npm run validate:local
   ├─ Revisar coverage
   └─ Revisar snapshots

4. Antes do Release
   ├─ Performance testing
   ├─ Mutation testing
   ├─ Testes de acessibilidade
   └─ Visual regression completo

5. CI/CD
   ├─ Todos os testes
   ├─ Lighthouse CI
   └─ Deploy se passar
```

## 🚀 Comandos Rápidos

### Testes Básicos

```bash
npm test                  # Unitários
npm run test:watch        # Watch mode
npm run test:coverage     # Com cobertura
```

### Testes Avançados

```bash
npm run test:e2e          # E2E
npm run test:visual       # Visual regression
npm run test:mutation     # Mutation testing
npm run lighthouse        # Performance
```

### Validação Completa

```bash
npm run validate:local    # Validação local (13 checks)
npm run test:all          # Todos os testes
```

### Desenvolvimento

```bash
npm run storybook         # Storybook (UI dev)
npm run chromatic         # Visual regression (pago)
```

## 📚 Recursos Adicionais

### Documentação

- [TESTING.md](../TESTING.md) - Guia básico de testes
- [VISUAL_REGRESSION.md](./VISUAL_REGRESSION.md) - Visual regression detalhado
- [scripts/README.md](../scripts/README.md) - Validação local

### Ferramentas

- [Playwright](https://playwright.dev/) - E2E e visual
- [Jest](https://jestjs.io/) - Unitários e snapshot
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci) - Performance
- [Stryker](https://stryker-mutator.io/) - Mutation testing
- [Chromatic](https://www.chromatic.com/) - Visual regression (pago)

### Boas Práticas

- [Testing Library Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Web Vitals](https://web.dev/vitals/)
- [Mutation Testing Best Practices](https://stryker-mutator.io/docs/mutation-testing-elements/supported-mutators/)

---

**Última atualização**: 2025-11-22

**Versão**: 2.0.0

**Implementado**:
✅ Visual Regression Testing (Playwright)
✅ Snapshot Testing
✅ Lighthouse CI
✅ Web Vitals Tracking
✅ Mutation Testing (Stryker)
✅ Performance Budgets

**Opcional**:
⏳ Chromatic (quando houver orçamento)
⏳ Storybook (para component development)
