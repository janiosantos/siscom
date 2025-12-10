#!/bin/bash
#
# Script para iniciar o Payment Gateway Mock Service
#

echo "🚀 Iniciando Payment Gateway Mock Service..."

# Opção 1: Docker (recomendado)
if command -v docker-compose &> /dev/null; then
    echo "Usando Docker Compose..."
    docker-compose up -d
    echo "✅ Serviço iniciado em http://localhost:8001"
    echo "📚 Documentação: http://localhost:8001/docs"
    echo "📊 Estatísticas: http://localhost:8001/admin/stats"
    echo ""
    echo "Para ver logs: docker-compose logs -f"
    echo "Para parar: docker-compose down"

# Opção 2: Python local
elif command -v python3 &> /dev/null; then
    echo "Usando Python local..."
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload &
    PID=$!
    echo $PID > .mock-service.pid
    echo "✅ Serviço iniciado (PID: $PID) em http://localhost:8001"
    echo "📚 Documentação: http://localhost:8001/docs"
    echo "📊 Estatísticas: http://localhost:8001/admin/stats"
    echo ""
    echo "Para parar: ./stop.sh ou kill $PID"

else
    echo "❌ Erro: Docker Compose ou Python3 não encontrado"
    exit 1
fi
