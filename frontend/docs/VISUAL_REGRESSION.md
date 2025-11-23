# Visual Regression Testing

## 📋 Visão Geral

Visual Regression Testing detecta mudanças visuais não intencionais na UI. Implementamos duas abordagens:

1. **Playwright Screenshots** (Built-in, gratuito)
2. **Chromatic** (Opcional, pago, mais recursos)

## 🎨 Playwright Screenshot Testing (Implementado)

### Como Funciona

Playwright captura screenshots e compara com baselines (referências). Se houver diferenças, o teste falha.

### Executar Testes Visuais

```bash
# Primeira execução - gera baselines
npm run test:e2e -- e2e/visual-regression.spec.ts

# Executar testes visuais
npm run test:e2e -- e2e/visual-regression.spec.ts

# Atualizar baselines (após revisar mudanças)
npm run test:e2e -- e2e/visual-regression.spec.ts --update-snapshots
```

### Baselines Geradas

Screenshots são salvos em:
```
e2e/visual-regression.spec.ts-snapshots/
├── produtos-page-chromium.png
├── produtos-table-chromium.png
├── produto-modal-chromium.png
├── produtos-mobile-chromium.png
├── produtos-tablet-chromium.png
├── produtos-empty-chromium.png
├── produtos-loading-chromium.png
├── produtos-error-chromium.png
├── produtos-dark-chromium.png
├── button-hover-chromium.png
└── table-row-hover-chromium.png
```

### Testes Implementados

#### Estados da Página
- ✅ Página completa (desktop, mobile, tablet)
- ✅ Componentes específicos (tabela, modal)
- ✅ Estado vazio (sem dados)
- ✅ Estado de loading
- ✅ Estado de erro
- ✅ Dark mode
- ✅ Hover states

#### Viewports Testados
- Desktop: 1280x720 (default)
- Mobile: 375x667 (iPhone)
- Tablet: 768x1024 (iPad)

### Configuração Avançada

#### Ignorar Elementos Dinâmicos

```typescript
await expect(page).toHaveScreenshot('page.png', {
  mask: [page.locator('.timestamp')], // Ocultar timestamps
  fullPage: true,
})
```

#### Threshold de Diferença

```typescript
await expect(page).toHaveScreenshot('page.png', {
  maxDiffPixels: 100, // Permitir até 100 pixels diferentes
})
```

#### Desabilitar Animações

```typescript
await expect(page).toHaveScreenshot('page.png', {
  animations: 'disabled', // Desabilitar animações CSS
})
```

### Exemplo de Teste Visual

```typescript
import { test, expect } from '@playwright/test'

test('visual test example', async ({ page }) => {
  await page.goto('/produtos')

  // Aguardar carregamento
  await page.waitForLoadState('networkidle')

  // Capturar screenshot
  await expect(page).toHaveScreenshot('produtos.png', {
    fullPage: true,
    animations: 'disabled',
  })
})
```

### Ver Diferenças

Quando um teste visual falha, Playwright gera:

1. **Expected**: Screenshot baseline
2. **Actual**: Screenshot atual
3. **Diff**: Imagem com diferenças destacadas

```bash
# Abrir relatório HTML para ver diferenças
npm run test:e2e:report
```

### Workflow Recomendado

```
1. Desenvolver feature
   ↓
2. Executar testes visuais
   npm run test:e2e -- visual-regression.spec.ts
   ↓
3. Se falhar:
   - Ver diferenças no relatório
   - Se mudança intencional: atualizar baseline
   - Se bug: corrigir código
   ↓
4. Atualizar baseline (se necessário)
   npm run test:e2e -- visual-regression.spec.ts --update-snapshots
   ↓
5. Commit (incluir screenshots no git)
```

### Git e Baselines

**IMPORTANTE**: Commitar screenshots no git!

```bash
git add e2e/**/*.png
git commit -m "test: update visual regression baselines"
```

Isso permite:
- CI/CD comparar screenshots
- Revisão visual em PRs
- Histórico de mudanças visuais

### CI/CD Integration

```yaml
# .github/workflows/ci.yml
- name: Run Visual Regression Tests
  run: npm run test:e2e -- visual-regression.spec.ts

- name: Upload failed screenshots
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: visual-regression-diffs
    path: test-results/
```

## 🎨 Chromatic (Opcional)

### O que é Chromatic?

Chromatic é um serviço pago de visual regression testing que oferece:

- Interface web para revisar mudanças
- Histórico de snapshots
- Colaboração em equipe
- Integração com Storybook
- CI/CD integration
- Detecção automática de mudanças

### Quando Usar?

**Use Playwright (gratuito) se:**
- Orçamento limitado
- Testes E2E já estão em Playwright
- Controle total sobre screenshots
- Baselines no git são ok

**Use Chromatic (pago) se:**
- Precisa de interface web para revisão
- Colaboração em equipe é importante
- Quer integração com Storybook
- Histórico visual é necessário
- Orçamento permite (~$150-500/mês)

### Setup Chromatic (Opcional)

#### 1. Instalar Dependências

```bash
npm install --save-dev chromatic storybook @storybook/react @storybook/react-vite
```

#### 2. Inicializar Storybook

```bash
npx storybook init
```

#### 3. Criar Account em Chromatic

1. Acesse https://www.chromatic.com/
2. Conecte seu repositório GitHub
3. Copie o Project Token

#### 4. Configurar Token

```bash
# .env.local
CHROMATIC_PROJECT_TOKEN=your-token-here
```

#### 5. Criar Stories

```typescript
// components/ui/button.stories.tsx
import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './button'

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
}

export default meta
type Story = StoryObj<typeof Button>

export const Primary: Story = {
  args: {
    children: 'Button',
    variant: 'primary',
  },
}

export const Secondary: Story = {
  args: {
    children: 'Button',
    variant: 'secondary',
  },
}

export const Disabled: Story = {
  args: {
    children: 'Button',
    disabled: true,
  },
}
```

#### 6. Executar Chromatic

```bash
# Publicar snapshots
npx chromatic --project-token=<your-token>

# No CI/CD
npx chromatic --exit-zero-on-changes
```

#### 7. Scripts npm

```json
{
  "scripts": {
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build",
    "chromatic": "chromatic --exit-zero-on-changes"
  }
}
```

### Chromatic Workflow

```
1. Criar/modificar componente
   ↓
2. Criar/atualizar story
   ↓
3. npm run chromatic
   ↓
4. Revisar mudanças na UI web do Chromatic
   ↓
5. Aceitar ou rejeitar mudanças
   ↓
6. CI/CD valida automaticamente
```

### Configuração Avançada

```json
// .chromatic.json
{
  "projectToken": "CHROMATIC_PROJECT_TOKEN",
  "buildScriptName": "build-storybook",
  "exitZeroOnChanges": true,
  "exitOnceUploaded": true,
  "autoAcceptChanges": "main",
  "ignoreLastBuildOnBranch": "main",
  "externals": [
    "public/**"
  ],
  "skip": "dependabot/**"
}
```

## 📊 Comparação

| Feature | Playwright Screenshots | Chromatic |
|---------|----------------------|-----------|
| **Custo** | Gratuito | $150-500/mês |
| **Setup** | Simples | Moderado |
| **Interface** | CLI + Relatório HTML | Web UI rica |
| **Colaboração** | Git + PRs | Built-in |
| **Histórico** | Git commits | Dashboard |
| **CI/CD** | GitHub Actions | Integrado |
| **Storybook** | Não | Sim |
| **Controle** | Total | Abstração |
| **Manutenção** | Manual | Gerenciado |

## 🎯 Recomendação

**Para o SISCOM:**

1. **Iniciar com Playwright Screenshots** (já implementado)
   - Gratuito
   - Suficiente para maioria dos casos
   - Fácil integração com testes E2E existentes

2. **Adicionar Chromatic futuramente** se:
   - Time crescer (múltiplos devs)
   - Orçamento permitir
   - Precisar de interface web
   - Quiser integração com Storybook

## 🚀 Comandos Rápidos

### Playwright (Implementado)

```bash
# Gerar baselines
npm run test:e2e -- visual-regression.spec.ts

# Executar testes visuais
npm run test:e2e -- visual-regression.spec.ts

# Atualizar baselines
npm run test:e2e -- visual-regression.spec.ts --update-snapshots

# Ver relatório
npm run test:e2e:report
```

### Chromatic (Opcional)

```bash
# Setup (uma vez)
npm install --save-dev chromatic storybook
npx storybook init

# Executar
npm run storybook              # Dev mode
npm run build-storybook        # Build
npm run chromatic              # Publicar
```

## 📚 Recursos

- [Playwright Visual Comparisons](https://playwright.dev/docs/test-snapshots)
- [Chromatic Docs](https://www.chromatic.com/docs/)
- [Storybook Docs](https://storybook.js.org/docs/react/get-started/introduction)

---

**Status**: ✅ Playwright Screenshots implementado
**Opcional**: ⏳ Chromatic (quando houver orçamento)
