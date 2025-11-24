# Como Executar o Backend - SISCOM

Este guia mostra as diferentes formas de executar o backend do SISCOM.

---

## 🚀 Opção 1: Execução Rápida com SQLite (Recomendado para Dev)

**Ideal para:** Desenvolvimento local rápido, testes, aprendizado

### Método A: Script Automático
```bash
./start.sh
```

### Método B: Comando Direto
```bash
# Criar .env se não existir
cp .env.example .env

# Ou criar manualmente com SQLite
cat > .env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./siscom.db
REDIS_URL=redis://localhost:6380/0
DEBUG=true
SECRET_KEY=dev-secret-key
EOF

# Executar servidor
make run
# ou
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Vantagens:**
- ✅ Não precisa de Docker
- ✅ Não precisa de PostgreSQL instalado
- ✅ Inicialização instantânea
- ✅ Arquivo de banco local (`siscom.db`)
- ✅ Perfeito para desenvolvimento

**Desvantagens:**
- ⚠️ SQLite tem limitações (sem algumas features do PostgreSQL)
- ⚠️ Não recomendado para produção

---

## 🐳 Opção 2: Docker Compose Completo (Produção-like)

**Ideal para:** Testar em ambiente próximo ao de produção

### Passo a Passo

```bash
# 1. Iniciar todos os serviços
docker-compose -f docker-compose.dev.yml up -d

# Isso inicia:
# - PostgreSQL (porta 5432)
# - Redis (porta 6380 - evita conflito)
# - Backend (porta 8000)

# 2. Ver logs
docker-compose -f docker-compose.dev.yml logs -f backend

# 3. Parar serviços
docker-compose -f docker-compose.dev.yml down
```

**Vantagens:**
- ✅ PostgreSQL completo
- ✅ Redis para cache
- ✅ Ambiente isolado
- ✅ Próximo de produção

**Desvantagens:**
- ⚠️ Requer Docker instalado
- ⚠️ Usa mais recursos (RAM/CPU)
- ⚠️ Inicialização mais lenta

---

## 🔧 Opção 3: Dev Container (VSCode)

**Ideal para:** Desenvolvimento com VSCode, ambiente completamente isolado

### Requisitos
- Docker Desktop instalado
- VSCode com extensão "Dev Containers"

### Como Usar

1. **Abrir no Dev Container**
   - Abrir VSCode no diretório raiz
   - Pressionar `F1`
   - Selecionar: `Dev Containers: Reopen in Container`
   - Escolher: `SISCOM Backend (Python)`

2. **Aguardar Setup** (primeira vez: 5-10 min)
   - Docker constrói a imagem
   - Dependências instaladas automaticamente
   - Extensões VSCode instaladas

3. **Executar Backend**
   ```bash
   # Opção A: Com PostgreSQL e Redis (via docker-compose)
   # Os serviços já estão rodando!
   make run

   # Opção B: Com SQLite (mais rápido)
   # Criar .env com SQLite
   cat > .env << 'EOF'
   DATABASE_URL=sqlite+aiosqlite:///./siscom.db
   EOF

   make run
   ```

**Vantagens:**
- ✅ Ambiente 100% isolado
- ✅ Python 3.12 garantido
- ✅ Todas extensões VSCode pré-instaladas
- ✅ PostgreSQL client, Redis tools inclusos
- ✅ Oh My Zsh configurado

**Desvantagens:**
- ⚠️ Requer Docker Desktop
- ⚠️ Primeira execução lenta (build)
- ⚠️ Pode confundir sobre qual banco usar

---

## ⚡ Opção 4: Híbrido (PostgreSQL no Docker, Backend Local)

**Ideal para:** Desenvolvedores que preferem rodar Python localmente mas querem PostgreSQL

```bash
# 1. Iniciar apenas PostgreSQL e Redis
docker-compose -f docker-compose.dev.yml up -d postgres redis

# 2. Criar .env com conexão ao PostgreSQL do Docker
cat > .env << 'EOF'
DATABASE_URL=postgresql+asyncpg://siscom:siscom123@localhost:5432/siscom_dev
REDIS_URL=redis://localhost:6380/0
DEBUG=true
SECRET_KEY=dev-secret-key
EOF

# 3. Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 4. Executar backend
make run
```

**Vantagens:**
- ✅ PostgreSQL completo
- ✅ Backend roda localmente (debug mais fácil)
- ✅ Menos overhead que Docker Compose completo

**Desvantagens:**
- ⚠️ Precisa gerenciar ambiente Python local
- ⚠️ Duas janelas de terminal (Docker + Backend)

---

## 📊 Comparação das Opções

| Opção | Database | Tempo Setup | Recursos | Melhor Para |
|-------|----------|-------------|----------|-------------|
| **SQLite Local** | SQLite | ⚡ Segundos | 🟢 Baixo | Desenvolvimento rápido |
| **Docker Compose** | PostgreSQL | 🐢 Minutos | 🔴 Alto | Testes de produção |
| **Dev Container** | Configurável | 🐌 10 min (1x) | 🟡 Médio | VSCode users |
| **Híbrido** | PostgreSQL | ⚡ 1 minuto | 🟡 Médio | Flexibilidade |

---

## 🎯 Qual Opção Escolher?

### Você quer começar AGORA?
→ **Use SQLite (`./start.sh`)**

### Você usa VSCode e quer ambiente isolado?
→ **Use Dev Container**

### Você vai testar integrações reais (pagamentos, etc)?
→ **Use Docker Compose**

### Você prefere controle total?
→ **Use Híbrido**

---

## 🔍 Troubleshooting

### Erro: "Connection refused" ao PostgreSQL

**Causa:** PostgreSQL não está rodando ou está em porta diferente

**Solução:**
```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Se não estiver, iniciar
docker-compose -f docker-compose.dev.yml up -d postgres

# Ou usar SQLite
cat > .env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./siscom.db
EOF
```

### Erro: "Redis not available"

**Isso é um WARNING, não um erro!**

O sistema automaticamente usa memória local para rate limiting quando Redis não está disponível.

**Para remover o warning:**
```bash
# Iniciar Redis na porta 6380 (evita conflito)
docker run -d -p 6380:6379 redis:7-alpine

# Ou via docker-compose (já configurado na porta 6380)
docker-compose -f docker-compose.dev.yml up -d redis
```

### Erro: "Table doesn't exist"

**Causa:** Banco de dados não foi inicializado

**Solução:**
```bash
# O servidor cria tabelas automaticamente na inicialização
# Mas se precisar forçar:

# Com Alembic (recomendado)
alembic upgrade head

# Ou deletar banco e reiniciar (perde dados!)
rm siscom.db
make run
```

### Porta 8000 já está em uso

**Solução:**
```bash
# Encontrar processo na porta 8000
lsof -i :8000

# Matar processo
kill -9 <PID>

# Ou usar porta diferente
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

---

## 📖 Após Iniciar o Servidor

### Acessar Documentação
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Health Checks
- **Health**: http://localhost:8000/health
- **Ready**: http://localhost:8000/ready

### Inicializar Autenticação
```bash
# Criar usuário admin padrão
python scripts/init_auth.py

# Login padrão criado:
# Email: admin@siscom.com
# Senha: admin123
```

### Testar API
```bash
# Via curl
curl http://localhost:8000/health

# Via httpie
http GET http://localhost:8000/health

# Ou use Thunder Client / Postman / Insomnia
```

---

## 🚀 Produção

Para produção, **NUNCA** use SQLite!

```bash
# Usar PostgreSQL real
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database

# Secret key forte
SECRET_KEY=<gerar-com-openssl-rand>

# Debug desligado
DEBUG=false
```

**Gerar secret key:**
```bash
openssl rand -hex 32
```

---

## 📚 Mais Informações

- **Guia Completo**: Ver [DEVCONTAINER_GUIDE.md](./DEVCONTAINER_GUIDE.md)
- **Documentação**: Ver [CLAUDE.md](./CLAUDE.md)
- **Estrutura**: Ver [ESTRUTURA_MONOREPO.md](./ESTRUTURA_MONOREPO.md)

---

**Última atualização:** 2025-11-24
