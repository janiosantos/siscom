# Estrutura do Monorepo - SISCOM

**Data:** 2025-11-23
**Decisão:** Manter um único repositório com backend e frontend organizados em pastas separadas

---

## 📁 Estrutura Completa

```
siscom/                                    # Repositório único (monorepo)
│
├── 🐍 BACKEND (Python/FastAPI)
│   ├── app/
│   │   ├── core/                          # Configurações centrais
│   │   │   ├── config.py                  # Settings
│   │   │   ├── database.py                # Database setup
│   │   │   ├── security.py                # JWT, bcrypt
│   │   │   ├── logging.py                 # Logging estruturado
│   │   │   ├── cache.py                   # Redis cache
│   │   │   ├── exceptions.py              # Exceções customizadas
│   │   │   └── health.py                  # Health checks
│   │   │
│   │   ├── modules/                       # Módulos de negócio (30+)
│   │   │   ├── auth/                      # Autenticação e autorização
│   │   │   │   ├── models.py              # User, Role, Permission
│   │   │   │   ├── schemas.py             # Login, Register DTOs
│   │   │   │   ├── repository.py          # User queries
│   │   │   │   ├── service.py             # Auth logic
│   │   │   │   ├── router.py              # Auth endpoints
│   │   │   │   └── dependencies.py        # Auth dependencies
│   │   │   │
│   │   │   ├── produtos/                  # Gestão de produtos
│   │   │   ├── categorias/                # Categorias
│   │   │   ├── estoque/                   # Controle de estoque
│   │   │   ├── vendas/                    # Vendas
│   │   │   ├── pdv/                       # Ponto de venda
│   │   │   ├── financeiro/                # Financeiro
│   │   │   ├── nfe/                       # NF-e/NFC-e
│   │   │   ├── clientes/                  # Clientes
│   │   │   ├── fornecedores/              # Fornecedores
│   │   │   ├── compras/                   # Compras
│   │   │   ├── orcamentos/                # Orçamentos
│   │   │   ├── os/                        # Ordens de serviço
│   │   │   ├── dashboard/                 # Dashboard e KPIs
│   │   │   ├── relatorios/                # Relatórios
│   │   │   ├── export/                    # Export Excel/CSV
│   │   │   ├── crm/                       # CRM
│   │   │   ├── fidelidade/                # Programa fidelidade
│   │   │   ├── lgpd/                      # Compliance LGPD
│   │   │   ├── multiempresa/              # Multi-tenant
│   │   │   └── ...                        # Outros módulos
│   │   │
│   │   ├── integrations/                  # Integrações externas
│   │   │   ├── mercadopago.py             # Gateway Mercado Pago
│   │   │   ├── pagseguro.py               # Gateway PagSeguro
│   │   │   ├── correios.py                # Cálculo de frete
│   │   │   ├── melhorenvio.py             # Melhor Envio
│   │   │   ├── email.py                   # SendGrid/AWS SES
│   │   │   ├── sms.py                     # Twilio SMS/WhatsApp
│   │   │   ├── mercadolivre.py            # Marketplace
│   │   │   └── ...router.py               # Routers das integrações
│   │   │
│   │   ├── middleware/                    # Middlewares
│   │   │   ├── correlation.py             # Correlation IDs
│   │   │   ├── rate_limit.py              # Rate limiting
│   │   │   ├── security_headers.py        # Security headers
│   │   │   └── tenant.py                  # Multi-tenant
│   │   │
│   │   ├── utils/                         # Utilitários
│   │   │   ├── validators.py              # CPF, CNPJ, etc
│   │   │   └── xml_reader.py              # Leitura XML NF-e
│   │   │
│   │   └── tests/                         # Testes unitários (mirror)
│   │
│   ├── alembic/                           # Migrações Alembic
│   │   ├── versions/                      # Arquivos de migração
│   │   └── env.py                         # Config Alembic
│   │
│   ├── tests/                             # Testes de integração
│   │   ├── conftest.py                    # Fixtures globais
│   │   ├── test_auth.py                   # 18 testes
│   │   ├── test_health.py
│   │   ├── test_pix.py
│   │   ├── test_boleto.py
│   │   ├── test_export.py
│   │   └── ...                            # 233 testes total
│   │
│   ├── scripts/                           # Scripts utilitários
│   │   ├── init_auth.py                   # Inicializar auth
│   │   ├── backup/                        # Scripts backup
│   │   └── validate_ci_local.sh           # Validação local
│   │
│   ├── main.py                            # Entry point FastAPI
│   ├── requirements.txt                   # Dependências Python
│   ├── pytest.ini                         # Config pytest
│   ├── alembic.ini                        # Config Alembic
│   └── Makefile                           # Comandos úteis
│
├── ⚛️ FRONTEND (Next.js/React)
│   └── frontend/
│       ├── src/
│       │   ├── app/                       # App Router (Next.js 14)
│       │   │   ├── (auth)/               # Rotas autenticadas
│       │   │   │   ├── dashboard/
│       │   │   │   ├── produtos/
│       │   │   │   ├── vendas/
│       │   │   │   ├── estoque/
│       │   │   │   └── ...
│       │   │   │
│       │   │   ├── (public)/             # Rotas públicas
│       │   │   │   ├── login/
│       │   │   │   └── register/
│       │   │   │
│       │   │   ├── layout.tsx            # Layout raiz
│       │   │   └── page.tsx              # Home page
│       │   │
│       │   ├── components/               # Componentes React
│       │   │   ├── ui/                   # shadcn/ui base
│       │   │   │   ├── button.tsx
│       │   │   │   ├── input.tsx
│       │   │   │   ├── table.tsx
│       │   │   │   ├── dialog.tsx
│       │   │   │   └── ...               # 20+ componentes
│       │   │   │
│       │   │   ├── forms/                # Formulários
│       │   │   │   ├── produto-form.tsx
│       │   │   │   ├── venda-form.tsx
│       │   │   │   └── ...
│       │   │   │
│       │   │   ├── charts/               # Gráficos (Recharts)
│       │   │   │   ├── bar-chart.tsx
│       │   │   │   ├── line-chart.tsx
│       │   │   │   └── pie-chart.tsx
│       │   │   │
│       │   │   └── layout/               # Layout components
│       │   │       ├── header.tsx
│       │   │       ├── sidebar.tsx
│       │   │       └── footer.tsx
│       │   │
│       │   └── lib/                      # Bibliotecas
│       │       ├── api/                  # Cliente API
│       │       │   ├── client.ts         # Axios config
│       │       │   ├── produtos.ts       # Produtos API
│       │       │   ├── vendas.ts         # Vendas API
│       │       │   └── ...
│       │       │
│       │       ├── hooks/                # Custom hooks
│       │       │   ├── use-auth.ts       # Hook de auth
│       │       │   ├── use-produtos.ts   # Hook produtos
│       │       │   └── ...
│       │       │
│       │       ├── contexts/             # Context providers
│       │       │   ├── auth-context.tsx
│       │       │   └── theme-context.tsx
│       │       │
│       │       └── utils/                # Utilitários
│       │           ├── cn.ts             # Class names
│       │           ├── format.ts         # Formatação
│       │           └── validators.ts     # Validações
│       │
│       ├── public/                       # Assets estáticos
│       │   ├── images/
│       │   ├── icons/
│       │   └── mockServiceWorker.js      # MSW
│       │
│       ├── __tests__/                    # Testes
│       │   ├── mocks/                    # MSW mocks
│       │   ├── components/               # Testes componentes
│       │   └── integration/              # Testes integração
│       │
│       ├── package.json                  # Deps Node.js
│       ├── tsconfig.json                 # Config TypeScript
│       ├── next.config.js                # Config Next.js
│       ├── tailwind.config.ts            # Config Tailwind
│       ├── jest.config.js                # Config Jest
│       ├── playwright.config.ts          # Config Playwright
│       └── .env.local.example            # Env vars exemplo
│
├── 📚 DOCUMENTAÇÃO
│   ├── docs/                             # Docs técnicas
│   │   ├── AUTHENTICATION.md
│   │   ├── LOGGING.md
│   │   ├── RATE_LIMITING.md
│   │   ├── BACKUP.md
│   │   ├── TESTING.md
│   │   ├── PAGAMENTOS.md
│   │   └── INTEGRACAO_MERCADOPAGO.md
│   │
│   ├── CLAUDE.md                         # ⭐ Guia principal devs
│   ├── README.md                         # ⭐ README principal
│   ├── DEVCONTAINER_GUIDE.md             # Guia Dev Containers
│   ├── ESTRUTURA_MONOREPO.md             # Este arquivo
│   ├── SEPARACAO_REPOSITORIOS.md         # Ref. futura
│   ├── PROGRESSO_IMPLEMENTACAO.md        # Status projeto
│   ├── PROMPT_MASTER_ERP.md              # Especificação
│   └── NOVOS_RECURSOS.md                 # Roadmap
│
├── 🐳 DEV CONTAINERS
│   ├── .devcontainer-backend/            # Dev Container Python
│   │   ├── devcontainer.json             # Config VSCode
│   │   └── Dockerfile                    # Python 3.12
│   │
│   ├── .devcontainer-frontend/           # Dev Container Node.js
│   │   ├── devcontainer.json             # Config VSCode
│   │   └── Dockerfile                    # Node.js 18
│   │
│   └── docker-compose.dev.yml            # Orquestração dev
│
├── ⚙️ CONFIGURAÇÕES RAIZ
│   ├── .env.example                      # Template env vars
│   ├── .gitignore                        # Git ignore
│   ├── .pre-commit-config.yaml           # Pre-commit hooks
│   └── .github/
│       └── workflows/
│           └── ci.yml                    # GitHub Actions
│
└── 📄 OUTROS
    ├── LICENSE                           # Licença
    └── .editorconfig                     # Editor config
```

---

## 🎯 Vantagens do Monorepo

### ✅ Vantagens Mantidas

1. **Código Compartilhado Fácil**
   - Backend e frontend no mesmo repo
   - Commit único afeta ambos
   - Sincronização automática

2. **Deploys Simplificados**
   - Um único repositório para clonar
   - CI/CD unificado
   - Versionamento conjunto

3. **Desenvolvimento Integrado**
   - Mudanças de API + UI no mesmo PR
   - Histórico Git completo
   - Menos overhead de gestão

4. **Dev Containers Isolados**
   - Backend em container Python separado
   - Frontend em container Node.js separado
   - Database e cache compartilhados
   - Melhor dos dois mundos!

5. **Documentação Centralizada**
   - Todas as docs em um lugar
   - README principal unificado
   - Guias compartilhados

### ⚖️ Comparação

| Aspecto | Monorepo (Atual) | Dois Repos |
|---------|------------------|------------|
| Sincronização | ✅ Automática | ⚠️ Manual |
| Setup Dev | ✅ Um clone | ⚠️ Dois clones |
| CI/CD | ✅ Pipeline único | ⚠️ Dois pipelines |
| Versionamento | ✅ Unified | ⚠️ Separado |
| Independência | ⚠️ Acoplado | ✅ Total |
| Deploy | ⚠️ Tudo junto | ✅ Separado |
| Isolamento | ✅ Via Dev Containers | ✅ Repos separados |

---

## 🚀 Como Trabalhar com o Monorepo

### Setup Inicial

```bash
# 1. Clonar repositório único
git clone https://github.com/janiosantos/siscom.git
cd siscom

# 2. Escolher o que desenvolver
```

### Opção A: Trabalhar no Backend

```bash
# Abrir VSCode no diretório raiz
code .

# F1 → "Dev Containers: Reopen in Container" → Backend
# Container Python isola o ambiente

# Trabalhar normalmente
alembic upgrade head
python scripts/init_auth.py
uvicorn main:app --reload
```

### Opção B: Trabalhar no Frontend

```bash
# Abrir VSCode no diretório frontend
cd frontend
code .

# F1 → "Dev Containers: Reopen in Container" → Frontend
# Container Node.js isola o ambiente

# Trabalhar normalmente
npm install
npm run dev
```

### Opção C: Full Stack (Dois VSCode)

```bash
# Terminal 1: Backend
code .
# F1 → Backend Container
# uvicorn main:app --reload

# Terminal 2: Frontend
cd frontend && code .
# F1 → Frontend Container
# npm run dev
```

---

## 📦 Estrutura de Pastas por Tipo

### Backend (/app)

```
app/
├── core/          # Código central compartilhado
├── modules/       # Módulos de negócio (domínio)
├── integrations/  # Integrações externas (anti-corruption layer)
├── middleware/    # Middlewares HTTP
├── utils/         # Utilitários gerais
└── tests/         # Testes unitários
```

**Padrão de Módulo (exemplo: produtos)**
```
app/modules/produtos/
├── models.py        # SQLAlchemy models (tabelas)
├── schemas.py       # Pydantic schemas (DTOs)
├── repository.py    # Data Access Layer
├── service.py       # Business Logic Layer
└── router.py        # API endpoints (presentation)
```

### Frontend (/frontend)

```
frontend/src/
├── app/           # Next.js App Router (rotas)
├── components/    # Componentes React reutilizáveis
├── lib/           # Bibliotecas e utilitários
└── __tests__/     # Testes Jest
```

---

## 🔧 Scripts e Comandos

### Backend (raiz do projeto)

```bash
# Desenvolvimento
make run              # Executar backend
make test             # Executar testes
make migration        # Criar migração
make migrate          # Aplicar migrações

# Direto com Python
python main.py
pytest
alembic upgrade head
```

### Frontend (dentro de /frontend)

```bash
# Desenvolvimento
npm run dev           # Dev server
npm test              # Jest tests
npm run build         # Build produção
npm run lint          # ESLint

# Ou com yarn
yarn dev
yarn test
yarn build
```

---

## 🐳 Docker Compose

O arquivo `docker-compose.dev.yml` orquestra 4 serviços:

```yaml
services:
  backend:      # Python/FastAPI (porta 8000)
  frontend:     # Node.js/Next.js (porta 3000)
  postgres:     # PostgreSQL 15 (porta 5432)
  redis:        # Redis 7 (porta 6379)
```

**Vantagens:**
- ✅ Backend e frontend isolados
- ✅ Database compartilhado
- ✅ Cache compartilhado
- ✅ Network dedicada
- ✅ Volumes persistentes

---

## 📝 Git Workflow

### Commits

```bash
# Mudanças apenas no backend
git commit -m "feat(backend): adicionar endpoint de produtos"

# Mudanças apenas no frontend
git commit -m "feat(frontend): adicionar página de produtos"

# Mudanças em ambos
git commit -m "feat: implementar CRUD completo de produtos

- Backend: endpoint de produtos
- Frontend: página de listagem
- Docs: atualizar API docs"
```

### Branches

```
main                              # Produção
├── develop                       # Desenvolvimento
│   ├── feature/produtos-crud     # Feature completa (backend + frontend)
│   ├── feature/backend-auth      # Feature só backend
│   └── feature/frontend-ui       # Feature só frontend
```

---

## 🎓 Para Novos Desenvolvedores

### Backend Developer

1. ✅ Ler [README.md](./README.md)
2. ✅ Ler [CLAUDE.md](./CLAUDE.md) (guia completo)
3. ✅ Setup: Dev Container Backend
4. ✅ Executar testes: `make test`
5. ✅ Explorar: `/app/modules/produtos/` (exemplo completo)
6. ✅ Estudar: [docs/AUTHENTICATION.md](./docs/AUTHENTICATION.md)

### Frontend Developer

1. ✅ Ler [README.md](./README.md)
2. ✅ Ler seção Frontend do README
3. ✅ Setup: Dev Container Frontend
4. ✅ Executar testes: `npm test`
5. ✅ Explorar: `/frontend/src/components/ui/` (shadcn/ui)
6. ✅ Estudar: API client em `/frontend/src/lib/api/`

### Full Stack Developer

1. ✅ Fazer ambos os setups acima
2. ✅ Entender fluxo: Frontend → API → Backend → Database
3. ✅ Ver [DEVCONTAINER_GUIDE.md](./DEVCONTAINER_GUIDE.md)
4. ✅ Praticar: Criar feature completa (backend + frontend)

---

## 🔮 Futuro

Se algum dia for necessário separar em dois repositórios:
- Consultar [SEPARACAO_REPOSITORIOS.md](./SEPARACAO_REPOSITORIOS.md)
- Usar script automatizado: `scripts/split_repos.sh`
- Manter READMEs separados já criados

Por enquanto, **monorepo é a melhor escolha** para este projeto! 🎉

---

## 📞 Dúvidas?

- **Setup**: Ver [DEVCONTAINER_GUIDE.md](./DEVCONTAINER_GUIDE.md)
- **Desenvolvimento**: Ver [CLAUDE.md](./CLAUDE.md)
- **API**: Ver [docs/](./docs/)
- **Status**: Ver [PROGRESSO_IMPLEMENTACAO.md](./PROGRESSO_IMPLEMENTACAO.md)

**Última atualização:** 2025-11-23
