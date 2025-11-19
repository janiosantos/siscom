#!/bin/bash

###############################################################################
# Script de Restore do PostgreSQL
#
# Descrição: Restaura backup do banco de dados PostgreSQL
# Uso: ./restore.sh <arquivo_backup.sql.gz>
# Autor: Sistema ERP
# Data: 2025-11-19
###############################################################################

set -e  # Exit on error

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações
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

# Arquivo de backup
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}Erro: Informe o arquivo de backup${NC}"
    echo "Uso: $0 <arquivo_backup.sql.gz>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Erro: Arquivo não encontrado: $BACKUP_FILE${NC}"
    exit 1
fi

###############################################################################
# Funções
###############################################################################

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

confirm_restore() {
    echo ""
    log_warning "============================================"
    log_warning "ATENÇÃO: Esta operação irá SOBRESCREVER"
    log_warning "todos os dados do banco de dados:"
    log_warning "  Database: $DB_NAME"
    log_warning "  Host: $DB_HOST:$DB_PORT"
    log_warning "============================================"
    echo ""
    read -p "Tem certeza que deseja continuar? (digite 'SIM' para confirmar): " confirm

    if [ "$confirm" != "SIM" ]; then
        log "Restore cancelado pelo usuário"
        exit 0
    fi
}

verify_backup() {
    log "Verificando integridade do backup..."

    if gzip -t "$BACKUP_FILE" 2>/dev/null; then
        log_success "Backup verificado com sucesso"
    else
        log_error "Backup corrompido!"
        exit 1
    fi
}

create_pre_restore_backup() {
    log "Criando backup de segurança antes do restore..."

    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    PRE_RESTORE_BACKUP="$PROJECT_ROOT/backups/pre_restore_${TIMESTAMP}.sql.gz"

    mkdir -p "$PROJECT_ROOT/backups"

    export PGPASSWORD="$DB_PASSWORD"

    if pg_dump -h "$DB_HOST" \
               -p "$DB_PORT" \
               -U "$DB_USER" \
               -d "$DB_NAME" \
               --format=plain \
               --no-owner \
               --no-acl \
               2>/dev/null | gzip > "$PRE_RESTORE_BACKUP"; then
        log_success "Backup de segurança criado: $PRE_RESTORE_BACKUP"
    else
        log_warning "Não foi possível criar backup de segurança"
    fi

    unset PGPASSWORD
}

perform_restore() {
    log "Iniciando restore do banco de dados..."
    log "Arquivo: $BACKUP_FILE"

    export PGPASSWORD="$DB_PASSWORD"

    # Descomprime e restaura
    if gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" \
                                        -p "$DB_PORT" \
                                        -U "$DB_USER" \
                                        -d "$DB_NAME" \
                                        -v ON_ERROR_STOP=1 \
                                        2>/dev/null; then
        log_success "Restore concluído com sucesso!"
    else
        log_error "Erro ao restaurar backup"
        log_error "O backup de segurança está disponível em: $PRE_RESTORE_BACKUP"
        exit 1
    fi

    unset PGPASSWORD
}

verify_restore() {
    log "Verificando restore..."

    export PGPASSWORD="$DB_PASSWORD"

    # Testa conexão
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "Banco de dados acessível"

        # Conta tabelas
        TABLE_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
                           -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null)

        log "Tabelas encontradas: $TABLE_COUNT"
    else
        log_error "Não foi possível conectar ao banco de dados"
        exit 1
    fi

    unset PGPASSWORD
}

###############################################################################
# Main
###############################################################################

main() {
    log "========== INICIANDO RESTORE DO BANCO DE DADOS =========="

    verify_backup
    confirm_restore
    create_pre_restore_backup
    perform_restore
    verify_restore

    log_success "Restore concluído com sucesso!"

    exit 0
}

# Executa main
if ! main; then
    log_error "Restore falhou!"
    exit 1
fi
