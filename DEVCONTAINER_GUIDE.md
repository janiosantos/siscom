# Guia de Dev Containers - SISCOM

## 📋 Visão Geral

Este projeto está configurado com **VSCode Dev Containers** para fornecer ambientes de desenvolvimento isolados, consistentes e totalmente configurados para backend e frontend.

### Vantagens

✅ **Isolamento completo** - Não polui seu sistema operacional
✅ **Ambiente consistente** - Todos os desenvolvedores usam as mesmas versões
✅ **Setup automático** - Dependências instaladas automaticamente
✅ **Extensões incluídas** - VSCode já vem com todas as extensões necessárias
✅ **Database incluído** - PostgreSQL e Redis prontos para uso
✅ **Sem conflitos** - Python, Node.js isolados em containers

---

## 🛠️ Pré-requisitos

### Ferramentas Necessárias

1. **Visual Studio Code** (versão mais recente)
   - Download: https://code.visualstudio.com/

2. **Docker Desktop** (ou Docker Engine + Docker Compose)
   - **Windows/Mac**: Docker Desktop - https://www.docker.com/products/docker-desktop
   - **Linux**: Docker Engine + Docker Compose
     ```bash
     # Ubuntu/Debian
     sudo apt-get update
     sudo apt-get install docker.io docker-compose
     sudo usermod -aG docker $USER
     # Fazer logout e login novamente
     ```

3. **Extensão Dev Containers no VSCode**
   - Abra VSCode
   - Vá em Extensions (Ctrl+Shift+X)
   - Procure por "Dev Containers"
   - Instale a extensão oficial da Microsoft

### Verificar Instalação

```bash
# Verificar Docker
docker --version
docker-compose --version

# Testar Docker
docker run hello-world
```

---

## 🚀 Como Usar

### Opção 1: Abrir Backend em Dev Container

1. **Abrir VSCode no diretório raiz do projeto**
   ```bash
   cd /home/user/siscom
   code .
   ```

2. **Abrir Command Palette**
   - Pressione `F1` ou `Ctrl+Shift+P`

3. **Selecionar Dev Container**
   - Digite: `Dev Containers: Reopen in Container`
   - Selecione: **SISCOM Backend (Python)**

4. **Aguardar Setup**
   - Docker irá construir a imagem (primeira vez pode demorar 5-10 min)
   - Dependências serão instaladas automaticamente
   - Extensões do VSCode serão instaladas

5. **Pronto!**
   - Terminal já está dentro do container
   - Python 3.12 disponível
   - PostgreSQL rodando em `postgres:5432`
   - Redis rodando em `redis:6379`

### Opção 2: Abrir Frontend em Dev Container

1. **Abrir VSCode no diretório do frontend**
   ```bash
   cd /home/user/siscom/frontend
   code .
   ```

2. **Abrir Command Palette**
   - Pressione `F1` ou `Ctrl+Shift+P`

3. **Selecionar Dev Container**
   - Digite: `Dev Containers: Reopen in Container`
   - Selecione: **SISCOM Frontend (Next.js)**

4. **Aguardar Setup**
   - Docker irá construir a imagem
   - `npm install` executado automaticamente
   - Extensões do VSCode instaladas

5. **Pronto!**
   - Node.js 18 disponível
   - API acessível em `http://localhost:8000`

---

## 🔧 Estrutura dos Dev Containers

### Backend (.devcontainer-backend/)

**Tecnologias incluídas:**
- Python 3.12
- PostgreSQL Client
- Redis Tools
- Git, GitHub CLI
- Oh My Zsh

**Ferramentas Python instaladas:**
- black (formatação)
- flake8 (linting)
- isort (organização de imports)
- mypy (type checking)
- pytest, pytest-cov (testes)
- ipython, ipdb (debugging)
- pre-commit (hooks)

**Extensões VSCode (25+):**
- Python, Pylance, Black, Flake8
- SQLTools + PostgreSQL Driver
- GitLens, Git Graph
- Docker
- Thunder Client (REST)
- GitHub Copilot

**Portas expostas:**
- 8000 - FastAPI Backend
- 5432 - PostgreSQL
- 6379 - Redis

### Frontend (.devcontainer-frontend/)

**Tecnologias incluídas:**
- Node.js 18
- npm, yarn, pnpm
- Git, GitHub CLI
- Oh My Zsh

**Ferramentas Node.js instaladas:**
- next (framework)
- eslint (linting)
- prettier (formatação)
- typescript (type checking)
- vercel (deploy)

**Extensões VSCode (30+):**
- ESLint, Prettier
- Tailwind CSS IntelliSense
- React snippets, Next.js snippets
- TypeScript
- Jest, Playwright
- GitLens
- GitHub Copilot
- Import Cost
- Console Ninja

**Portas expostas:**
- 3000 - Next.js Frontend

---

## 📦 Serviços Disponíveis (docker-compose.dev.yml)

### Backend Service
```yaml
Container: siscom-backend-dev
Port: 8000
Comando inicial: sleep infinity (permite comandos manuais)
Volumes: Código mapeado em /workspace
```

### Frontend Service
```yaml
Container: siscom-frontend-dev
Port: 3000
Comando inicial: sleep infinity
Volumes: Código frontend mapeado em /workspace
```

### PostgreSQL Database
```yaml
Container: siscom-postgres-dev
Port: 5432
Database: siscom_dev
User: siscom
Password: siscom123
Healthcheck: Automático
```

### Redis Cache
```yaml
Container: siscom-redis-dev
Port: 6379
Healthcheck: Automático
```

---

## 🎯 Workflows Comuns

### Iniciar Backend

Dentro do Dev Container do backend:

```bash
# Aplicar migrações
alembic upgrade head

# Inicializar autenticação
python scripts/init_auth.py

# Executar servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Ou com Makefile
make run
```

Acessar API: http://localhost:8000/docs

### Iniciar Frontend

Dentro do Dev Container do frontend:

```bash
# Instalar dependências (se ainda não instalado)
npm install

# Executar em desenvolvimento
npm run dev

# Ou
yarn dev
```

Acessar app: http://localhost:3000

### Executar Testes Backend

```bash
# Testes unitários
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/test_auth.py -v

# Via Makefile
make test
```

### Executar Testes Frontend

```bash
# Testes unitários
npm test

# Testes em watch mode
npm test -- --watch

# Testes E2E
npm run test:e2e

# Com interface gráfica
npm run test:e2e:ui
```

### Acessar Database

**Via VSCode SQLTools:**
1. Clique no ícone "Database" na barra lateral
2. Conexão "PostgreSQL SISCOM Dev" já está configurada
3. Clique para conectar

**Via Terminal:**
```bash
# Dentro do dev container backend
psql postgresql://siscom:siscom123@postgres:5432/siscom_dev

# Ou usando cliente externo
psql -h localhost -U siscom -d siscom_dev
```

### Acessar Redis

```bash
# Dentro do dev container backend
redis-cli -h redis

# Comandos úteis
PING
KEYS *
GET chave
SET chave valor
```

---

## 🔄 Comandos Úteis

### Reconstruir Container

Quando você atualiza o Dockerfile ou devcontainer.json:

1. Pressione `F1`
2. Digite: `Dev Containers: Rebuild Container`
3. Selecione "Rebuild" (ou "Rebuild Without Cache" se necessário)

### Reabrir no Host

Para sair do Dev Container:

1. Pressione `F1`
2. Digite: `Dev Containers: Reopen Folder Locally`

### Ver Logs do Container

```bash
# No host (fora do container)
docker logs siscom-backend-dev
docker logs siscom-frontend-dev
docker logs siscom-postgres-dev
docker logs siscom-redis-dev
```

### Parar Todos os Containers

```bash
# No host
cd /home/user/siscom
docker-compose -f docker-compose.dev.yml down

# Parar e remover volumes (CUIDADO: apaga dados do banco)
docker-compose -f docker-compose.dev.yml down -v
```

### Iniciar Containers Manualmente

```bash
# No host
cd /home/user/siscom
docker-compose -f docker-compose.dev.yml up -d
```

### Executar Comando em Container Específico

```bash
# No host
docker exec -it siscom-backend-dev bash
docker exec -it siscom-frontend-dev sh
docker exec -it siscom-postgres-dev psql -U siscom -d siscom_dev
```

---

## 🐛 Troubleshooting

### Problema: "Docker daemon not running"

**Solução:**
- Inicie o Docker Desktop (Windows/Mac)
- Ou inicie o serviço Docker (Linux):
  ```bash
  sudo systemctl start docker
  ```

### Problema: "Port already in use"

**Causa:** Outra aplicação usando a porta 8000, 3000, 5432 ou 6379

**Solução 1:** Parar a aplicação conflitante

**Solução 2:** Mudar a porta no docker-compose.dev.yml:
```yaml
ports:
  - "8001:8000"  # Muda porta host de 8000 para 8001
```

### Problema: Container muito lento (Windows/Mac)

**Causa:** Volumes Docker no Windows/Mac podem ser lentos

**Solução:** Usar named volumes para node_modules e venv (já configurado!)
```yaml
volumes:
  - backend-venv:/workspace/venv
  - frontend-node-modules:/workspace/node_modules
```

### Problema: Mudanças no código não refletem

**Solução 1:** Verificar se o volume está mapeado corretamente
```bash
docker inspect siscom-backend-dev | grep Mounts -A 20
```

**Solução 2:** Rebuild do container
- F1 → "Dev Containers: Rebuild Container"

### Problema: Extensões não instaladas

**Solução:**
- F1 → "Dev Containers: Rebuild Container Without Cache"
- Aguardar instalação completa

### Problema: Database connection failed

**Verificar se PostgreSQL está rodando:**
```bash
docker ps | grep postgres
docker logs siscom-postgres-dev
```

**Testar conexão:**
```bash
# Dentro do backend container
psql postgresql://siscom:siscom123@postgres:5432/siscom_dev -c "SELECT 1"
```

### Problema: Permissões de arquivo (Linux)

**Causa:** Arquivos criados no container têm owner diferente

**Solução:** Ajustar USER_UID no devcontainer:
```json
"build": {
  "args": {
    "USER_UID": "1000"  // Seu UID no host
  }
}
```

Ver seu UID:
```bash
id -u
```

---

## 📚 Recursos Adicionais

### Documentação Oficial

- **Dev Containers**: https://code.visualstudio.com/docs/devcontainers/containers
- **Docker Compose**: https://docs.docker.com/compose/
- **VSCode Remote**: https://code.visualstudio.com/docs/remote/remote-overview

### Dicas de Produtividade

**Usar terminal integrado:**
- O terminal do VSCode já está dentro do container
- Não precisa fazer `docker exec`

**Múltiplos terminais:**
- Ctrl+Shift+` para abrir novo terminal
- Cada terminal é uma sessão no container

**Debugging:**
- Backend: Use debugger do VSCode (F5) - já configurado
- Frontend: Use Console Ninja extension para ver logs em tempo real

**Git:**
- Suas credenciais Git do host são compartilhadas automaticamente
- SSH keys também funcionam

**Extensões:**
- Extensões instaladas no container não afetam o VSCode do host
- Cada devcontainer tem suas próprias extensões

---

## 🎓 Fluxo de Trabalho Recomendado

### Desenvolvedor Backend

1. Abrir VSCode no diretório raiz
2. F1 → "Dev Containers: Reopen in Container" → Backend
3. Aguardar setup
4. Terminal: `alembic upgrade head`
5. Terminal: `python scripts/init_auth.py`
6. Terminal: `make run` (ou `uvicorn main:app --reload`)
7. Desenvolver normalmente
8. Testes: `make test`
9. Commit: Git funciona normalmente

### Desenvolvedor Frontend

1. Abrir VSCode em `/frontend`
2. F1 → "Dev Containers: Reopen in Container" → Frontend
3. Aguardar setup
4. Terminal: `npm run dev`
5. Desenvolver normalmente
6. Testes: `npm test`
7. Commit: Git funciona normalmente

### Desenvolvedor Full Stack

**Opção 1: Dois VSCode Windows**
- VSCode 1: Backend no dev container
- VSCode 2: Frontend no dev container
- Ambos rodando simultaneamente

**Opção 2: Terminal Split**
- Abrir backend no dev container
- Terminal 1: `uvicorn main:app --reload`
- Terminal 2: `cd frontend && npm run dev`
- (Frontend não estará no dev container nesse caso)

---

## ✅ Checklist de Primeiro Uso

- [ ] Docker instalado e rodando
- [ ] VSCode instalado
- [ ] Extensão "Dev Containers" instalada no VSCode
- [ ] Repositório clonado
- [ ] Abrir backend em dev container
- [ ] Aguardar build (primeira vez: 5-10 min)
- [ ] Verificar PostgreSQL: `psql postgresql://siscom:siscom123@postgres:5432/siscom_dev -c "SELECT 1"`
- [ ] Aplicar migrações: `alembic upgrade head`
- [ ] Inicializar auth: `python scripts/init_auth.py`
- [ ] Testar backend: `make test`
- [ ] Executar backend: `make run`
- [ ] Acessar docs: http://localhost:8000/docs
- [ ] Abrir frontend em dev container (nova janela VSCode)
- [ ] Aguardar build
- [ ] Testar frontend: `npm test`
- [ ] Executar frontend: `npm run dev`
- [ ] Acessar app: http://localhost:3000

---

## 🔐 Segurança

### Credenciais de Desenvolvimento

**⚠️ IMPORTANTE:** As credenciais no docker-compose.dev.yml são APENAS para desenvolvimento local.

**NUNCA** use em produção:
- Database password: `siscom123`
- Secret key: `dev-secret-key-change-in-production`

### Produção

Para produção, use:
- Variáveis de ambiente seguras
- Docker secrets
- Vault ou AWS Secrets Manager
- Nunca commitar credenciais reais

---

## 📞 Suporte

### Problemas Comuns

Consulte a seção **Troubleshooting** acima.

### Issues

Se encontrar problemas:
1. Verificar logs: `docker logs siscom-backend-dev`
2. Rebuild container: F1 → "Rebuild Container"
3. Verificar Docker: `docker ps`
4. Abrir issue no GitHub com logs

---

## 🎉 Pronto!

Agora você tem um ambiente de desenvolvimento completo, isolado e consistente para trabalhar no SISCOM!

**Happy Coding! 🚀**
