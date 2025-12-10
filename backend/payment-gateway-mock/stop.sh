#!/bin/bash
#
# Script para parar o Payment Gateway Mock Service
#

echo "🛑 Parando Payment Gateway Mock Service..."

# Tentar parar via Docker Compose
if [ -f docker-compose.yml ] && command -v docker-compose &> /dev/null; then
    docker-compose down
    echo "✅ Serviço Docker parado"
fi

# Tentar parar via PID file
if [ -f .mock-service.pid ]; then
    PID=$(cat .mock-service.pid)
    if kill $PID 2>/dev/null; then
        echo "✅ Serviço Python parado (PID: $PID)"
        rm .mock-service.pid
    fi
fi

# Fallback: matar processo por nome
pkill -f "uvicorn app.main:app" && echo "✅ Processos uvicorn parados"

echo "✅ Serviço parado"
