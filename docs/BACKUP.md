# Sistema de Backup Automático

## Visão Geral

O sistema implementa backup automático do banco de dados PostgreSQL com:
- Backups diários, semanais e mensais
- Compressão automática (gzip)
- Rotação automática (retenção configurável)
- Verificação de integridade
- Logs detalhados
- Scripts de restore

## Estrutura de Arquivos

```
scripts/backup/
├── backup.sh          # Script principal de backup
├── restore.sh         # Script de restauração
└── setup_cron.sh      # Configuração de agendamento

backups/
├── daily/             # Backups diários (retenção: 7 dias)
├── weekly/            # Backups semanais (retenção: 30 dias)
├── monthly/           # Backups mensais (retenção: 365 dias)
└── logs/              # Logs de backup
```

## Configuração

### 1. Variáveis de Ambiente

No `.env`:

```env
# Configurações de Banco de Dados
DB_HOST=localhost
DB_PORT=5432
DB_NAME=erp_db
DB_USER=postgres
DB_PASSWORD=seu_password_seguro

# Diretório de backups (opcional)
BACKUP_ROOT=/path/to/backups  # Padrão: ./backups
```

### 2. Tornar Scripts Executáveis

```bash
chmod +x scripts/backup/backup.sh
chmod +x scripts/backup/restore.sh
chmod +x scripts/backup/setup_cron.sh
```

## Uso

### Backup Manual

#### Backup Diário

```bash
./scripts/backup/backup.sh daily
```

- **Retenção**: 7 dias
- **Uso**: Backups frequentes para recuperação rápida

#### Backup Semanal

```bash
./scripts/backup/backup.sh weekly
```

- **Retenção**: 30 dias
- **Uso**: Backups semanais para histórico médio prazo

#### Backup Mensal

```bash
./scripts/backup/backup.sh monthly
```

- **Retenção**: 365 dias (1 ano)
- **Uso**: Arquivamento de longo prazo

### Backup Automático

#### Configuração Rápida

```bash
./scripts/backup/setup_cron.sh
```

Este script configura automaticamente:
- Backup diário às 2h da manhã
- Backup semanal aos domingos às 3h
- Backup mensal no dia 1 de cada mês às 4h

#### Configuração Manual

```bash
crontab -e
```

Adicione:

```cron
# Backup diário às 2h
0 2 * * * /path/to/siscom/scripts/backup/backup.sh daily >> /var/log/erp_backup.log 2>&1

# Backup semanal aos domingos às 3h
0 3 * * 0 /path/to/siscom/scripts/backup/backup.sh weekly >> /var/log/erp_backup.log 2>&1

# Backup mensal no dia 1 às 4h
0 4 1 * * /path/to/siscom/scripts/backup/backup.sh monthly >> /var/log/erp_backup.log 2>&1
```

## Restauração

### Listar Backups Disponíveis

```bash
ls -lh backups/daily/
ls -lh backups/weekly/
ls -lh backups/monthly/
```

### Restaurar Backup

```bash
./scripts/backup/restore.sh backups/daily/erp_backup_daily_20251119_020000.sql.gz
```

**ATENÇÃO**: Restauração sobrescreve todos os dados do banco!

#### Fluxo de Restauração

1. Verifica integridade do arquivo de backup
2. Solicita confirmação (digite "SIM")
3. Cria backup de segurança do estado atual
4. Realiza restore
5. Verifica sucesso

### Restore de Emergência

Se houver problema com restore:

```bash
# O script cria backup de segurança automaticamente
# Localizado em: backups/pre_restore_TIMESTAMP.sql.gz

# Para reverter:
./scripts/backup/restore.sh backups/pre_restore_TIMESTAMP.sql.gz
```

## Recursos

### Compressão Automática

- Todos os backups são comprimidos com gzip
- Reduz espaço em disco em ~90%
- Exemplo: 1GB descomprimido → ~100MB comprimido

### Verificação de Integridade

Cada backup é automaticamente verificado:
- Teste de integridade do gzip
- Cálculo de MD5 checksum
- Registrado nos logs

### Rotação Automática

Backups antigos são removidos automaticamente:

| Tipo | Retenção |
|------|----------|
| Daily | 7 dias |
| Weekly | 30 dias |
| Monthly | 365 dias |

### Logs Detalhados

Cada backup gera log completo em `backups/logs/`:

```
[2025-11-19 02:00:00] Iniciando backup do banco de dados...
[2025-11-19 02:00:01] Tipo: daily
[2025-11-19 02:00:01] Arquivo: backups/daily/erp_backup_daily_20251119_020000.sql.gz
[2025-11-19 02:02:30] SUCCESS: Backup SQL criado
[2025-11-19 02:02:45] Tamanho do backup: 123M
[2025-11-19 02:02:45] SUCCESS: Backup verificado com sucesso
[2025-11-19 02:02:46] Removidos 3 backup(s) antigo(s)
```

## Monitoramento

### Verificar Últimos Backups

```bash
# Últimos backups diários
ls -lt backups/daily/ | head -5

# Tamanho total dos backups
du -sh backups/

# Verificar logs
tail -f backups/logs/backup_*.log
```

### Verificar Cron Jobs

```bash
# Listar jobs agendados
crontab -l

# Ver logs do cron (Ubuntu/Debian)
grep CRON /var/log/syslog

# Ver logs do cron (CentOS/RHEL)
grep CRON /var/log/cron
```

### Alertas de Falha

Edite `backup.sh` para adicionar notificações:

```bash
send_notification() {
    local status=$1
    local message=$2

    # Email
    echo "$message" | mail -s "Backup ERP - $status" admin@example.com

    # Slack
    curl -X POST -H 'Content-type: application/json' \
         --data "{\"text\":\"$message\"}" \
         YOUR_SLACK_WEBHOOK_URL

    # Telegram
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
         -d chat_id=$TELEGRAM_CHAT_ID \
         -d text="$message"
}
```

## Backup Remoto

### Para S3 (AWS)

Instalar AWS CLI:

```bash
pip install awscli
aws configure
```

Adicionar ao final de `backup.sh`:

```bash
# Upload para S3
if command -v aws &> /dev/null; then
    log "Enviando backup para S3..."
    aws s3 cp "$BACKUP_FILE_GZ" "s3://seu-bucket/backups/$BACKUP_TYPE/"
    log_success "Backup enviado para S3"
fi
```

### Para Google Cloud Storage

```bash
# Instalar gsutil
pip install gsutil

# Adicionar ao backup.sh
gsutil cp "$BACKUP_FILE_GZ" "gs://seu-bucket/backups/$BACKUP_TYPE/"
```

### Para Servidor Remoto (rsync/scp)

```bash
# Via rsync (mais eficiente)
rsync -avz --progress "$BACKUP_FILE_GZ" user@backup-server:/backups/

# Via scp
scp "$BACKUP_FILE_GZ" user@backup-server:/backups/
```

## Testes

### Testar Backup

```bash
# Executar backup de teste
./scripts/backup/backup.sh daily

# Verificar se arquivo foi criado
ls -lh backups/daily/

# Verificar integridade
gzip -t backups/daily/erp_backup_daily_*.sql.gz

# Verificar logs
cat backups/logs/backup_*.log | tail -20
```

### Testar Restore (Ambiente de Teste)

**NUNCA fazer em produção sem backup!**

```bash
# 1. Criar backup atual
./scripts/backup/backup.sh daily

# 2. Fazer mudanças no banco (para testar restore)
psql -d erp_db -c "CREATE TABLE teste_restore (id INT);"

# 3. Restaurar backup anterior
./scripts/backup/restore.sh backups/daily/erp_backup_daily_ANTERIOR.sql.gz

# 4. Verificar se tabela teste_restore foi removida
psql -d erp_db -c "\dt teste_restore"  # Não deve existir
```

## Segurança

### Permissões

```bash
# Apenas owner pode ler backups
chmod 700 backups/
chmod 600 backups/*/*.sql.gz

# Scripts executáveis apenas pelo owner
chmod 700 scripts/backup/*.sh
```

### Criptografia

Para criptografar backups:

```bash
# Backup com criptografia GPG
./scripts/backup/backup.sh daily
gpg --symmetric --cipher-algo AES256 backups/daily/erp_backup_daily_*.sql.gz

# Restore descriptografando
gpg --decrypt backups/daily/erp_backup_daily_*.sql.gz.gpg | gunzip | psql -d erp_db
```

### .pgpass para Senha Segura

Ao invés de senha no `.env`:

```bash
# Criar ~/.pgpass
echo "localhost:5432:erp_db:postgres:senha_segura" > ~/.pgpass
chmod 600 ~/.pgpass

# Remover DB_PASSWORD do .env
# Scripts usarão .pgpass automaticamente
```

## Troubleshooting

### Backup Falha com "Permission Denied"

```bash
# Tornar scripts executáveis
chmod +x scripts/backup/*.sh

# Verificar permissões de diretório
chmod 755 backups/
```

### "pg_dump: command not found"

```bash
# Instalar PostgreSQL client
# Ubuntu/Debian
sudo apt-get install postgresql-client

# CentOS/RHEL
sudo yum install postgresql

# macOS
brew install postgresql
```

### Backup Muito Grande

```bash
# Ver tamanho do banco
psql -d erp_db -c "SELECT pg_size_pretty(pg_database_size('erp_db'));"

# Backup incremental (avançado)
# Considerar WAL archiving do PostgreSQL
```

### Cron Não Executa

```bash
# Verificar se cron está rodando
sudo systemctl status cron  # Ubuntu/Debian
sudo systemctl status crond # CentOS/RHEL

# Verificar permissões do script
chmod +x scripts/backup/backup.sh

# Usar caminho absoluto no crontab
/full/path/to/scripts/backup/backup.sh daily

# Verificar logs do cron
tail -f /var/log/syslog | grep CRON
```

### Restore Falha

```bash
# Verificar integridade do backup
gzip -t backup.sql.gz

# Verificar se banco existe
psql -l | grep erp_db

# Ver erros detalhados
gunzip -c backup.sql.gz | psql -d erp_db -v ON_ERROR_STOP=1
```

## Boas Práticas

1. **3-2-1 Rule**:
   - 3 cópias dos dados
   - 2 tipos de mídia diferentes
   - 1 cópia off-site (remota)

2. **Teste Restores Regularmente**:
   - Mensal: Restaurar backup em ambiente de teste
   - Validar integridade dos dados

3. **Monitore Espaço em Disco**:
   ```bash
   df -h backups/
   ```

4. **Verifique Logs Periodicamente**:
   - Procure por erros ou warnings
   - Valide que backups estão sendo criados

5. **Documente Procedimentos**:
   - Mantenha procedimento de restore documentado
   - Treine equipe em disaster recovery

6. **Use Backup Remoto**:
   - Sempre envie backups para local remoto
   - Protege contra falha de hardware/desastre

## Performance

### Otimizações

```bash
# Backup paralelo (mais rápido)
pg_dump -j 4 ...  # 4 jobs paralelos

# Compressão mais rápida (menos compressão)
gzip -1 ...  # Nível 1 (rápido)

# Compressão máxima (mais lento)
gzip -9 ...  # Nível 9 (máximo)
```

### Janela de Backup

- Agende backups em horários de baixa utilização
- Evite horário comercial
- Considere impacto na performance

## Próximos Passos

1. **Point-in-Time Recovery (PITR)**: WAL archiving
2. **Backup Incremental**: Apenas mudanças
3. **Snapshot de Volume**: LVM/ZFS snapshots
4. **Replicação**: Streaming replication
5. **Monitoramento Avançado**: Prometheus + Grafana
