#!/bin/bash
# ==============================================================================
# SETUP SCRIPT - Initial Setup for Production/Staging
# ==============================================================================
set -e

echo "=========================================="
echo "SISCOM ERP - Setup Inicial"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Por favor, execute como root ou com sudo${NC}"
    exit 1
fi

# Detect environment
if [ -f ".env" ]; then
    source .env
    ENVIRONMENT=${ENVIRONMENT:-development}
else
    echo -e "${YELLOW}Arquivo .env não encontrado!${NC}"
    read -p "Qual ambiente deseja configurar? (staging/production): " ENVIRONMENT
fi

echo -e "${GREEN}Configurando ambiente: $ENVIRONMENT${NC}"

# ==============================================================================
# 1. Install Docker and Docker Compose
# ==============================================================================
echo ""
echo "1. Verificando Docker..."
if ! command -v docker &> /dev/null; then
    echo "Instalando Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
else
    echo -e "${GREEN}Docker já instalado: $(docker --version)${NC}"
fi

echo ""
echo "2. Verificando Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "Instalando Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}Docker Compose já instalado: $(docker-compose --version)${NC}"
fi

# ==============================================================================
# 2. Create directories
# ==============================================================================
echo ""
echo "3. Criando diretórios necessários..."
mkdir -p logs
mkdir -p backups
mkdir -p nginx/ssl
mkdir -p nginx/logs
mkdir -p certificados
chmod 700 certificados  # Apenas root pode acessar

echo -e "${GREEN}Diretórios criados${NC}"

# ==============================================================================
# 3. Configure environment file
# ==============================================================================
echo ""
echo "4. Configurando variáveis de ambiente..."

if [ "$ENVIRONMENT" == "production" ]; then
    ENV_FILE=".env.production"
elif [ "$ENVIRONMENT" == "staging" ]; then
    ENV_FILE=".env.staging"
else
    ENV_FILE=".env.example"
fi

if [ ! -f ".env" ]; then
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" .env
        echo -e "${YELLOW}Arquivo .env criado a partir de $ENV_FILE${NC}"
        echo -e "${YELLOW}IMPORTANTE: Edite o arquivo .env e configure as variáveis!${NC}"
        read -p "Pressione Enter para editar o arquivo .env agora..."
        ${EDITOR:-nano} .env
    else
        echo -e "${RED}Arquivo $ENV_FILE não encontrado!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Arquivo .env já existe${NC}"
fi

# ==============================================================================
# 4. Generate SSL certificates (if needed)
# ==============================================================================
echo ""
echo "5. Certificados SSL..."

if [ ! -f "nginx/ssl/fullchain.pem" ]; then
    echo -e "${YELLOW}Certificados SSL não encontrados${NC}"
    read -p "Deseja gerar certificados auto-assinados para testes? (s/n): " GENERATE_SSL

    if [ "$GENERATE_SSL" == "s" ] || [ "$GENERATE_SSL" == "S" ]; then
        echo "Gerando certificados auto-assinados..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/privkey.pem \
            -out nginx/ssl/fullchain.pem \
            -subj "/C=BR/ST=State/L=City/O=Organization/CN=localhost"
        echo -e "${GREEN}Certificados auto-assinados criados${NC}"
        echo -e "${YELLOW}Para produção, use Let's Encrypt ou certificados válidos!${NC}"
    else
        echo -e "${YELLOW}Coloque os certificados em nginx/ssl/${NC}"
        echo "  - nginx/ssl/fullchain.pem"
        echo "  - nginx/ssl/privkey.pem"
    fi
else
    echo -e "${GREEN}Certificados SSL encontrados${NC}"
fi

# ==============================================================================
# 5. Build images
# ==============================================================================
echo ""
echo "6. Construindo imagens Docker..."

if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml build --no-cache
else
    docker-compose build
fi

echo -e "${GREEN}Imagens construídas com sucesso${NC}"

# ==============================================================================
# 6. Initialize database
# ==============================================================================
echo ""
echo "7. Inicializando banco de dados..."

# Start only database first
if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml up -d postgres redis
else
    docker-compose up -d postgres redis
fi

# Wait for database to be ready
echo "Aguardando banco de dados ficar pronto..."
sleep 10

# Run migrations
echo "Executando migrações..."
if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
else
    docker-compose run --rm backend alembic upgrade head
fi

# Initialize auth system
echo "Inicializando sistema de autenticação..."
if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml run --rm backend python scripts/init_auth.py
else
    docker-compose run --rm backend python scripts/init_auth.py
fi

echo -e "${GREEN}Banco de dados inicializado${NC}"

# ==============================================================================
# 7. Start all services
# ==============================================================================
echo ""
echo "8. Iniciando todos os serviços..."

if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml up -d
else
    docker-compose up -d
fi

echo -e "${GREEN}Serviços iniciados${NC}"

# ==============================================================================
# 8. Show status
# ==============================================================================
echo ""
echo "9. Verificando status dos serviços..."
sleep 5

if [ "$ENVIRONMENT" == "production" ]; then
    docker-compose -f docker-compose.prod.yml ps
else
    docker-compose ps
fi

# ==============================================================================
# Final instructions
# ==============================================================================
echo ""
echo "=========================================="
echo -e "${GREEN}Setup concluído com sucesso!${NC}"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo "1. Acesse o sistema:"
if [ "$ENVIRONMENT" == "production" ]; then
    echo "   - Frontend: https://seudominio.com"
    echo "   - API Docs: https://seudominio.com/docs"
    echo "   - Metabase: https://seudominio.com/metabase"
else
    echo "   - Frontend: http://localhost:3000"
    echo "   - API Docs: http://localhost:8000/docs"
    echo "   - Metabase: http://localhost:3001"
fi
echo ""
echo "2. Usuário admin padrão:"
echo "   - Email: admin@siscom.com"
echo "   - Senha: admin123 (ALTERE IMEDIATAMENTE!)"
echo ""
echo "3. Monitore os logs:"
if [ "$ENVIRONMENT" == "production" ]; then
    echo "   docker-compose -f docker-compose.prod.yml logs -f"
else
    echo "   docker-compose logs -f"
fi
echo ""
echo "4. Para parar os serviços:"
if [ "$ENVIRONMENT" == "production" ]; then
    echo "   docker-compose -f docker-compose.prod.yml down"
else
    echo "   docker-compose down"
fi
echo ""
echo -e "${YELLOW}IMPORTANTE: Revise as configurações de segurança!${NC}"
echo "Veja: docs/DEPLOYMENT.md"
echo ""
