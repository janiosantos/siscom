#!/bin/bash

# Script para separar o monorepo em dois repositórios
# Uso: ./scripts/split_repos.sh

set -e

echo "🚀 Iniciando separação de repositórios..."
echo ""

# Cores para output
RED='\033[0:31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Diretório base
BASE_DIR="/home/user/siscom"
TEMP_DIR="/tmp/siscom-split"

# Criar diretório temporário
mkdir -p "$TEMP_DIR"

# ============================================================================
# BACKEND
# ============================================================================

echo -e "${YELLOW}📦 Preparando Backend...${NC}"

BACKEND_DIR="$TEMP_DIR/siscom-backend"
mkdir -p "$BACKEND_DIR"

# Copiar arquivos do backend
echo "  Copiando arquivos do backend..."
cp -r "$BASE_DIR/app" "$BACKEND_DIR/"
cp -r "$BASE_DIR/alembic" "$BACKEND_DIR/"
cp -r "$BASE_DIR/tests" "$BACKEND_DIR/"
cp -r "$BASE_DIR/docs" "$BACKEND_DIR/"
cp -r "$BASE_DIR/scripts" "$BACKEND_DIR/"
cp -r "$BASE_DIR/nginx" "$BACKEND_DIR/"

# Arquivos raiz
cp "$BASE_DIR/main.py" "$BACKEND_DIR/"
cp "$BASE_DIR/requirements.txt" "$BACKEND_DIR/"
cp "$BASE_DIR/pytest.ini" "$BACKEND_DIR/"
cp "$BASE_DIR/alembic.ini" "$BACKEND_DIR/"
cp "$BASE_DIR/Makefile" "$BACKEND_DIR/"
cp "$BASE_DIR/Dockerfile" "$BACKEND_DIR/"
cp "$BASE_DIR/docker-compose.yml" "$BACKEND_DIR/"
cp "$BASE_DIR/docker-compose.prod.yml" "$BACKEND_DIR/"
cp "$BASE_DIR/.env.example" "$BACKEND_DIR/"
cp "$BASE_DIR/.gitignore" "$BACKEND_DIR/"
cp "$BASE_DIR/.pre-commit-config.yaml" "$BACKEND_DIR/"

# README específico
cp "$BASE_DIR/README_BACKEND.md" "$BACKEND_DIR/README.md"

# Documentação
cp "$BASE_DIR/CLAUDE.md" "$BACKEND_DIR/"

# Criar .github para CI/CD
mkdir -p "$BACKEND_DIR/.github/workflows"

echo -e "${GREEN}✅ Backend preparado em: $BACKEND_DIR${NC}"
echo ""

# ============================================================================
# FRONTEND
# ============================================================================

echo -e "${YELLOW}📦 Preparando Frontend...${NC}"

FRONTEND_DIR="$TEMP_DIR/siscom-frontend"
mkdir -p "$FRONTEND_DIR"

# Copiar todo o conteúdo do frontend
echo "  Copiando arquivos do frontend..."
cp -r "$BASE_DIR/frontend/"* "$FRONTEND_DIR/" 2>/dev/null || true
cp -r "$BASE_DIR/frontend/".* "$FRONTEND_DIR/" 2>/dev/null || true

# README específico
cp "$BASE_DIR/README_FRONTEND.md" "$FRONTEND_DIR/README.md"

# Dockerfile específico
if [ -f "$BASE_DIR/frontend/Dockerfile" ]; then
  cp "$BASE_DIR/frontend/Dockerfile" "$FRONTEND_DIR/"
fi

echo -e "${GREEN}✅ Frontend preparado em: $FRONTEND_DIR${NC}"
echo ""

# ============================================================================
# Inicializar Git
# ============================================================================

echo -e "${YELLOW}🔧 Inicializando repositórios Git...${NC}"

# Backend
cd "$BACKEND_DIR"
git init
git add .
git commit -m "chore: Initial commit - Backend API

Sistema ERP completo para Materiais de Construção

Stack:
- FastAPI 0.109
- Python 3.12+
- PostgreSQL 15
- SQLAlchemy 2.0 async
- JWT + RBAC
- 40+ endpoints
- Testes com pytest

Features:
- Autenticação e autorização
- Gestão de produtos e estoque
- Vendas e orçamentos
- Pagamentos (PIX, Boleto, Cartão)
- NF-e e documentos fiscais
- Relatórios e dashboard
- Integrações (Mercado Pago, PagSeguro, Correios)
"

echo -e "${GREEN}✅ Backend Git inicializado${NC}"

# Frontend
cd "$FRONTEND_DIR"
git init
git add .
git commit -m "chore: Initial commit - Frontend Web

Interface web moderna para Sistema ERP

Stack:
- Next.js 14 (App Router)
- React 18
- TypeScript 5
- Tailwind CSS
- Shadcn/ui
- SWR

Features:
- Dashboard com métricas em tempo real
- Gestão de produtos e vendas
- Relatórios e análises
- Interface responsiva
- Tema claro/escuro
- Testes com Jest e Playwright
"

echo -e "${GREEN}✅ Frontend Git inicializado${NC}"
echo ""

# ============================================================================
# Instruções finais
# ============================================================================

echo -e "${GREEN}🎉 Separação concluída!${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos passos:${NC}"
echo ""
echo "1. Criar repositórios no GitHub:"
echo "   https://github.com/new"
echo "   - siscom-backend (privado recomendado)"
echo "   - siscom-frontend (pode ser público)"
echo ""
echo "2. Conectar e enviar Backend:"
echo "   cd $BACKEND_DIR"
echo "   git remote add origin https://github.com/janiosantos/siscom-backend.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Conectar e enviar Frontend:"
echo "   cd $FRONTEND_DIR"
echo "   git remote add origin https://github.com/janiosantos/siscom-frontend.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo -e "${YELLOW}📂 Arquivos preparados em:${NC}"
echo "   Backend:  $BACKEND_DIR"
echo "   Frontend: $FRONTEND_DIR"
echo ""
echo -e "${GREEN}✨ Pronto para push!${NC}"
