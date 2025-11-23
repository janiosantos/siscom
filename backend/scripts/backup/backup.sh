#!/bin/bash

###############################################################################
# Script de Backup Automático do PostgreSQL
#
# Descrição: Realiza backup completo do banco de dados PostgreSQL
# Uso: ./backup.sh [daily|weekly|monthly]
# Autor: Sistema ERP
# Data: 2025-11-19
###############################################################################

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações (sobrescritas por .env se existir)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Carrega variáveis do .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
fi

# Configurações de banco de dados
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-erp_db}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

# Diretórios de backup
BACKUP_ROOT="${BACKUP_ROOT:-$PROJECT_ROOT/backups}"
BACKUP_TYPE="${1:-daily}"  # daily, weekly, monthly

# Cria estrutura de diretórios
BACKUP_DIR="$BACKUP_ROOT/$BACKUP_TYPE"
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_ROOT/logs"

# Nome do arquivo de backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/erp_backup_${BACKUP_TYPE}_${TIMESTAMP}.sql"
BACKUP_FILE_GZ="${BACKUP_FILE}.gz"
LOG_FILE="$BACKUP_ROOT/logs/backup_${TIMESTAMP}.log"

# Retenção (dias)
case "$BACKUP_TYPE" in
    daily)
        RETENTION_DAYS=7
        ;;
    weekly)
        RETENTION_DAYS=30
        ;;
    monthly)
        RETENTION_DAYS=365
        ;;
    *)
        echo -e "${RED}Erro: Tipo de backup inválido. Use: daily, weekly ou monthly${NC}"
        exit 1
        ;;
esac

###############################################################################
# Funções
###############################################################################

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

check_dependencies() {
    log "Verificando dependências..."

    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump não encontrado. Instale o PostgreSQL client."
        exit 1
    fi

    if ! command -v gzip &> /dev/null; then
        log_error "gzip não encontrado."
        exit 1
    fi

    log_success "Dependências OK"
}

test_connection() {
    log "Testando conexão com banco de dados..."

    export PGPASSWORD="$DB_PASSWORD"

    if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        log_error "Não foi possível conectar ao banco de dados"
        exit 1
    fi

    log_success "Conexão com banco de dados OK"
}

perform_backup() {
    log "Iniciando backup do banco de dados..."
    log "Tipo: $BACKUP_TYPE"
    log "Arquivo: $BACKUP_FILE_GZ"

    export PGPASSWORD="$DB_PASSWORD"

    # Executa pg_dump
    if pg_dump -h "$DB_HOST" \
               -p "$DB_PORT" \
               -U "$DB_USER" \
               -d "$DB_NAME" \
               --format=plain \
               --no-owner \
               --no-acl \
               --verbose \
               -f "$BACKUP_FILE" 2>> "$LOG_FILE"; then

        log_success "Backup SQL criado: $BACKUP_FILE"

        # Comprime o backup
        log "Comprimindo backup..."
        if gzip -f "$BACKUP_FILE"; then
            log_success "Backup comprimido: $BACKUP_FILE_GZ"

            # Mostra tamanho do arquivo
            BACKUP_SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
            log "Tamanho do backup: $BACKUP_SIZE"
        else
            log_error "Erro ao comprimir backup"
            exit 1
        fi
    else
        log_error "Erro ao criar backup"
        exit 1
    fi

    unset PGPASSWORD
}

verify_backup() {
    log "Verificando integridade do backup..."

    if [ -f "$BACKUP_FILE_GZ" ]; then
        if gzip -t "$BACKUP_FILE_GZ" 2>> "$LOG_FILE"; then
            log_success "Backup verificado com sucesso"
        else
            log_error "Backup corrompido!"
            exit 1
        fi
    else
        log_error "Arquivo de backup não encontrado"
        exit 1
    fi
}

cleanup_old_backups() {
    log "Removendo backups antigos (retenção: $RETENTION_DAYS dias)..."

    DELETED_COUNT=0

    # Remove backups mais antigos que RETENTION_DAYS
    find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS | while read -r old_backup; do
        log "Removendo: $old_backup"
        rm -f "$old_backup"
        ((DELETED_COUNT++))
    done

    if [ $DELETED_COUNT -gt 0 ]; then
        log "Removidos $DELETED_COUNT backup(s) antigo(s)"
    else
        log "Nenhum backup antigo para remover"
    fi

    # Remove logs antigos (90 dias)
    find "$BACKUP_ROOT/logs" -name "*.log" -type f -mtime +90 -delete
}

send_notification() {
    local status=$1
    local message=$2

    # Aqui você pode implementar notificações via:
    # - Email (usando sendmail, mailx, etc)
    # - Slack
    # - Telegram
    # - Discord
    # - etc

    log "Notificação: [$status] $message"

    # Exemplo com email (descomente se configurado):
    # if command -v mail &> /dev/null; then
    #     echo "$message" | mail -s "Backup ERP - $status" admin@example.com
    # fi
}

generate_report() {
    log "==================== RELATÓRIO DE BACKUP ===================="
    log "Tipo: $BACKUP_TYPE"
    log "Data/Hora: $(date '+%Y-%m-%d %H:%M:%S')"
    log "Banco: $DB_NAME@$DB_HOST:$DB_PORT"
    log "Arquivo: $BACKUP_FILE_GZ"

    if [ -f "$BACKUP_FILE_GZ" ]; then
        log "Tamanho: $(du -h "$BACKUP_FILE_GZ" | cut -f1)"
        log "MD5: $(md5sum "$BACKUP_FILE_GZ" | cut -d' ' -f1)"
    fi

    log "Retenção: $RETENTION_DAYS dias"
    log "Backups existentes em $BACKUP_DIR: $(find "$BACKUP_DIR" -name "*.sql.gz" | wc -l)"
    log "==========================================================="
}

###############################################################################
# Main
###############################################################################

main() {
    log "========== INICIANDO BACKUP DO BANCO DE DADOS =========="

    check_dependencies
    test_connection
    perform_backup
    verify_backup
    cleanup_old_backups
    generate_report

    log_success "Backup concluído com sucesso!"
    send_notification "SUCCESS" "Backup $BACKUP_TYPE concluído com sucesso"

    exit 0
}

# Executa main e captura erros
if ! main; then
    log_error "Backup falhou!"
    send_notification "FAILED" "Backup $BACKUP_TYPE falhou. Verifique os logs."
    exit 1
fi
