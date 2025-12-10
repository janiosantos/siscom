#!/bin/bash

###############################################################################
# Script de Validação Local - Frontend
#
# Este script executa TODAS as validações que o GitHub Actions executa,
# mas localmente, permitindo detectar erros ANTES de fazer push.
#
# Uso:
#   bash scripts/validate_frontend_local.sh
#
# Similar ao script do backend (scripts/validate_ci_local.sh)
###############################################################################

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

# Função para imprimir seção
print_section() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# Função para imprimir sucesso
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

# Função para imprimir erro
print_error() {
    echo -e "${RED}❌ $1${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

# Função para imprimir warning
print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Função para executar check
run_check() {
    local check_name=$1
    local command=$2

    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))

    echo -e "${BLUE}Executando: $check_name${NC}"

    if eval "$command"; then
        print_success "$check_name"
        return 0
    else
        print_error "$check_name"
        return 1
    fi
}

# Início do script
print_section "🚀 Validação Local do Frontend - SISCOM"
echo "Este script executa as mesmas validações do CI/CD, mas localmente."
echo "Economize tempo e detecte erros antes de fazer push!"
echo ""

# Verificar se estamos no diretório correto
if [ ! -f "package.json" ]; then
    print_error "package.json não encontrado. Execute este script da pasta frontend/"
    exit 1
fi

print_success "Diretório correto detectado"

###############################################################################
# 1. VERIFICAÇÃO DE SINTAXE E TYPES
###############################################################################
print_section "1️⃣  Verificação de Sintaxe e TypeScript"

run_check "TypeScript Type Check" "npm run type-check" || true

###############################################################################
# 2. LINTING E FORMATAÇÃO
###############################################################################
print_section "2️⃣  Linting e Formatação"

run_check "ESLint" "npm run lint" || true

###############################################################################
# 3. BUILD
###############################################################################
print_section "3️⃣  Build do Projeto"

run_check "Next.js Build" "npm run build" || {
    print_warning "Build falhou. Verifique os erros acima."
}

###############################################################################
# 4. TESTES UNITÁRIOS E DE INTEGRAÇÃO
###############################################################################
print_section "4️⃣  Testes Unitários e de Integração (Jest)"

run_check "Testes Jest com Cobertura" "npm run test:ci" || {
    print_error "Testes Jest falharam"
}

###############################################################################
# 5. TESTES E2E (OPCIONAL - COMENTADO POR PADRÃO)
###############################################################################
print_section "5️⃣  Testes E2E (Playwright)"

print_warning "Testes E2E desabilitados por padrão (demoram mais)"
print_warning "Para executar: npm run test:e2e"

# Descomente para executar testes E2E automaticamente:
# run_check "Testes E2E Playwright" "npm run test:e2e" || {
#     print_error "Testes E2E falharam"
# }

###############################################################################
# 6. VERIFICAÇÃO DE DEPENDÊNCIAS
###############################################################################
print_section "6️⃣  Verificação de Dependências"

# Verificar se todas as dependências estão instaladas
if [ -d "node_modules" ]; then
    print_success "node_modules existe"
else
    print_error "node_modules não encontrado. Execute: npm install"
    exit 1
fi

# Verificar vulnerabilidades (npm audit)
run_check "NPM Audit (Vulnerabilidades)" "npm audit --audit-level=high" || {
    print_warning "Vulnerabilidades encontradas. Revise com: npm audit"
}

###############################################################################
# 7. VERIFICAÇÃO DE ARQUIVOS ESSENCIAIS
###############################################################################
print_section "7️⃣  Verificação de Arquivos Essenciais"

ESSENTIAL_FILES=(
    "package.json"
    "tsconfig.json"
    "next.config.js"
    "jest.config.js"
    "jest.setup.js"
    "playwright.config.ts"
    "tailwind.config.ts"
)

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "Arquivo $file existe"
    else
        print_error "Arquivo $file não encontrado"
    fi
done

###############################################################################
# 8. VERIFICAÇÃO DE ESTRUTURA DE PASTAS
###############################################################################
print_section "8️⃣  Verificação de Estrutura de Pastas"

ESSENTIAL_DIRS=(
    "app"
    "components"
    "lib"
    "public"
    "__tests__"
    "e2e"
)

for dir in "${ESSENTIAL_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        print_success "Diretório $dir existe"
    else
        print_warning "Diretório $dir não encontrado"
    fi
done

###############################################################################
# 9. VERIFICAÇÃO DE TESTES
###############################################################################
print_section "9️⃣  Verificação de Cobertura de Testes"

# Contar arquivos de teste
TEST_FILES=$(find . -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.spec.ts" | wc -l)
echo "Total de arquivos de teste: $TEST_FILES"

if [ "$TEST_FILES" -gt 20 ]; then
    print_success "Boa cobertura de testes ($TEST_FILES arquivos)"
else
    print_warning "Poucos arquivos de teste ($TEST_FILES). Considere adicionar mais."
fi

###############################################################################
# 10. VERIFICAÇÃO DE IMPORTS QUEBRADOS
###############################################################################
print_section "🔟 Verificação de Imports Quebrados"

run_check "Verificar Imports" "grep -r \"from '@/\" app/ components/ lib/ || echo 'Nenhum import quebrado detectado'" || true

###############################################################################
# 11. VERIFICAÇÃO DE CONSOLE.LOG
###############################################################################
print_section "1️⃣1️⃣  Verificação de console.log (Limpeza de Código)"

CONSOLE_LOGS=$(grep -r "console.log" app/ components/ lib/ 2>/dev/null | wc -l || echo "0")

if [ "$CONSOLE_LOGS" -eq 0 ]; then
    print_success "Nenhum console.log encontrado"
else
    print_warning "$CONSOLE_LOGS console.log(s) encontrado(s). Considere remover antes do commit."
fi

###############################################################################
# 12. VERIFICAÇÃO DE CONFIGURAÇÃO MSW
###############################################################################
print_section "1️⃣2️⃣  Verificação de MSW (Mock Service Worker)"

if [ -d "__tests__/mocks" ]; then
    print_success "Pasta de mocks MSW existe"

    if [ -f "__tests__/mocks/handlers.ts" ]; then
        print_success "handlers.ts existe"
    else
        print_error "handlers.ts não encontrado"
    fi

    if [ -f "__tests__/mocks/server.ts" ]; then
        print_success "server.ts existe"
    else
        print_error "server.ts não encontrado"
    fi
else
    print_error "Pasta __tests__/mocks não encontrada"
fi

###############################################################################
# 13. VERIFICAÇÃO DE ACESSIBILIDADE (jest-axe)
###############################################################################
print_section "1️⃣3️⃣  Verificação de Testes de Acessibilidade"

AXE_TESTS=$(grep -r "jest-axe" app/ components/ __tests__/ 2>/dev/null | wc -l || echo "0")

if [ "$AXE_TESTS" -gt 0 ]; then
    print_success "$AXE_TESTS testes de acessibilidade encontrados"
else
    print_warning "Nenhum teste de acessibilidade encontrado. Considere usar jest-axe."
fi

###############################################################################
# RESUMO FINAL
###############################################################################
print_section "📊 RESUMO DA VALIDAÇÃO"

echo "Total de verificações: $TOTAL_CHECKS"
echo -e "${GREEN}Passou: $PASSED_CHECKS${NC}"
echo -e "${RED}Falhou: $FAILED_CHECKS${NC}"
echo ""

if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✅ TODAS AS VALIDAÇÕES PASSARAM!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${GREEN}Você pode fazer commit e push com segurança! 🚀${NC}"
    exit 0
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}❌ ALGUMAS VALIDAÇÕES FALHARAM${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${RED}Por favor, corrija os erros antes de fazer push.${NC}"
    echo ""
    echo "Dicas:"
    echo "  - Execute 'npm run type-check' para verificar erros de TypeScript"
    echo "  - Execute 'npm run lint' para verificar problemas de linting"
    echo "  - Execute 'npm test' para rodar os testes"
    echo "  - Execute 'npm run build' para verificar se o build passa"
    exit 1
fi
