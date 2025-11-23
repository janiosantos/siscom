# SISCOM Backend - API ERP

<div align="center">

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Sistema ERP completo para Materiais de Construção - Backend API**

[Documentação](#-documentação) •
[Instalação](#-instalação) •
[Deploy](#-deploy) •
[API Docs](#-api-docs)

</div>

---

## 📋 Sobre

Backend do sistema ERP SISCOM desenvolvido com FastAPI, fornecendo API REST completa para gerenciamento de:

- 🔐 Autenticação e Autorização (JWT + RBAC)
- 📦 Produtos e Categorias
- 📊 Estoque e Movimentações
- 💰 Vendas e Orçamentos
- 💳 Pagamentos (PIX, Boleto, Cartão)
- 📄 NF-e e Documentos Fiscais
- 👥 Clientes e Fornecedores
- 📈 Relatórios e Dashboard
- 🔌 Integrações (Mercado Pago, PagSeguro, Correios)

---

## 🚀 Stack Tecnológica

- **Framework:** FastAPI 0.109
- **Python:** 3.12+
- **Database:** PostgreSQL 15 + asyncpg
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Validation:** Pydantic v2
- **Auth:** JWT (access + refresh tokens)
- **Cache:** Redis (opcional)
- **Tests:** pytest + pytest-asyncio
- **Docs:** Swagger UI (auto-gerado)

---

## 📁 Estrutura do Projeto

```
siscom-backend/
├── app/
│   ├── core/              # Configurações centrais
│   ├── middleware/        # Middlewares
│   ├── modules/           # Módulos de negócio
│   │   ├── auth/
│   │   ├── produtos/
│   │   ├── vendas/
│   │   └── ...
│   ├── integrations/      # Integrações externas
│   └── utils/             # Utilitários
├── alembic/               # Migrations
├── tests/                 # Testes
├── docs/                  # Documentação
├── scripts/               # Scripts utilitários
├── main.py                # Entry point
└── requirements.txt       # Dependências
```

---

## 🛠️ Instalação

### Pré-requisitos

- Python 3.12+
- PostgreSQL 15+
- Redis (opcional)

### 1. Clonar Repositório

```bash
git clone https://github.com/janiosantos/siscom-backend.git
cd siscom-backend
```

### 2. Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
# Editar .env com suas configurações
```

**Principais variáveis:**
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/siscom
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=true
```

### 5. Executar Migrations

```bash
alembic upgrade head
```

### 6. Inicializar Dados

```bash
python scripts/init_auth.py
```

### 7. Executar Servidor

```bash
# Desenvolvimento
uvicorn main:app --reload --port 8000

# Ou com Makefile
make run
```

---

## 🧪 Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/test_auth.py -v

# Via Makefile
make test
```

---

## 📚 API Docs

Após iniciar o servidor, acesse:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## 🐳 Docker

### Desenvolvimento

```bash
docker-compose up -d
```

### Produção

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🚀 Deploy

### Opção 1: Docker (Recomendado)

```bash
# Build
docker build -t siscom-backend:latest .

# Run
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=... \
  -e SECRET_KEY=... \
  siscom-backend:latest
```

### Opção 2: Servidor Linux

```bash
# 1. Instalar dependências do sistema
sudo apt update
sudo apt install python3.12 python3.12-venv postgresql-15

# 2. Configurar projeto
./scripts/deploy/setup.sh

# 3. Iniciar com Gunicorn
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

Consulte [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) para guia completo.

---

## 🔐 Autenticação

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@exemplo.com",
    "password": "senha123"
  }'
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1...",
  "refresh_token": "eyJ0eXAiOiJKV1...",
  "token_type": "bearer"
}
```

### Usar Token

```bash
curl -X GET http://localhost:8000/api/v1/produtos \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1..."
```

---

## 📡 Endpoints Principais

### Auth
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### Produtos
- `GET /api/v1/produtos` - Listar
- `POST /api/v1/produtos` - Criar
- `GET /api/v1/produtos/{id}` - Detalhes
- `PUT /api/v1/produtos/{id}` - Atualizar
- `DELETE /api/v1/produtos/{id}` - Deletar

### Vendas
- `GET /api/v1/vendas` - Listar
- `POST /api/v1/vendas` - Criar
- `GET /api/v1/vendas/{id}` - Detalhes

### Dashboard
- `GET /api/v1/dashboard/stats` - Estatísticas
- `GET /api/v1/dashboard/vendas-por-dia` - Vendas por dia

### Export
- `POST /api/v1/export/dashboard` - Exportar dados
- `POST /api/v1/export/vendas` - Exportar vendas
- `POST /api/v1/export/produtos` - Exportar produtos

**Ver todos:** http://localhost:8000/docs

---

## 🔌 Integrações

### Mercado Pago
```bash
MERCADOPAGO_ACCESS_TOKEN=TEST-...
MERCADOPAGO_PUBLIC_KEY=TEST-...
```

### PagSeguro
```bash
PAGSEGURO_EMAIL=email@exemplo.com
PAGSEGURO_TOKEN=TOKEN_AQUI
```

### Correios / Melhor Envio
```bash
CORREIOS_CEP_USERNAME=usuario
MELHOR_ENVIO_CLIENT_ID=id
```

---

## 🛡️ Segurança

- ✅ JWT com refresh tokens
- ✅ RBAC (5 roles + 40+ permissões)
- ✅ Rate limiting
- ✅ CORS configurável
- ✅ Security headers
- ✅ Audit logs
- ✅ Password hashing (bcrypt)

---

## 📊 Monitoramento

### Health Checks

```bash
curl http://localhost:8000/health    # Status geral
curl http://localhost:8000/ready     # Ready para requests
curl http://localhost:8000/live      # Liveness
curl http://localhost:8000/metrics   # Métricas
```

### Logs

Logs estruturados em JSON:
```json
{
  "timestamp": "2025-11-23T10:00:00Z",
  "level": "INFO",
  "logger": "app.modules.auth",
  "message": "User logged in",
  "user_id": 123
}
```

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Add: nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👥 Autores

- **Janio Santos** - [GitHub](https://github.com/janiosantos)

---

## 🔗 Links

- **Frontend:** [siscom-frontend](https://github.com/janiosantos/siscom-frontend)
- **Documentação:** [docs/](docs/)
- **API Docs:** http://localhost:8000/docs
- **Issues:** [GitHub Issues](https://github.com/janiosantos/siscom-backend/issues)

---

<div align="center">

**Desenvolvido com ❤️ usando FastAPI**

</div>
