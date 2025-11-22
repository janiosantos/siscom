# Documentação - Frontend SISCOM

## 📚 Guias Disponíveis

### Testes

1. **[TESTING.md](../TESTING.md)** - Guia completo de testes básicos
   - Testes unitários com Jest
   - Testes de componentes com React Testing Library
   - Testes de integração com MSW
   - Testes E2E com Playwright
   - Script de validação local

2. **[ADVANCED_TESTING.md](./ADVANCED_TESTING.md)** - Técnicas avançadas de teste
   - Visual Regression Testing
   - Snapshot Testing
   - Performance Testing (Lighthouse CI)
   - Web Vitals Tracking
   - Mutation Testing
   - Estratégias e melhores práticas

3. **[VISUAL_REGRESSION.md](./VISUAL_REGRESSION.md)** - Visual regression detalhado
   - Playwright Screenshots
   - Chromatic (opcional)
   - Configuração e workflow
   - Exemplos práticos

## 🚀 Quick Start

### Executar Testes

```bash
# Testes básicos
npm test                    # Unitários
npm run test:e2e            # E2E
npm run validate:local      # Validação completa

# Testes avançados
npm run test:visual         # Visual regression
npm run test:mutation       # Mutation testing
npm run lighthouse          # Performance
```

### Ver Documentação

```bash
# Abrir guia de testes
cat docs/TESTING.md

# Abrir guia avançado
cat docs/ADVANCED_TESTING.md

# Abrir visual regression
cat docs/VISUAL_REGRESSION.md
```

## 📊 Níveis de Teste

| Nível | Guia | Quando Usar |
|-------|------|-------------|
| **Básico** | [TESTING.md](../TESTING.md) | Início do projeto |
| **Intermediário** | [TESTING.md](../TESTING.md) | Desenvolvimento contínuo |
| **Avançado** | [ADVANCED_TESTING.md](./ADVANCED_TESTING.md) | Antes de releases |

## 🎯 Qual Guia Usar?

### Para Começar
👉 [TESTING.md](../TESTING.md)
- Setup inicial
- Testes unitários
- Testes E2E básicos

### Para Melhorar Qualidade
👉 [ADVANCED_TESTING.md](./ADVANCED_TESTING.md)
- Visual regression
- Performance testing
- Mutation testing

### Para Visual Testing
👉 [VISUAL_REGRESSION.md](./VISUAL_REGRESSION.md)
- Screenshots automáticos
- Chromatic setup
- Workflow completo

## 🔗 Links Externos

### Ferramentas
- [Jest Docs](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright Docs](https://playwright.dev/docs/intro)
- [MSW Docs](https://mswjs.io/docs/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [Stryker Docs](https://stryker-mutator.io/docs/)

### Recursos
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Web Vitals](https://web.dev/vitals/)
- [Accessibility Testing](https://github.com/nickcolley/jest-axe)

---

**Última atualização**: 2025-11-22
