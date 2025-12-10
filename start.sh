#!/bin/bash

echo "🚀 Iniciando SISCOM Backend..."
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado. Criando..."
    cat > .env << 'EOF'
# Database - SQLite para desenvolvimento
DATABASE_URL=sqlite+aiosqlite:///./siscom.db

# Redis - Porta 6380 para evitar conflito com Redis local
REDIS_URL=redis://localhost:6380/0

# Application
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
APP_NAME=SISCOM ERP
APP_VERSION=1.0.0

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
EOF
    echo "✅ Arquivo .env criado"
    echo ""
fi

# Verificar se banco existe
if [ ! -f siscom.db ]; then
    echo "📦 Banco de dados não encontrado. Será criado automaticamente..."
    echo ""
fi

# Iniciar servidor
echo "🌐 Servidor iniciando em http://0.0.0.0:8000"
echo "📖 Documentação disponível em http://0.0.0.0:8000/docs"
echo ""
echo "Pressione Ctrl+C para parar"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
