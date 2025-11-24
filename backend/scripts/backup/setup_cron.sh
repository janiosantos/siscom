#!/bin/bash

###############################################################################
# Script para Configurar Backups Automáticos via Cron
#
# Descrição: Configura crontab para executar backups automáticos
# Uso: ./setup_cron.sh
# Autor: Sistema ERP
# Data: 2025-11-19
###############################################################################

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"

echo -e "${YELLOW}Configurando backups automáticos via cron${NC}"
echo ""

# Torna scripts executáveis
chmod +x "$SCRIPT_DIR/backup.sh"
chmod +x "$SCRIPT_DIR/restore.sh"

echo "Scripts tornados executáveis"
echo ""

# Sugestões de agendamento
echo "Sugestões de agendamento:"
echo ""
echo "1. Backup diário às 2h da manhã:"
echo "   0 2 * * * $BACKUP_SCRIPT daily >> /var/log/erp_backup.log 2>&1"
echo ""
echo "2. Backup semanal aos domingos às 3h:"
echo "   0 3 * * 0 $BACKUP_SCRIPT weekly >> /var/log/erp_backup.log 2>&1"
echo ""
echo "3. Backup mensal no dia 1 às 4h:"
echo "   0 4 1 * * $BACKUP_SCRIPT monthly >> /var/log/erp_backup.log 2>&1"
echo ""
echo "4. Todos os backups (recomendado):"
echo "   0 2 * * * $BACKUP_SCRIPT daily >> /var/log/erp_backup.log 2>&1"
echo "   0 3 * * 0 $BACKUP_SCRIPT weekly >> /var/log/erp_backup.log 2>&1"
echo "   0 4 1 * * $BACKUP_SCRIPT monthly >> /var/log/erp_backup.log 2>&1"
echo ""

# Pergunta se deseja configurar automaticamente
read -p "Deseja configurar backups automáticos agora? (s/N): " configure

if [[ "$configure" =~ ^[Ss]$ ]]; then
    # Cria arquivo temporário com crontab atual
    crontab -l > /tmp/crontab_temp 2>/dev/null || true

    # Remove entradas antigas do ERP (se existirem)
    sed -i '/# ERP Backup/d' /tmp/crontab_temp
    sed -i "$BACKUP_SCRIPT/d" /tmp/crontab_temp

    # Adiciona novas entradas
    echo "" >> /tmp/crontab_temp
    echo "# ERP Backup - Daily (2h)" >> /tmp/crontab_temp
    echo "0 2 * * * $BACKUP_SCRIPT daily >> /var/log/erp_backup.log 2>&1" >> /tmp/crontab_temp
    echo "" >> /tmp/crontab_temp
    echo "# ERP Backup - Weekly (Sunday 3h)" >> /tmp/crontab_temp
    echo "0 3 * * 0 $BACKUP_SCRIPT weekly >> /var/log/erp_backup.log 2>&1" >> /tmp/crontab_temp
    echo "" >> /tmp/crontab_temp
    echo "# ERP Backup - Monthly (1st day 4h)" >> /tmp/crontab_temp
    echo "0 4 1 * * $BACKUP_SCRIPT monthly >> /var/log/erp_backup.log 2>&1" >> /tmp/crontab_temp

    # Instala novo crontab
    crontab /tmp/crontab_temp
    rm /tmp/crontab_temp

    echo -e "${GREEN}Backups automáticos configurados com sucesso!${NC}"
    echo ""
    echo "Agendamento:"
    echo "  - Diário: Todos os dias às 2h"
    echo "  - Semanal: Domingos às 3h"
    echo "  - Mensal: Dia 1 de cada mês às 4h"
    echo ""
    echo "Logs: /var/log/erp_backup.log"
    echo ""
    echo "Para listar cron jobs: crontab -l"
    echo "Para editar cron jobs: crontab -e"
else
    echo "Configure manualmente usando: crontab -e"
fi

echo ""
echo -e "${GREEN}Setup concluído!${NC}"
