# Guia de Separação em Dois Repositórios

> **⚠️ NOTA IMPORTANTE (2025-11-23):**
> Este guia foi criado para documentar o processo de separação em dois repositórios independentes, mas **a decisão final foi MANTER UM ÚNICO REPOSITÓRIO (MONOREPO)** com backend e frontend bem organizados em pastas separadas.
>
> **Estrutura adotada:**
> - `/app/` - Backend (Python/FastAPI)
> - `/frontend/` - Frontend (Next.js/React)
> - Dev Containers configurados para ambos
>
> Este documento é mantido apenas como **referência futura** caso seja necessário fazer a separação.

---

**Data de criação:** 23/11/2025
**Objetivo original:** Separar o monorepo atual em dois repositórios independentes

---

## 📋 Estrutura Atual vs Nova

### Atual (Monorepo):
```
siscom/
├── app/                    # Backend
├── frontend/               # Frontend
├── alembic/               # Migrations
├── tests/                 # Backend tests
├── docs/                  # Documentação
├── main.py                # Backend entry point
└── requirements.txt       # Backend deps
```

### Nova (Dois Repositórios):

**Repositório 1: siscom-backend**
```
siscom-backend/
├── app/
├── alembic/
├── tests/
├── docs/
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

**Repositório 2: siscom-frontend**
```
siscom-frontend/
├── app/
├── components/
├── lib/
├── public/
├── __tests__/
├── package.json
├── Dockerfile
└── README.md
```

---

## 🚀 Plano de Separação

### Opção 1: Preservar Histórico Git (Recomendado)

Usa `git subtree` para manter todo o histórico de commits.

### Opção 2: Repos Novos (Mais Simples)

Cria repos novos sem histórico anterior.

---

## 📝 Passo a Passo - Opção 2 (Recomendada)

### 1. Criar Repositórios no GitHub

No GitHub, criar dois repositórios vazios:
- `siscom-backend`
- `siscom-frontend`

### 2. Preparar Backend

```bash
# Criar diretório temporário para backend
cd /tmp
mkdir siscom-backend
cd siscom-backend

# Copiar arquivos do backend
cp -r /home/user/siscom/app .
cp -r /home/user/siscom/alembic .
cp -r /home/user/siscom/tests .
cp -r /home/user/siscom/docs .
cp -r /home/user/siscom/scripts .
cp -r /home/user/siscom/nginx .
cp /home/user/siscom/main.py .
cp /home/user/siscom/requirements.txt .
cp /home/user/siscom/pytest.ini .
cp /home/user/siscom/alembic.ini .
cp /home/user/siscom/Makefile .
cp /home/user/siscom/Dockerfile .
cp /home/user/siscom/docker-compose.yml .
cp /home/user/siscom/docker-compose.prod.yml .
cp /home/user/siscom/.env.example .
cp /home/user/siscom/.gitignore .
cp /home/user/siscom/.pre-commit-config.yaml .

# Copiar documentação importante
cp /home/user/siscom/CLAUDE.md .
cp /home/user/siscom/README.md README_OLD.md

# Inicializar git
git init
git add .
git commit -m "Initial commit: Backend ERP Sistema"

# Conectar ao GitHub
git remote add origin https://github.com/janiosantos/siscom-backend.git
git branch -M main
git push -u origin main
```

### 3. Preparar Frontend

```bash
# Criar diretório temporário para frontend
cd /tmp
mkdir siscom-frontend
cd siscom-frontend

# Copiar todo o conteúdo do frontend
cp -r /home/user/siscom/frontend/* .
cp -r /home/user/siscom/frontend/.* . 2>/dev/null || true

# Inicializar git
git init
git add .
git commit -m "Initial commit: Frontend ERP Sistema"

# Conectar ao GitHub
git remote add origin https://github.com/janiosantos/siscom-frontend.git
git branch -M main
git push -u origin main
```

---

## 📝 Passo a Passo - Opção 1 (Com Histórico)

### Para Backend:

```bash
# Criar novo repo apenas com histórico do backend
cd /home/user
git clone siscom siscom-backend
cd siscom-backend

# Remover pasta frontend do histórico
git filter-repo --path frontend --invert-paths --force

# OU usar git subtree (mais simples)
git subtree split --prefix=. -b backend-only

# Conectar ao novo repo
git remote add origin https://github.com/janiosantos/siscom-backend.git
git push -u origin main
```

### Para Frontend:

```bash
# Criar novo repo apenas com histórico do frontend
cd /home/user
git clone siscom siscom-frontend
cd siscom-frontend

# Manter apenas pasta frontend
git filter-repo --path frontend --force

# Mover conteúdo de frontend/ para raiz
git mv frontend/* .
git mv frontend/.* . 2>/dev/null || true
git commit -m "Reorganizar: Mover frontend para raiz"

# Conectar ao novo repo
git remote add origin https://github.com/janiosantos/siscom-frontend.git
git push -u origin main
```

---

## 📄 Arquivos Adicionais Necessários

Vou criar os arquivos específicos para cada repositório nos próximos passos.

---

## 🔗 Comunicação Entre Repositórios

### Backend .env
```bash
# Frontend URL para CORS
FRONTEND_URL=http://localhost:3000
ALLOWED_ORIGINS=["http://localhost:3000","https://app.seudominio.com"]
```

### Frontend .env.local
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## ⚙️ CI/CD Separado

### Backend (.github/workflows/backend-ci.yml)
- Testes Python
- Lint (flake8, black)
- Build Docker
- Deploy backend

### Frontend (.github/workflows/frontend-ci.yml)
- Testes Jest
- Build Next.js
- Deploy Vercel/Netlify

---

## 📦 Dependências

### Backend Independente:
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis (opcional)

### Frontend Independente:
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

---

## 🎯 Vantagens da Separação

1. ✅ **Deploy Independente:** Backend e frontend podem ser deployados separadamente
2. ✅ **CI/CD Mais Rápido:** Pipelines menores e mais rápidos
3. ✅ **Equipes Separadas:** Backend e frontend teams podem trabalhar independentemente
4. ✅ **Versionamento:** Versões independentes (backend v1.0, frontend v2.0)
5. ✅ **Segurança:** Repositório backend pode ser privado, frontend público
6. ✅ **Escalabilidade:** Mais fácil escalar cada parte separadamente

---

## ⚠️ Desvantagens

1. ❌ **Sincronização:** Precisa manter schemas/types sincronizados
2. ❌ **Dois PRs:** Mudanças que afetam ambos requerem 2 pull requests
3. ❌ **Complexidade:** Mais repos para gerenciar

---

## 🛠️ Próximos Passos

1. Criar repositórios no GitHub
2. Executar scripts de preparação
3. Criar README.md específicos (próximo arquivo)
4. Atualizar documentação
5. Configurar CI/CD para cada repo
6. Testar deploy separado

---

**Pronto para executar?** Vou criar os arquivos específicos nos próximos passos.
