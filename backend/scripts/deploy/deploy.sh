#!/bin/bash
# ==============================================================================
# DEPLOY SCRIPT - Deploy/Update Application
# ==============================================================================
set -e

echo "=========================================="
echo "SISCOM ERP - Deploy/Atualização"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment
if [ -f ".env" ]; then
    source .env
    ENVIRONMENT=${ENVIRONMENT:-development}
else
    echo -e "${RED}Arquivo .env não encontrado!${NC}"
    exit 1
fi

echo -e "${GREEN}Ambiente: $ENVIRONMENT${NC}"

# Confirm deployment
if [ "$ENVIRONMENT" == "production" ]; then
    echo -e "${RED}ATENÇÃO: Você está fazendo deploy em PRODUÇÃO!${NC}"
    read -p "Tem certeza que deseja continuar? (sim/não): " CONFIRM
    if [ "$CONFIRM" != "sim" ]; then
        echo "Deploy cancelado"
        exit 0
    fi
fi

# ==============================================================================
# 1. Backup before deploy
# ==============================================================================
echo ""
echo "1. Criando backup pré-deploy..."
./scripts/deploy/backup.sh

# ==============================================================================
# 2. Pull latest code
# ==============================================================================
echo ""
echo "2. Atualizando código..."
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Branch atual: $CURRENT_BRANCH"

read -p "Fazer pull da branch atual? (s/n): " PULL_CODE
if [ "$PULL_CODE" == "s" ] || [ "$PULL_CODE" == "S" ]; then
    git pull origin $CURRENT_BRANCH
    echo -e "${GREEN}Código atualizado${NC}"
fi

# ==============================================================================
# 3. Rebuild images
# ==============================================================================
echo ""
echo "3. Reconstruindo imagens..."

if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml build --no-cache
else
    docker-compose build
fi

echo -e "${GREEN}Imagens reconstruídas${NC}"

# ==============================================================================
# 4. Run database migrations
# ==============================================================================
echo ""
echo "4. Executando migrações do banco de dados..."

if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
else
    docker-compose run --rm backend alembic upgrade head
fi

echo -e "${GREEN}Migrações executadas${NC}"

# ==============================================================================
# 5. Restart services with zero-downtime
# ==============================================================================
echo ""
echo "5. Reiniciando serviços..."

if [ "$ENVIRONMENT" == "production" ]; then
    # Rolling restart for zero-downtime
    docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend
    sleep 5
    docker-compose -f docker-compose.prod.yml up -d --no-deps --build frontend
    sleep 5
    docker-compose -f docker-compose.prod.yml restart nginx
else
    docker-compose up -d
fi

echo -e "${GREEN}Serviços reiniciados${NC}"

# ==============================================================================
# 6. Health check
# ==============================================================================
echo ""
echo "6. Verificando saúde dos serviços..."
sleep 10

./scripts/deploy/health-check.sh

# ==============================================================================
# 7. Show logs
# ==============================================================================
echo ""
echo "7. Últimas linhas dos logs:"
if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml logs --tail=50 backend frontend
else
    docker-compose logs --tail=50 backend frontend
fi

# ==============================================================================
# Final status
# ==============================================================================
echo ""
echo "=========================================="
echo -e "${GREEN}Deploy concluído com sucesso!${NC}"
echo "=========================================="
echo ""
echo "Serviços rodando:"
if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml ps
else
    docker-compose ps
fi
echo ""
echo "Para monitorar:"
if [ "$ENVIRONMENT" == "production" ]; then
    echo "  docker-compose -f docker-compose.prod.yml logs -f"
else
    echo "  docker-compose logs -f"
fi
echo ""
