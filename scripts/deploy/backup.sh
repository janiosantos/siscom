#!/bin/bash
# ==============================================================================
# BACKUP SCRIPT - Backup Database and Files
# ==============================================================================
set -e

echo "=========================================="
echo "SISCOM ERP - Backup"
echo "=========================================="

# Colors
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

# Variables
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="siscom_backup_${TIMESTAMP}"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

mkdir -p "$BACKUP_DIR"

echo "Criando backup: $BACKUP_NAME"

# ==============================================================================
# 1. Backup Database
# ==============================================================================
echo ""
echo "1. Fazendo backup do banco de dados..."

if [ "$ENVIRONMENT" == "production" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
else
    COMPOSE_FILE="docker-compose.yml"
fi

docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --clean \
    --if-exists \
    --verbose \
    > "$BACKUP_DIR/${BACKUP_NAME}_database.sql"

echo -e "${GREEN}Backup do banco concluído${NC}"

# ==============================================================================
# 2. Backup Redis (optional)
# ==============================================================================
echo ""
echo "2. Fazendo backup do Redis..."

docker-compose -f "$COMPOSE_FILE" exec -T redis \
    redis-cli --rdb "/data/dump.rdb" SAVE

docker cp $(docker-compose -f "$COMPOSE_FILE" ps -q redis):/data/dump.rdb \
    "$BACKUP_DIR/${BACKUP_NAME}_redis.rdb" 2>/dev/null || echo "Redis backup skipped"

# ==============================================================================
# 3. Backup important files
# ==============================================================================
echo ""
echo "3. Fazendo backup de arquivos importantes..."

tar -czf "$BACKUP_DIR/${BACKUP_NAME}_files.tar.gz" \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.next' \
    --exclude='venv' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='logs' \
    --exclude='backups' \
    .env \
    certificados/ \
    nginx/ssl/ 2>/dev/null || echo "Some files may not exist"

echo -e "${GREEN}Backup de arquivos concluído${NC}"

# ==============================================================================
# 4. Compress everything
# ==============================================================================
echo ""
echo "4. Comprimindo backup completo..."

cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}_complete.tar.gz" \
    "${BACKUP_NAME}_database.sql" \
    "${BACKUP_NAME}_redis.rdb" \
    "${BACKUP_NAME}_files.tar.gz" 2>/dev/null

# Remove individual files
rm -f "${BACKUP_NAME}_database.sql" \
      "${BACKUP_NAME}_redis.rdb" \
      "${BACKUP_NAME}_files.tar.gz"

cd - > /dev/null

BACKUP_SIZE=$(du -h "$BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz" | cut -f1)
echo -e "${GREEN}Backup completo criado: ${BACKUP_NAME}_complete.tar.gz (${BACKUP_SIZE})${NC}"

# ==============================================================================
# 5. Upload to S3 (if configured)
# ==============================================================================
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    echo ""
    echo "5. Enviando backup para S3..."

    aws s3 cp "$BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz" \
        "s3://${BACKUP_S3_BUCKET}/backups/${BACKUP_NAME}_complete.tar.gz" \
        --region "${BACKUP_S3_REGION:-us-east-1}" && \
    echo -e "${GREEN}Backup enviado para S3${NC}" || \
    echo -e "${YELLOW}Falha ao enviar para S3 (AWS CLI pode não estar configurado)${NC}"
fi

# ==============================================================================
# 6. Clean old backups
# ==============================================================================
echo ""
echo "6. Limpando backups antigos (mais de ${RETENTION_DAYS} dias)..."

find "$BACKUP_DIR" -name "siscom_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
REMAINING=$(ls -1 "$BACKUP_DIR"/siscom_backup_*.tar.gz 2>/dev/null | wc -l)
echo "Backups restantes: $REMAINING"

# ==============================================================================
# Summary
# ==============================================================================
echo ""
echo "=========================================="
echo -e "${GREEN}Backup concluído com sucesso!${NC}"
echo "=========================================="
echo ""
echo "Arquivo de backup: $BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz"
echo "Tamanho: $BACKUP_SIZE"
echo ""
echo "Para restaurar:"
echo "  ./scripts/deploy/restore.sh $BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz"
echo ""
