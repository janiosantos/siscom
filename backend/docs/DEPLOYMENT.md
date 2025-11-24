# 🚀 Guia de Deploy - SISCOM ERP

**Versão:** 1.0.0
**Última Atualização:** 2025-11-23

---

## 📋 Índice

1. [Requisitos](#requisitos)
2. [Arquitetura de Deploy](#arquitetura-de-deploy)
3. [Ambientes](#ambientes)
4. [Setup Inicial](#setup-inicial)
5. [Deploy em Homologação](#deploy-em-homologação)
6. [Deploy em Produção](#deploy-em-produção)
7. [Backup e Restore](#backup-e-restore)
8. [Monitoramento](#monitoramento)
9. [Troubleshooting](#troubleshooting)
10. [Rollback](#rollback)

---

## 🔧 Requisitos

### Hardware Mínimo (Produção)

| Componente | Especificação |
|------------|---------------|
| CPU        | 4 cores       |
| RAM        | 8 GB          |
| Disco      | 100 GB SSD    |
| Rede       | 100 Mbps      |

### Hardware Recomendado (Produção)

| Componente | Especificação |
|------------|---------------|
| CPU        | 8 cores       |
| RAM        | 16 GB         |
| Disco      | 250 GB SSD NVMe |
| Rede       | 1 Gbps        |

### Software

- **SO**: Ubuntu 22.04 LTS / Debian 11+ / CentOS 8+
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Git**: 2.30+
- **OpenSSL**: 1.1.1+
- **(Opcional) AWS CLI**: 2.0+ (para backups S3)

---

## 🏗️ Arquitetura de Deploy

```
┌─────────────────────────────────────────┐
│           Internet/Users                │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│          Nginx Reverse Proxy             │
│  - SSL/TLS Termination                   │
│  - Load Balancing                        │
│  - Rate Limiting                         │
└──────────────┬───────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌─────────────┐  ┌─────────────┐
│  Frontend   │  │   Backend   │
│  (Next.js)  │  │  (FastAPI)  │
└──────┬──────┘  └──────┬──────┘
       │                │
       └────────┬───────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌─────────────┐  ┌────────────┐
│  PostgreSQL │  │    Redis   │
│  (Database) │  │   (Cache)  │
└─────────────┘  └────────────┘
        │
        ▼
┌─────────────┐
│  Metabase   │
│    (BI)     │
└─────────────┘
```

---

## 🌍 Ambientes

### Development (Local)
- URL: `http://localhost:3000`
- Banco: SQLite/PostgreSQL local
- Debug: Habilitado
- Auto-reload: Habilitado

### Staging (Homologação)
- URL: `https://staging.seudominio.com`
- Banco: PostgreSQL dedicado
- Debug: Desabilitado
- Logs: INFO level
- Integrações: Sandbox/Test mode

### Production (Produção)
- URL: `https://seudominio.com`
- Banco: PostgreSQL cluster (replicado)
- Debug: Desabilitado
- Logs: WARNING level
- Integrações: Production mode
- Backups: Automatizados

---

## 🚀 Setup Inicial

### 1. Preparar Servidor

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    curl \
    git \
    openssl \
    ca-certificates \
    gnupg \
    lsb-release

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### 2. Clonar Repositório

```bash
# Clone repository
git clone https://github.com/sua-empresa/siscom.git
cd siscom

# Checkout appropriate branch
git checkout production  # ou staging
```

### 3. Configurar Variáveis de Ambiente

```bash
# Copy environment template
cp .env.production .env  # ou .env.staging

# Edit environment file
nano .env

# IMPORTANTE: Altere TODOS os valores sensíveis:
# - Senhas do banco de dados
# - Secret keys
# - Tokens de API
# - Certificados
```

### 4. Gerar Certificados SSL

#### Opção A: Let's Encrypt (Recomendado)

```bash
# Install certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d seudominio.com -d www.seudominio.com

# Copy certificates
sudo cp /etc/letsencrypt/live/seudominio.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/seudominio.com/privkey.pem nginx/ssl/
sudo chown $USER:$USER nginx/ssl/*.pem
```

#### Opção B: Auto-assinado (Apenas para testes)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/privkey.pem \
    -out nginx/ssl/fullchain.pem \
    -subj "/C=BR/ST=State/L=City/O=Organization/CN=seudominio.com"
```

### 5. Executar Setup

```bash
# Run setup script
sudo ./scripts/deploy/setup.sh

# Script will:
# 1. Verify Docker installation
# 2. Create necessary directories
# 3. Build Docker images
# 4. Initialize database
# 5. Run migrations
# 6. Create admin user
# 7. Start all services
```

---

## 🧪 Deploy em Homologação

```bash
# 1. Set environment
export ENVIRONMENT=staging
cp .env.staging .env

# 2. Run setup (first time only)
sudo ./scripts/deploy/setup.sh

# 3. For updates, use deploy script
./scripts/deploy/deploy.sh

# 4. Verify health
./scripts/deploy/health-check.sh

# 5. Access staging environment
# Frontend: https://staging.seudominio.com
# API Docs: https://staging.seudominio.com/docs
# Metabase: https://staging.seudominio.com/metabase
```

### Testes em Homologação

```bash
# Run integration tests
docker-compose -f docker-compose.yml exec backend pytest tests/

# Run E2E tests
cd frontend
npm run test:e2e

# Load testing (optional)
apt install apache2-utils
ab -n 1000 -c 10 https://staging.seudominio.com/api/v1/health
```

---

## 🏭 Deploy em Produção

### Pre-Deploy Checklist

- [ ] Código revisado e aprovado
- [ ] Testes passando em staging
- [ ] Backup do banco de dados criado
- [ ] Certificados SSL válidos
- [ ] Variáveis de ambiente configuradas
- [ ] Secrets rotacionados
- [ ] DNS configurado
- [ ] Firewall configurado
- [ ] Monitoramento configurado
- [ ] Equipe notificada

### Deploy Steps

```bash
# 1. Create backup
./scripts/deploy/backup.sh

# 2. Set production environment
export ENVIRONMENT=production
cp .env.production .env

# 3. Pull latest code
git fetch origin
git checkout production
git pull origin production

# 4. Run deploy script
./scripts/deploy/deploy.sh

# Deploy script will:
# - Create backup
# - Rebuild images
# - Run migrations
# - Restart services (zero-downtime)
# - Run health checks

# 5. Verify deployment
./scripts/deploy/health-check.sh

# 6. Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Post-Deploy

```bash
# 1. Smoke tests
curl https://seudominio.com/health
curl https://seudominio.com/api/v1/health

# 2. Check error logs
docker-compose -f docker-compose.prod.yml logs backend | grep ERROR

# 3. Monitor metrics
# - Response times
# - Error rates
# - CPU/Memory usage

# 4. Notify team
# Send notification to team (Slack, email, etc.)
```

---

## 💾 Backup e Restore

### Backup Automático

Configurado em `cron` para rodar diariamente às 2h:

```bash
# Edit crontab
crontab -e

# Add line:
0 2 * * * /path/to/siscom/scripts/deploy/backup.sh >> /var/log/siscom-backup.log 2>&1
```

### Backup Manual

```bash
# Create backup
./scripts/deploy/backup.sh

# Backup includes:
# - PostgreSQL database dump
# - Redis data
# - Configuration files
# - SSL certificates

# Backup location: ./backups/siscom_backup_YYYYMMDD_HHMMSS_complete.tar.gz
```

### Restore

```bash
# 1. Stop services
docker-compose -f docker-compose.prod.yml down

# 2. Extract backup
cd backups
tar -xzf siscom_backup_YYYYMMDD_HHMMSS_complete.tar.gz

# 3. Restore database
docker-compose -f docker-compose.prod.yml up -d postgres
sleep 10

docker-compose -f docker-compose.prod.yml exec -T postgres \
    psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} \
    < siscom_backup_YYYYMMDD_HHMMSS_database.sql

# 4. Restore files
tar -xzf siscom_backup_YYYYMMDD_HHMMSS_files.tar.gz -C ..

# 5. Start all services
docker-compose -f docker-compose.prod.yml up -d

# 6. Verify
./scripts/deploy/health-check.sh
```

---

## 📊 Monitoramento

### Health Checks

```bash
# Check all services
./scripts/deploy/health-check.sh

# Individual checks
curl https://seudominio.com/health        # Overall health
curl https://seudominio.com/ready         # Readiness
curl https://seudominio.com/live          # Liveness
curl https://seudominio.com/metrics       # Prometheus metrics
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# View last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 backend

# Search for errors
docker-compose -f docker-compose.prod.yml logs backend | grep ERROR

# Export logs
docker-compose -f docker-compose.prod.yml logs --no-color > logs/export.log
```

### Metrics

Acesse Prometheus metrics:
- URL: `https://seudominio.com/metrics`
- Format: Prometheus format
- Metrics: Request counts, response times, error rates, etc.

### Sentry (Error Tracking)

1. Configure `SENTRY_DSN` in `.env`
2. Errors are automatically sent to Sentry
3. Access Sentry dashboard for error analysis

---

## 🔧 Troubleshooting

### Container não inicia

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs backend

# Inspect container
docker inspect siscom-backend-prod

# Common fixes:
# 1. Check .env file
# 2. Verify ports are not in use
# 3. Check disk space: df -h
# 4. Check memory: free -h
```

### Banco de dados não conecta

```bash
# Check postgres container
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT 1"

# Common fixes:
# 1. Verify DATABASE_URL in .env
# 2. Check postgres is healthy
# 3. Check network connectivity
```

### API retorna 502 Bad Gateway

```bash
# Check backend container
docker-compose -f docker-compose.prod.yml logs backend

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Common fixes:
# 1. Backend container not running
# 2. Backend port mismatch
# 3. Nginx configuration error
```

### Frontend não carrega

```bash
# Check frontend container
docker-compose -f docker-compose.prod.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend

# Common fixes:
# 1. Environment variables missing
# 2. API URL incorrect
# 3. Build failed
```

---

## ⏪ Rollback

### Quick Rollback

```bash
# 1. Stop current deployment
docker-compose -f docker-compose.prod.yml down

# 2. Checkout previous version
git log --oneline -5  # Find previous commit
git checkout <previous-commit>

# 3. Restore database backup (if needed)
./scripts/deploy/restore.sh backups/siscom_backup_<timestamp>.tar.gz

# 4. Rebuild and start
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 5. Verify
./scripts/deploy/health-check.sh
```

### Database Rollback

```bash
# 1. Identify target migration
docker-compose -f docker-compose.prod.yml exec backend \
    alembic history

# 2. Downgrade to specific revision
docker-compose -f docker-compose.prod.yml exec backend \
    alembic downgrade <revision>

# 3. Verify database state
docker-compose -f docker-compose.prod.yml exec postgres \
    psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
```

---

## 🔒 Segurança

Ver [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) para lista completa de segurança.

### Principais Pontos

1. **SSL/TLS**: Sempre usar HTTPS em produção
2. **Secrets**: Rotacionar secrets regularmente
3. **Backups**: Manter backups criptografados
4. **Firewall**: Apenas portas 80/443 abertas
5. **Updates**: Manter sistema atualizado
6. **Monitoring**: Configurar alertas
7. **Rate Limiting**: Proteger contra abuso
8. **WAF**: Considerar Web Application Firewall

---

## 📞 Suporte

Em caso de problemas:

1. **Consultar logs**: `docker-compose logs`
2. **Health check**: `./scripts/deploy/health-check.sh`
3. **Documentação**: [docs/](../docs/)
4. **Issues**: GitHub Issues
5. **Email**: suporte@seudominio.com

---

**Última revisão**: 2025-11-23
**Versão do documento**: 1.0.0
