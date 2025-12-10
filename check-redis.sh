#!/bin/bash

echo "🔍 Verificando Redis..."
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para testar conexão
test_redis() {
    local port=$1
    if redis-cli -h localhost -p $port ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis rodando na porta $port${NC}"

        # Mostrar informações
        echo ""
        echo "📊 Informações:"
        redis-cli -h localhost -p $port INFO server | grep -E "redis_version|tcp_port|uptime_in_seconds" | sed 's/^/  /'

        # Estatísticas
        echo ""
        echo "📈 Estatísticas:"
        redis-cli -h localhost -p $port INFO stats | grep -E "total_connections_received|total_commands_processed|instantaneous_ops_per_sec" | sed 's/^/  /'

        # Memória
        echo ""
        echo "💾 Memória:"
        redis-cli -h localhost -p $port INFO memory | grep -E "used_memory_human|maxmemory_human" | sed 's/^/  /'

        # Número de chaves
        echo ""
        echo "🔑 Chaves:"
        local keys=$(redis-cli -h localhost -p $port DBSIZE)
        echo "  Total de chaves: $keys"

        return 0
    else
        echo -e "${RED}❌ Redis NÃO está rodando na porta $port${NC}"
        return 1
    fi
}

# Verificar se redis-cli está instalado
if ! command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}⚠️  redis-cli não está instalado${NC}"
    echo ""
    echo "Instale com:"
    echo "  Ubuntu/Debian: sudo apt install redis-tools"
    echo "  Mac: brew install redis"
    echo ""
fi

# Testar portas comuns
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Porta 6380 (configuração do projeto):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if test_redis 6380; then
    FOUND_6380=true
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Porta 6379 (padrão do Redis):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if test_redis 6379; then
    FOUND_6379=true
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar processos
echo ""
echo "🔍 Processos Redis:"
if command -v lsof &> /dev/null; then
    REDIS_PROCS=$(sudo lsof -i -P -n 2>/dev/null | grep redis || echo "")
    if [ -n "$REDIS_PROCS" ]; then
        echo "$REDIS_PROCS" | sed 's/^/  /'
    else
        echo "  Nenhum processo Redis encontrado"
    fi
else
    echo "  (lsof não disponível)"
fi

# Verificar Docker
echo ""
echo "🐳 Containers Docker Redis:"
if command -v docker &> /dev/null; then
    REDIS_CONTAINERS=$(docker ps --filter "name=redis" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "")
    if [ -n "$REDIS_CONTAINERS" ] && [ "$REDIS_CONTAINERS" != "NAMES	STATUS	PORTS" ]; then
        echo "$REDIS_CONTAINERS" | sed 's/^/  /'
    else
        echo "  Nenhum container Redis rodando"
    fi
else
    echo "  (Docker não disponível)"
fi

# Resumo e recomendações
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Resumo:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$FOUND_6380" = true ]; then
    echo -e "${GREEN}✅ Redis configurado corretamente (porta 6380)${NC}"
    echo ""
    echo "Para conectar:"
    echo "  redis-cli -p 6380"
elif [ "$FOUND_6379" = true ]; then
    echo -e "${YELLOW}⚠️  Redis rodando na porta padrão (6379)${NC}"
    echo ""
    echo "Recomendação: Use porta 6380 para evitar conflitos"
    echo "  docker-compose -f docker-compose.dev.yml up -d redis"
else
    echo -e "${RED}❌ Redis não está rodando${NC}"
    echo ""
    echo "Para iniciar Redis:"
    echo ""
    echo "Opção 1 - Docker Compose (recomendado):"
    echo "  docker-compose -f docker-compose.dev.yml up -d redis"
    echo ""
    echo "Opção 2 - Docker standalone:"
    echo "  docker run -d -p 6380:6379 --name redis-dev redis:7-alpine"
    echo ""
    echo "Opção 3 - Sem Redis:"
    echo "  O backend funciona sem Redis (usa memória local)"
    echo "  Apenas execute: ./start.sh"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Mais informações: cat REDIS_GUIDE.md"
