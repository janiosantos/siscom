#!/bin/bash
# ==============================================================================
# HEALTH CHECK SCRIPT - Verify Services Health
# ==============================================================================
set -e

echo "=========================================="
echo "SISCOM ERP - Health Check"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment
if [ -f ".env" ]; then
    source .env
else
    echo "Arquivo .env não encontrado!"
    exit 1
fi

ALL_HEALTHY=true

# ==============================================================================
# Helper Functions
# ==============================================================================
check_service() {
    SERVICE=$1
    URL=$2
    EXPECTED_STATUS=${3:-200}

    echo -n "Verificando $SERVICE... "

    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL" --max-time 10 2>/dev/null || echo "000")

    if [ "$STATUS" == "$EXPECTED_STATUS" ]; then
        echo -e "${GREEN}✓ OK (HTTP $STATUS)${NC}"
        return 0
    else
        echo -e "${RED}✗ FALHOU (HTTP $STATUS)${NC}"
        ALL_HEALTHY=false
        return 1
    fi
}

check_docker_service() {
    SERVICE=$1
    echo -n "Verificando container $SERVICE... "

    if [ "$ENVIRONMENT" == "production" ]; then
        CONTAINER=$(docker-compose -f docker-compose.prod.yml ps -q $SERVICE 2>/dev/null)
    else
        CONTAINER=$(docker-compose ps -q $SERVICE 2>/dev/null)
    fi

    if [ -z "$CONTAINER" ]; then
        echo -e "${RED}✗ Container não encontrado${NC}"
        ALL_HEALTHY=false
        return 1
    fi

    STATUS=$(docker inspect -f '{{.State.Health.Status}}' $CONTAINER 2>/dev/null || echo "none")

    if [ "$STATUS" == "healthy" ] || [ "$STATUS" == "none" ]; then
        # If no healthcheck, check if running
        if [ "$STATUS" == "none" ]; then
            RUNNING=$(docker inspect -f '{{.State.Running}}' $CONTAINER)
            if [ "$RUNNING" == "true" ]; then
                echo -e "${GREEN}✓ Rodando${NC}"
                return 0
            fi
        else
            echo -e "${GREEN}✓ Saudável${NC}"
            return 0
        fi
    fi

    echo -e "${RED}✗ Não saudável (Status: $STATUS)${NC}"
    ALL_HEALTHY=false
    return 1
}

# ==============================================================================
# Check Docker Containers
# ==============================================================================
echo ""
echo "1. Verificando containers Docker:"
check_docker_service postgres
check_docker_service redis
check_docker_service backend
check_docker_service frontend

if [ "$ENVIRONMENT" == "production" ]; then
    check_docker_service nginx
fi

# ==============================================================================
# Check HTTP Endpoints
# ==============================================================================
echo ""
echo "2. Verificando endpoints HTTP:"

if [ "$ENVIRONMENT" == "production" ]; then
    # Production URLs
    check_service "Backend Health" "https://localhost/health" 200
    check_service "Backend API Docs" "https://localhost/docs" 200
    check_service "Frontend" "https://localhost" 200
else
    # Development URLs
    check_service "Backend Health" "http://localhost:8000/health" 200
    check_service "Backend API Docs" "http://localhost:8000/docs" 200
    check_service "Frontend" "http://localhost:3000" 200
fi

# ==============================================================================
# Check Database Connection
# ==============================================================================
echo ""
echo "3. Verificando conexão com banco de dados:"

if [ "$ENVIRONMENT" == "production" ]; then
    DB_CHECK=$(docker-compose -f docker-compose.prod.yml exec -T postgres \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" 2>/dev/null || echo "FAILED")
else
    DB_CHECK=$(docker-compose exec -T postgres \
        psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" 2>/dev/null || echo "FAILED")
fi

if [[ "$DB_CHECK" == *"1 row"* ]]; then
    echo -e "${GREEN}✓ Banco de dados conectado${NC}"
else
    echo -e "${RED}✗ Falha na conexão com banco de dados${NC}"
    ALL_HEALTHY=false
fi

# ==============================================================================
# Check Redis Connection
# ==============================================================================
echo ""
echo "4. Verificando conexão com Redis:"

if [ "$ENVIRONMENT" == "production" ]; then
    REDIS_CHECK=$(docker-compose -f docker-compose.prod.yml exec -T redis \
        redis-cli -a "$REDIS_PASSWORD" PING 2>/dev/null || echo "FAILED")
else
    REDIS_CHECK=$(docker-compose exec -T redis \
        redis-cli -a "$REDIS_PASSWORD" PING 2>/dev/null || echo "FAILED")
fi

if [ "$REDIS_CHECK" == "PONG" ]; then
    echo -e "${GREEN}✓ Redis conectado${NC}"
else
    echo -e "${RED}✗ Falha na conexão com Redis${NC}"
    ALL_HEALTHY=false
fi

# ==============================================================================
# Check Disk Space
# ==============================================================================
echo ""
echo "5. Verificando espaço em disco:"

DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓ Espaço em disco: ${DISK_USAGE}%${NC}"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠ Espaço em disco: ${DISK_USAGE}% (Atenção!)${NC}"
else
    echo -e "${RED}✗ Espaço em disco: ${DISK_USAGE}% (Crítico!)${NC}"
    ALL_HEALTHY=false
fi

# ==============================================================================
# Check Memory Usage
# ==============================================================================
echo ""
echo "6. Verificando uso de memória:"

MEMORY_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')

if [ "$MEMORY_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓ Uso de memória: ${MEMORY_USAGE}%${NC}"
elif [ "$MEMORY_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠ Uso de memória: ${MEMORY_USAGE}% (Atenção!)${NC}"
else
    echo -e "${RED}✗ Uso de memória: ${MEMORY_USAGE}% (Crítico!)${NC}"
    ALL_HEALTHY=false
fi

# ==============================================================================
# Summary
# ==============================================================================
echo ""
echo "=========================================="
if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✓ Todos os serviços estão saudáveis!${NC}"
    echo "=========================================="
    exit 0
else
    echo -e "${RED}✗ Alguns serviços não estão saudáveis!${NC}"
    echo "=========================================="
    echo ""
    echo "Para ver logs:"
    if [ "$ENVIRONMENT" == "production" ]; then
        echo "  docker-compose -f docker-compose.prod.yml logs -f"
    else
        echo "  docker-compose logs -f"
    fi
    exit 1
fi
