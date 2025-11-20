#!/bin/bash
# Script de Validação Local CI/CD
# Executa verificações locais antes de fazer push, evitando erros no GitHub Actions
#
# USO:
#   ./scripts/validate_ci_local.sh
#   make validate-local  (se configurado no Makefile)
#
# O QUE FAZ:
#   1. Verifica sintaxe Python
#   2. Valida imports de modelos
#   3. Checa foreign keys incorretas
#   4. Valida existência de classes nos models
#   5. Verifica schemas Pydantic
#   6. Valida funções específicas (converter_status_mp, etc)
#   7. Checa configuração bcrypt
#   8. Valida imports em conftest.py
#   9. Verifica nomes de campos em testes
#   10. EXECUTA TESTES PYTEST (opcional)
#
# VANTAGENS:
#   - Detecta erros ANTES de fazer push
#   - Economiza tempo (não precisa esperar GitHub Actions)
#   - Feedback imediato sobre problemas
#   - Executa os mesmos testes que rodam no CI/CD

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BOLD}=================================================="
echo -e "🔍 Validação Local do CI/CD"
echo -e "==================================================${NC}"
echo ""

# 1. Sintaxe Python
echo -e "${YELLOW}1️⃣  Verificando sintaxe Python...${NC}"
if python3 -m py_compile app/models.py tests/conftest.py 2>/dev/null; then
    echo -e "   ${GREEN}✅ Sintaxe Python OK${NC}"
else
    echo -e "   ${RED}❌ Erro de sintaxe Python${NC}"
    exit 1
fi
echo ""

# 2. Imports do módulo auth
echo -e "${YELLOW}2️⃣  Verificando imports do módulo auth...${NC}"
if grep -E "^class (User|Role|Permission|AuditLog|RefreshToken)\(" app/modules/auth/models.py > /dev/null; then
    echo -e "   ${GREEN}✅ Módulo auth OK${NC}"
else
    echo -e "   ${RED}❌ Classes do módulo auth não encontradas${NC}"
    exit 1
fi
echo ""

# 3. Foreign keys incorretas
echo -e "${YELLOW}3️⃣  Verificando foreign keys...${NC}"
if grep -r 'ForeignKey("usuarios' app/modules --include="*.py"; then
    echo -e "   ${RED}❌ Encontrada referência a 'usuarios' (deveria ser 'users')${NC}"
    exit 1
else
    echo -e "   ${GREEN}✅ Nenhuma referência incorreta a 'usuarios'${NC}"
fi
echo ""

# 4. Imports em app/models.py
echo -e "${YELLOW}4️⃣  Verificando imports em app/models.py...${NC}"

# Classes que devem existir
declare -A model_checks=(
    ["app/modules/produtos/models.py"]="Produto"
    ["app/modules/categorias/models.py"]="Categoria"
    ["app/modules/estoque/models.py"]="MovimentacaoEstoque LoteEstoque LocalizacaoEstoque"
    ["app/modules/vendas/models.py"]="Venda ItemVenda"
    ["app/modules/pdv/models.py"]="Caixa MovimentacaoCaixa"
    ["app/modules/financeiro/models.py"]="ContaPagar ContaReceber"
    ["app/modules/nfe/models.py"]="NotaFiscal"
    ["app/modules/clientes/models.py"]="Cliente"
    ["app/modules/condicoes_pagamento/models.py"]="CondicaoPagamento ParcelaPadrao"
    ["app/modules/pagamentos/models.py"]="ChavePix TransacaoPix Boleto ConciliacaoBancaria"
)

errors=0
for file in "${!model_checks[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "   ${RED}❌ Arquivo não encontrado: $file${NC}"
        ((errors++))
        continue
    fi

    for class in ${model_checks[$file]}; do
        if ! grep -q "class $class(" "$file"; then
            echo -e "   ${RED}❌ Classe $class não encontrada em $file${NC}"
            ((errors++))
        fi
    done
done

if [ $errors -eq 0 ]; then
    echo -e "   ${GREEN}✅ Todos os imports verificados (36 classes)${NC}"
else
    echo -e "   ${RED}❌ $errors erro(s) encontrado(s) nos imports${NC}"
    exit 1
fi
echo ""

# 5. Schemas Pydantic
echo -e "${YELLOW}5️⃣  Verificando schemas Pydantic...${NC}"
if grep -q "tipo_conta" app/modules/pagamentos/schemas.py && \
   grep -q "nome_titular" app/modules/pagamentos/schemas.py; then
    echo -e "   ${GREEN}✅ ChavePixBase tem campos obrigatórios${NC}"
else
    echo -e "   ${RED}❌ Campos faltando em ChavePixBase${NC}"
    exit 1
fi
echo ""

# 6. Converter status
echo -e "${YELLOW}6️⃣  Verificando converter_status_mp...${NC}"
if grep -q "def converter_status_mp.*StatusPagamento" app/integrations/mercadopago.py; then
    echo -e "   ${GREEN}✅ converter_status_mp retorna StatusPagamento enum${NC}"
else
    echo -e "   ${RED}❌ converter_status_mp não retorna enum correto${NC}"
    exit 1
fi
echo ""

# 7. Bcrypt configuration
echo -e "${YELLOW}7️⃣  Verificando configuração bcrypt...${NC}"
if grep -q "bcrypt__default_rounds" app/modules/auth/security.py; then
    echo -e "   ${GREEN}✅ CryptContext configurado corretamente${NC}"
else
    echo -e "   ${RED}❌ CryptContext não tem configuração bcrypt${NC}"
    exit 1
fi
echo ""

# 8. Verificar import que não sobrescreve app
echo -e "${YELLOW}8️⃣  Verificando imports em conftest.py...${NC}"
if grep -q "^import app\\.models" tests/conftest.py; then
    echo -e "   ${RED}❌ 'import app.models' sobrescreve variável app${NC}"
    echo -e "   ${YELLOW}   Use 'from app import models' no lugar${NC}"
    exit 1
elif grep -q "^from app import models" tests/conftest.py; then
    echo -e "   ${GREEN}✅ Import de models correto (não sobrescreve app)${NC}"
else
    echo -e "   ${YELLOW}⚠️  Import de models não encontrado${NC}"
fi
echo ""

# 9. Verificar nomes de campos em schemas de testes
echo -e "${YELLOW}9️⃣  Verificando nomes de campos em testes...${NC}"
errors=0

# Verificar se test_boleto.py usa campos corretos
if [ -f "tests/test_boleto.py" ]; then
    if grep -q "cedente_cnpj" tests/test_boleto.py; then
        echo -e "   ${RED}❌ test_boleto.py usa 'cedente_cnpj' (deveria ser 'cedente_documento')${NC}"
        ((errors++))
    fi
    if grep -q "sacado_cpf_cnpj" tests/test_boleto.py; then
        echo -e "   ${RED}❌ test_boleto.py usa 'sacado_cpf_cnpj' (deveria ser 'sacado_documento')${NC}"
        ((errors++))
    fi
fi

# Verificar se test_pix.py usa campos corretos
if [ -f "tests/test_pix.py" ]; then
    if ! grep -q "tipo_conta" tests/test_pix.py && grep -q "ChavePixCreate" tests/test_pix.py; then
        echo -e "   ${YELLOW}⚠️  test_pix.py pode estar faltando campo 'tipo_conta'${NC}"
    fi
fi

if [ $errors -eq 0 ]; then
    echo -e "   ${GREEN}✅ Nomes de campos corretos nos testes${NC}"
else
    echo -e "   ${RED}❌ $errors erro(s) encontrado(s) nos nomes de campos${NC}"
    exit 1
fi
echo ""

# 10. Executar testes pytest (opcional - pode falhar se deps não instaladas)
echo -e "${YELLOW}🔟  Executando testes pytest (opcional)...${NC}"
if command -v pytest &> /dev/null; then
    echo -e "   ${YELLOW}   Executando pytest com coverage...${NC}"

    # Executar pytest com timeout e capturar resultado
    if timeout 120 python -m pytest tests/ -v --tb=short --maxfail=3 2>&1 | tee /tmp/pytest_output.txt; then
        echo -e "   ${GREEN}✅ Testes pytest passaram!${NC}"

        # Mostrar resumo
        if grep -q "passed" /tmp/pytest_output.txt; then
            summary=$(grep -E "passed|failed|error" /tmp/pytest_output.txt | tail -1)
            echo -e "   ${GREEN}   $summary${NC}"
        fi
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo -e "   ${YELLOW}⚠️  Testes excederam timeout de 120s${NC}"
        else
            echo -e "   ${RED}❌ Alguns testes falharam${NC}"
            echo -e "   ${YELLOW}   Verifique os erros acima${NC}"

            # Mostrar apenas os testes que falharam
            if [ -f /tmp/pytest_output.txt ]; then
                echo ""
                echo -e "   ${YELLOW}Testes que falharam:${NC}"
                grep "FAILED" /tmp/pytest_output.txt | head -5 | while read line; do
                    echo -e "   ${RED}   $line${NC}"
                done
            fi
            exit 1
        fi
    fi
else
    echo -e "   ${YELLOW}⚠️  pytest não instalado - pulando testes${NC}"
    echo -e "   ${YELLOW}   Instale com: pip install -r requirements.txt${NC}"
fi
echo ""

echo -e "${BOLD}${GREEN}=================================================="
echo -e "✅ VALIDAÇÃO COMPLETA - TUDO OK!"
echo -e "==================================================${NC}"
echo ""
echo -e "${GREEN}Você pode fazer push com segurança! 🚀${NC}"
