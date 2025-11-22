# Scripts do Frontend

## 📋 Visão Geral

Esta pasta contém scripts utilitários para o frontend do SISCOM.

## 🔍 validate_frontend_local.sh

### Descrição

Script de validação local que executa **TODAS** as verificações que o GitHub Actions executa no CI/CD, mas rodando localmente. Isso permite detectar erros **ANTES** de fazer push, economizando tempo e evitando falhas no CI.

### Por que usar?

- ⚡ **Feedback rápido**: Erros detectados em segundos, não minutos
- 💰 **Economiza tempo**: Não precisa esperar GitHub Actions
- 🎯 **Mais preciso**: Detecta problemas antes de fazer push
- ✅ **Confiável**: Mesmas verificações do CI/CD rodando localmente

### 13 Verificações Executadas

1. ✅ **TypeScript Type Check** - Verifica erros de tipos
2. ✅ **ESLint** - Verifica problemas de linting
3. ✅ **Build do Next.js** - Garante que o build funciona
4. ✅ **Testes Jest com Cobertura** - Executa testes unitários
5. ✅ **Testes E2E** (opcional) - Testes end-to-end com Playwright
6. ✅ **NPM Audit** - Verifica vulnerabilidades de segurança
7. ✅ **Arquivos Essenciais** - Verifica existência de arquivos críticos
8. ✅ **Estrutura de Pastas** - Valida estrutura do projeto
9. ✅ **Cobertura de Testes** - Conta e valida arquivos de teste
10. ✅ **Imports Quebrados** - Detecta imports inválidos
11. ✅ **console.log** - Alerta sobre console.log no código
12. ✅ **Configuração MSW** - Verifica setup de Mock Service Worker
13. ✅ **Testes de Acessibilidade** - Conta testes com jest-axe

### Como Usar

#### Via npm script (recomendado):

```bash
npm run validate:local
```

#### Diretamente:

```bash
bash scripts/validate_frontend_local.sh
```

#### No diretório raiz do projeto:

```bash
cd frontend
bash scripts/validate_frontend_local.sh
```

### Output de Exemplo

#### ✅ Sucesso (todas validações passaram):

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

========================================
✅ TODAS AS VALIDAÇÕES PASSARAM!
========================================

Você pode fazer commit e push com segurança! 🚀
```

#### ❌ Falha (algumas validações falharam):

```
🚀 Validação Local do Frontend - SISCOM
========================================

1️⃣  Verificação de Sintaxe e TypeScript
❌ TypeScript Type Check

...

📊 RESUMO DA VALIDAÇÃO
Total de verificações: 13
Passou: 11
Falhou: 2

========================================
❌ ALGUMAS VALIDAÇÕES FALHARAM
========================================

Por favor, corrija os erros antes de fazer push.

Dicas:
  - Execute 'npm run type-check' para verificar erros de TypeScript
  - Execute 'npm run lint' para verificar problemas de linting
  - Execute 'npm test' para rodar os testes
  - Execute 'npm run build' para verificar se o build passa
```

### Workflow Recomendado

```
1. Desenvolvimento Local
   - Fazer alterações no código
   - Testar localmente
   ↓
2. npm run validate:local ⭐ (CRÍTICO)
   - Executa todas as validações
   - Detecta erros antes do commit
   ↓
3. git add . && git commit -m "mensagem"
   - Fazer commit se validação passou
   ↓
4. git push
   - Enviar para o repositório
   ↓
5. GitHub Actions
   - Validação adicional no CI/CD
   - Mesmas verificações que rodaram localmente
```

### Diferenças com o Backend

O frontend tem um script similar ao backend (`scripts/validate_ci_local.sh`), mas adaptado para:

- **Backend**: Python, pytest, flake8, mypy, etc.
- **Frontend**: TypeScript, Jest, ESLint, Playwright, etc.

Ambos seguem a mesma filosofia:
> **Detecte erros localmente antes de fazer push!**

### Desabilitar Testes E2E

Por padrão, os testes E2E estão **desabilitados** no script (comentados) porque demoram mais tempo.

Para habilitar, edite `scripts/validate_frontend_local.sh` e descomente:

```bash
# run_check "Testes E2E Playwright" "npm run test:e2e" || {
#     print_error "Testes E2E falharam"
# }
```

### Executar Apenas Validações Específicas

Se quiser executar apenas uma validação específica:

```bash
# Type check
npm run type-check

# Linting
npm run lint

# Build
npm run build

# Testes
npm test

# Testes com cobertura
npm run test:coverage

# Testes E2E
npm run test:e2e
```

### Integração com Git Hooks

Você pode configurar o script para rodar automaticamente antes de commits usando Husky:

```bash
# Instalar Husky
npm install --save-dev husky

# Configurar pre-commit hook
npx husky install
npx husky add .husky/pre-commit "npm run validate:local"
```

### Troubleshooting

#### Script não encontrado

```bash
# Verificar se está no diretório correto
pwd  # Deve estar em /frontend

# Tornar script executável
chmod +x scripts/validate_frontend_local.sh
```

#### Permissão negada

```bash
chmod +x scripts/validate_frontend_local.sh
```

#### Node modules não encontrado

```bash
npm install
```

#### Script falha mas não sei qual check

O script mostra exatamente qual check falhou. Revise o output colorido:
- 🟢 Verde = Passou
- 🔴 Vermelho = Falhou
- 🟡 Amarelo = Warning

### Comparação com GitHub Actions

| Validação | Local (Script) | GitHub Actions |
|-----------|----------------|----------------|
| Type Check | ✅ | ✅ |
| Linting | ✅ | ✅ |
| Build | ✅ | ✅ |
| Testes | ✅ | ✅ |
| E2E | ⚠️ Opcional | ✅ |
| Audit | ✅ | ✅ |

**Vantagem Local**: Feedback instantâneo (segundos)
**Vantagem CI**: Ambiente isolado e controlado

### FAQ

**Q: Preciso rodar isso toda vez?**
A: Recomendado antes de fazer push ou PR.

**Q: Demora muito?**
A: ~30-60 segundos (sem E2E), ~2-5 minutos (com E2E).

**Q: Posso pular alguma validação?**
A: Sim, mas não recomendado. Todas são importantes.

**Q: Por que não usar apenas GitHub Actions?**
A: Feedback mais rápido + economia de tempo + detecta erros antes.

**Q: É igual ao backend?**
A: Filosofia similar, mas validações específicas de frontend.

---

## 📚 Recursos Relacionados

- [TESTING.md](../TESTING.md) - Guia completo de testes
- [package.json](../package.json) - Scripts npm disponíveis
- Backend: [scripts/validate_ci_local.sh](../../scripts/validate_ci_local.sh)

---

**Última atualização**: 2025-11-22

**Autor**: Sistema SISCOM

**Versão**: 1.0.0
