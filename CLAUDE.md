# CLAUDE.md - ERP para Loja de Materiais de Construção

**Sistema ERP completo em Python com FastAPI, SQLAlchemy 2.0 e Pydantic v2**

---

## 📋 Visão Geral do Projeto

Este é um ERP (Enterprise Resource Planning) completo para lojas de materiais de construção, desenvolvido em Python usando arquitetura modular monolítica. O projeto está em **produção-ready** com 92% de conclusão das fases planejadas.

### Status Atual (2025-11-19)
- ✅ **Fase 1 - Segurança**: 100% Completa
- ✅ **Fase 2 - Compliance Brasil**: 100% Completa
- ✅ **Fase 3 - Escalabilidade**: 83% Completa
- 🔄 **Fase 4 - Integrações**: 80% Completa (em progresso)
- ✅ **Fase 5 - Analytics**: 100% Infraestrutura

### Documentos Importantes
- `PROGRESSO_IMPLEMENTACAO.md` - Status detalhado de cada fase
- `PROMPT_MASTER_ERP.md` - Especificação original do projeto
- `NOVOS_RECURSOS.md` - Roadmap e recursos pendentes
- `README.md` - Instruções de instalação e uso
- `docs/` - Documentação técnica específica

---

## 🏗️ Arquitetura do Projeto

### Stack Tecnológica

```yaml
Backend:
  Framework: FastAPI 0.109.0
  Language: Python 3.12+
  ORM: SQLAlchemy 2.0 (async)
  Migrations: Alembic
  Validation: Pydantic v2

Database:
  Production: PostgreSQL (asyncpg)
  Testing: SQLite (in-memory)
  Cache: Redis (opcional)

Security:
  Auth: JWT (access + refresh tokens)
  RBAC: 5 roles padrão + 40+ permissões granulares
  Password: bcrypt hashing
  Rate Limiting: slowapi

Testing:
  Framework: pytest + pytest-asyncio
  Coverage: pytest-cov
  Mocking: httpx, faker

Integrations:
  Payments: Mercado Pago, PagSeguro
  Shipping: Correios, Melhor Envio
  Communication: SendGrid/AWS SES, Twilio
  Marketplaces: Mercado Livre

Monitoring:
  Logging: JSON structured logging
  APM: Sentry (opcional)
  Health: /health, /ready, /live, /metrics
  BI: Metabase (docker-compose)
```

### Estrutura de Diretórios

```
siscom/
├── app/
│   ├── core/                      # Configurações centrais
│   │   ├── config.py              # Configurações da aplicação
│   │   ├── database.py            # Setup do banco de dados
│   │   ├── security.py            # Utilitários de segurança
│   │   ├── logging.py             # Logging estruturado
│   │   ├── health.py              # Health checks
│   │   ├── cache.py               # Redis cache manager
│   │   ├── celery_app.py          # Tarefas assíncronas
│   │   └── exceptions.py          # Exceções customizadas
│   │
│   ├── middleware/                # Middlewares
│   │   ├── correlation.py         # Correlation IDs
│   │   ├── rate_limit.py          # Rate limiting
│   │   ├── security_headers.py    # Security headers
│   │   └── tenant.py              # Multi-tenant isolation
│   │
│   ├── modules/                   # Módulos de negócio (ver abaixo)
│   │   ├── auth/                  # Autenticação e autorização
│   │   ├── produtos/              # Gestão de produtos
│   │   ├── categorias/            # Categorias de produtos
│   │   ├── estoque/               # Gestão de estoque
│   │   ├── vendas/                # Vendas
│   │   ├── pdv/                   # Ponto de Venda
│   │   ├── financeiro/            # Contas a pagar/receber
│   │   ├── nfe/                   # NF-e/NFC-e
│   │   ├── fiscal/                # Compliance fiscal
│   │   ├── orcamentos/            # Orçamentos
│   │   ├── compras/               # Compras
│   │   ├── fornecedores/          # Fornecedores
│   │   ├── os/                    # Ordens de Serviço
│   │   ├── mobile/                # API Mobile
│   │   ├── ecommerce/             # E-commerce
│   │   ├── crm/                   # CRM
│   │   ├── fidelidade/            # Programa de fidelidade
│   │   ├── clientes/              # Gestão de clientes
│   │   ├── relatorios/            # Relatórios
│   │   ├── pagamentos/            # PIX, Boleto, Conciliação
│   │   ├── condicoes_pagamento/   # Condições de pagamento
│   │   ├── lgpd/                  # Conformidade LGPD
│   │   └── multiempresa/          # Multi-tenant
│   │
│   ├── integrations/              # Integrações externas
│   │   ├── mercadopago.py         # Gateway Mercado Pago
│   │   ├── mercadopago_router.py
│   │   ├── pagseguro.py           # Gateway PagSeguro
│   │   ├── pagseguro_router.py
│   │   ├── correios.py            # Cálculo de frete
│   │   ├── melhorenvio.py         # Melhor Envio
│   │   ├── frete_router.py
│   │   ├── email.py               # SendGrid/AWS SES
│   │   ├── sms.py                 # Twilio SMS/WhatsApp
│   │   ├── email_templates.py     # Templates HTML
│   │   ├── comunicacao_router.py
│   │   ├── mercadolivre.py        # Marketplace
│   │   └── marketplace_router.py
│   │
│   ├── tasks/                     # Celery tasks
│   │   └── webhooks.py
│   │
│   ├── utils/                     # Utilitários
│   │   ├── validators.py          # Validadores (CPF, CNPJ, etc)
│   │   └── xml_reader.py          # Leitura de XML NF-e
│   │
│   └── tests/                     # Testes unitários (mirror da estrutura)
│
├── alembic/                       # Migrações do banco
│   ├── versions/                  # Arquivos de migração
│   └── env.py
│
├── tests/                         # Testes de integração
│   ├── conftest.py                # Fixtures compartilhadas
│   ├── test_auth.py
│   ├── test_health.py
│   ├── test_pix.py
│   ├── test_boleto.py
│   ├── test_conciliacao.py
│   ├── test_mercadopago.py
│   ├── test_frete_router.py
│   ├── test_comunicacao_router.py
│   └── test_marketplace_router.py
│
├── scripts/                       # Scripts utilitários
│   ├── init_auth.py              # Inicializar usuários/roles
│   └── backup/                   # Scripts de backup
│
├── docs/                          # Documentação
│   ├── AUTHENTICATION.md
│   ├── LOGGING.md
│   ├── RATE_LIMITING.md
│   ├── BACKUP.md
│   ├── TESTING.md
│   ├── PAGAMENTOS.md
│   └── INTEGRACAO_MERCADOPAGO.md
│
├── main.py                        # Entry point da aplicação
├── requirements.txt               # Dependências Python
├── pytest.ini                     # Configuração do pytest
├── alembic.ini                    # Configuração do Alembic
├── Makefile                       # Comandos úteis (30+)
├── .env.example                   # Template de variáveis de ambiente
├── .pre-commit-config.yaml        # Hooks de pre-commit
├── docker-compose.metabase.yml    # BI com Metabase
└── .github/workflows/ci.yml       # CI/CD pipeline
```

---

## 🎯 Padrão de Módulos (EXTREMAMENTE IMPORTANTE)

Cada módulo segue **RIGOROSAMENTE** este padrão de 5 arquivos:

### 1. `models.py` - Modelos SQLAlchemy 2.0

```python
"""
Modelos de banco de dados usando SQLAlchemy 2.0 ORM

RESPONSABILIDADES:
- Definir tabelas e colunas
- Definir relacionamentos (ForeignKey, relationship)
- Definir constraints (unique, index, check)
- Usar type hints modernos (Mapped[tipo])

NUNCA:
- Incluir regras de negócio
- Incluir validações complexas
- Acessar outros módulos diretamente
"""

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime

class Produto(Base):
    __tablename__ = "produtos"

    # Campos
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    descricao: Mapped[str] = mapped_column(String(255), nullable=False)
    preco_venda: Mapped[float] = mapped_column(Numeric(10, 2))
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"))

    # Relacionamentos
    categoria: Mapped["Categoria"] = relationship(back_populates="produtos")

    # Índices compostos
    __table_args__ = (
        Index('idx_codigo_categoria', 'codigo', 'categoria_id'),
    )
```

### 2. `schemas.py` - Schemas Pydantic v2

```python
"""
DTOs (Data Transfer Objects) usando Pydantic v2

RESPONSABILIDADES:
- Validar entrada da API (create, update)
- Serializar saída da API (response)
- Validações simples (tamanho, formato, range)

NUNCA:
- Incluir lógica de negócio
- Acessar banco de dados
- Ter dependências de outros módulos
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

# Schema de criação (entrada)
class ProdutoCreate(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50)
    descricao: str = Field(..., min_length=1, max_length=255)
    preco_venda: float = Field(..., gt=0)
    categoria_id: int

# Schema de atualização (entrada parcial)
class ProdutoUpdate(BaseModel):
    codigo: Optional[str] = Field(None, min_length=1, max_length=50)
    descricao: Optional[str] = None
    preco_venda: Optional[float] = Field(None, gt=0)
    categoria_id: Optional[int] = None

# Schema de resposta (saída)
class ProdutoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    descricao: str
    preco_venda: float
    categoria_id: int
    created_at: datetime
    updated_at: datetime
```

### 3. `repository.py` - Data Access Layer

```python
"""
Repository Pattern - Acesso a dados

RESPONSABILIDADES:
- CRUD básico (create, read, update, delete)
- Queries complexas (filtros, joins, agregações)
- Paginação
- Retornar dados brutos do banco

NUNCA:
- Aplicar regras de negócio
- Fazer cálculos complexos
- Chamar outros services
- Tratar exceções de negócio (só de BD)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from .models import Produto

class ProdutoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, produto_data: dict) -> Produto:
        """Criar novo produto"""
        produto = Produto(**produto_data)
        self.db.add(produto)
        await self.db.commit()
        await self.db.refresh(produto)
        return produto

    async def get_by_id(self, produto_id: int) -> Optional[Produto]:
        """Buscar produto por ID"""
        result = await self.db.execute(
            select(Produto)
            .options(selectinload(Produto.categoria))
            .where(Produto.id == produto_id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        categoria_id: Optional[int] = None
    ) -> List[Produto]:
        """Listar produtos com filtros"""
        query = select(Produto).options(selectinload(Produto.categoria))

        if categoria_id:
            query = query.where(Produto.categoria_id == categoria_id)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, produto_id: int, data: dict) -> Optional[Produto]:
        """Atualizar produto"""
        produto = await self.get_by_id(produto_id)
        if not produto:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(produto, key, value)

        await self.db.commit()
        await self.db.refresh(produto)
        return produto

    async def delete(self, produto_id: int) -> bool:
        """Deletar produto"""
        produto = await self.get_by_id(produto_id)
        if not produto:
            return False

        await self.db.delete(produto)
        await self.db.commit()
        return True

    async def count_by_categoria(self, categoria_id: int) -> int:
        """Contar produtos por categoria"""
        result = await self.db.execute(
            select(func.count(Produto.id))
            .where(Produto.categoria_id == categoria_id)
        )
        return result.scalar()
```

### 4. `service.py` - Business Logic Layer

```python
"""
Service Layer - Regras de negócio

RESPONSABILIDADES:
- TODAS as regras de negócio
- Validações complexas
- Cálculos
- Orquestração entre repositories
- Integração com outros módulos
- Tratamento de exceções de negócio

NUNCA:
- Acessar banco diretamente (usar repository)
- Conter SQL direto
- Expor modelos de banco (usar schemas)
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from .repository import ProdutoRepository
from .schemas import ProdutoCreate, ProdutoUpdate, ProdutoResponse
from app.core.exceptions import NotFoundException, BusinessException

class ProdutoService:
    def __init__(self, db: AsyncSession):
        self.repository = ProdutoRepository(db)
        self.db = db

    async def criar_produto(self, data: ProdutoCreate) -> ProdutoResponse:
        """
        Criar novo produto com validações de negócio
        """
        # Validação: código único
        produto_existente = await self.repository.get_by_codigo(data.codigo)
        if produto_existente:
            raise BusinessException(
                f"Produto com código {data.codigo} já existe"
            )

        # Validação: categoria existe
        # (aqui poderia chamar CategoriaService se necessário)

        # Regra de negócio: calcular preço de custo sugerido
        preco_custo_sugerido = data.preco_venda * 0.6

        produto_data = data.model_dump()
        produto_data['preco_custo'] = preco_custo_sugerido

        produto = await self.repository.create(produto_data)
        return ProdutoResponse.model_validate(produto)

    async def atualizar_produto(
        self,
        produto_id: int,
        data: ProdutoUpdate
    ) -> ProdutoResponse:
        """
        Atualizar produto com validações
        """
        produto = await self.repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        # Validação: código único (se mudando)
        if data.codigo and data.codigo != produto.codigo:
            existente = await self.repository.get_by_codigo(data.codigo)
            if existente:
                raise BusinessException(
                    f"Código {data.codigo} já está em uso"
                )

        update_data = data.model_dump(exclude_unset=True)
        produto_atualizado = await self.repository.update(produto_id, update_data)
        return ProdutoResponse.model_validate(produto_atualizado)

    async def listar_produtos(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[ProdutoResponse]:
        """Listar produtos"""
        produtos = await self.repository.list_all(skip=skip, limit=limit)
        return [ProdutoResponse.model_validate(p) for p in produtos]

    async def obter_produto(self, produto_id: int) -> ProdutoResponse:
        """Obter produto por ID"""
        produto = await self.repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")
        return ProdutoResponse.model_validate(produto)
```

### 5. `router.py` - API Endpoints

```python
"""
Router - Endpoints FastAPI

RESPONSABILIDADES:
- Definir rotas HTTP
- Validar entrada com schemas
- Chamar services
- Retornar respostas HTTP
- Documentação OpenAPI
- Autenticação e autorização

NUNCA:
- Incluir lógica de negócio
- Acessar repository diretamente
- Fazer queries SQL
- Ter regras complexas
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.models import User

from .service import ProdutoService
from .schemas import ProdutoCreate, ProdutoUpdate, ProdutoResponse

router = APIRouter()

@router.post(
    "/",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo produto",
    description="Cria um novo produto com validações de negócio"
)
async def criar_produto(
    data: ProdutoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("produtos.create"))
):
    """
    Criar novo produto

    Requer permissão: produtos.create

    Exemplo de requisição:
    ```json
    {
        "codigo": "CIMENTO-001",
        "descricao": "Cimento CP-II 50kg",
        "preco_venda": 32.90,
        "categoria_id": 1
    }
    ```
    """
    service = ProdutoService(db)
    return await service.criar_produto(data)

@router.get(
    "/",
    response_model=List[ProdutoResponse],
    summary="Listar produtos",
    description="Lista todos os produtos com paginação"
)
async def listar_produtos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Listar produtos com paginação

    Requer autenticação
    """
    service = ProdutoService(db)
    return await service.listar_produtos(skip=skip, limit=limit)

@router.get(
    "/{produto_id}",
    response_model=ProdutoResponse,
    summary="Obter produto por ID",
    description="Retorna detalhes de um produto específico"
)
async def obter_produto(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obter produto específico"""
    service = ProdutoService(db)
    return await service.obter_produto(produto_id)

@router.put(
    "/{produto_id}",
    response_model=ProdutoResponse,
    summary="Atualizar produto"
)
async def atualizar_produto(
    produto_id: int,
    data: ProdutoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("produtos.update"))
):
    """Atualizar produto existente"""
    service = ProdutoService(db)
    return await service.atualizar_produto(produto_id, data)

@router.delete(
    "/{produto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar produto"
)
async def deletar_produto(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("produtos.delete"))
):
    """Deletar produto"""
    service = ProdutoService(db)
    await service.deletar_produto(produto_id)
```

---

## 🔐 Autenticação e Autorização

### Sistema RBAC Completo

O sistema usa **Role-Based Access Control (RBAC)** com:
- 5 roles padrão: Admin, Gerente, Vendedor, Estoquista, Financeiro
- 40+ permissões granulares
- JWT com access + refresh tokens
- Audit trail (logs de todas as ações)

### Como Usar Autenticação

```python
from fastapi import Depends
from app.modules.auth.dependencies import (
    get_current_user,       # Apenas autenticado
    require_permission,     # Permissão específica
    require_role,           # Role específica
    is_admin               # Admin apenas
)
from app.modules.auth.models import User

# Apenas usuário autenticado
@router.get("/")
async def endpoint(
    current_user: User = Depends(get_current_user)
):
    pass

# Permissão específica
@router.post("/")
async def endpoint(
    current_user: User = Depends(require_permission("vendas.create"))
):
    pass

# Role específica
@router.get("/admin")
async def endpoint(
    current_user: User = Depends(require_role("Admin"))
):
    pass

# Admin apenas
@router.delete("/")
async def endpoint(
    current_user: User = Depends(is_admin)
):
    pass
```

### Permissões Disponíveis

```python
# Produtos
"produtos.view", "produtos.create", "produtos.update", "produtos.delete"

# Vendas
"vendas.view", "vendas.create", "vendas.update", "vendas.cancel"

# Financeiro
"financeiro.view", "financeiro.create", "financeiro.approve"

# E mais 30+ permissões...
```

### Inicializar Sistema de Auth

```bash
# Criar usuário admin padrão e roles
python scripts/init_auth.py

# Ou via Makefile
make init-auth
```

---

## 🧪 Testes

### Estrutura de Testes

```
tests/
├── conftest.py              # Fixtures globais
├── test_auth.py             # Testes de autenticação
├── test_produtos.py         # Testes de produtos
├── test_vendas.py           # Testes de vendas
└── ...

app/modules/[modulo]/tests/  # Testes unitários do módulo
```

### Fixtures Importantes

```python
# conftest.py

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.database import Base

@pytest.fixture
async def db_session():
    """Fixture de sessão de banco SQLite in-memory"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

@pytest.fixture
async def client(db_session):
    """Cliente HTTP de teste"""
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        yield client

@pytest.fixture
async def admin_token(db_session):
    """Token JWT de admin para testes"""
    from app.modules.auth.service import AuthService

    service = AuthService(db_session)
    # Criar admin e retornar token
    ...
    return token
```

### Exemplo de Teste

```python
# test_produtos.py

import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_criar_produto(client: AsyncClient, admin_token: str):
    """Teste de criação de produto"""
    response = await client.post(
        "/api/v1/produtos/",
        json={
            "codigo": "TEST-001",
            "descricao": "Produto Teste",
            "preco_venda": 100.0,
            "categoria_id": 1
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == "TEST-001"
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_listar_produtos(client: AsyncClient, admin_token: str):
    """Teste de listagem de produtos"""
    response = await client.get(
        "/api/v1/produtos/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

### Executar Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Testes específicos
pytest tests/test_produtos.py

# Testes com output verboso
pytest -v

# Testes paralelos (mais rápido)
pytest -n auto

# Via Makefile
make test
make test-cov
```

---

## 🔄 Migrações de Banco de Dados

### Criar Nova Migração

```bash
# Gerar migração automaticamente
alembic revision --autogenerate -m "Adicionar campo X na tabela Y"

# Criar migração manual
alembic revision -m "Minha migração"

# Via Makefile
make migration message="Adicionar campo X"
```

### Aplicar Migrações

```bash
# Aplicar todas as migrações pendentes
alembic upgrade head

# Voltar uma migração
alembic downgrade -1

# Ir para revisão específica
alembic upgrade abc123

# Via Makefile
make migrate
make migrate-down
```

### Estrutura de Migração

```python
"""Adicionar campo email em clientes

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2025-11-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123def456'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Aplicar mudanças"""
    op.add_column(
        'clientes',
        sa.Column('email', sa.String(255), nullable=True)
    )

    # Criar índice
    op.create_index(
        'idx_clientes_email',
        'clientes',
        ['email']
    )

def downgrade() -> None:
    """Reverter mudanças"""
    op.drop_index('idx_clientes_email', table_name='clientes')
    op.drop_column('clientes', 'email')
```

---

## 🚀 Desenvolvimento

### Setup do Ambiente

```bash
# 1. Clonar repositório
git clone <repo-url>
cd siscom

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Copiar .env.example para .env
cp .env.example .env

# 5. Configurar variáveis de ambiente
# Editar .env com suas configurações

# 6. Aplicar migrações
alembic upgrade head

# 7. Inicializar autenticação
python scripts/init_auth.py

# 8. Executar servidor
python main.py

# Ou via Makefile
make install
make setup
make run
```

### Variáveis de Ambiente Importantes

```bash
# .env

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/siscom
TEST_DATABASE_URL=sqlite+aiosqlite:///:memory:

# Security
SECRET_KEY=sua-chave-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME="ERP Materiais de Construção"
APP_VERSION="1.0.0"
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:3000"]

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# Celery (opcional)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Sentry (opcional)
SENTRY_DSN=

# Integrações - Mercado Pago
MERCADOPAGO_ACCESS_TOKEN=TEST-...
MERCADOPAGO_PUBLIC_KEY=TEST-...
MERCADOPAGO_WEBHOOK_SECRET=

# Integrações - PagSeguro
PAGSEGURO_EMAIL=
PAGSEGURO_TOKEN=
PAGSEGURO_SANDBOX=true

# Integrações - Correios
CORREIOS_CEP_USERNAME=
CORREIOS_CEP_PASSWORD=

# Integrações - Melhor Envio
MELHOR_ENVIO_CLIENT_ID=
MELHOR_ENVIO_CLIENT_SECRET=
MELHOR_ENVIO_REFRESH_TOKEN=

# Integrações - Email
EMAIL_PROVIDER=sendgrid  # ou aws_ses
SENDGRID_API_KEY=
AWS_SES_ACCESS_KEY=
AWS_SES_SECRET_KEY=
AWS_SES_REGION=

# Integrações - SMS/WhatsApp
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
TWILIO_WHATSAPP_NUMBER=

# Integrações - Mercado Livre
MERCADOLIVRE_CLIENT_ID=
MERCADOLIVRE_CLIENT_SECRET=
```

### Comandos Úteis (Makefile)

```bash
# Desenvolvimento
make dev              # Instalar deps de dev
make run              # Executar servidor
make run-reload       # Executar com auto-reload

# Testes
make test             # Executar testes
make test-cov         # Testes com cobertura
make test-watch       # Testes em modo watch

# Qualidade de Código
make lint             # Executar linters
make format           # Formatar código (black, isort)
make type-check       # Type checking (mypy)
make security-check   # Security scan (bandit)

# Banco de Dados
make migrate          # Aplicar migrações
make migrate-down     # Reverter última migração
make migration        # Criar nova migração
make db-reset         # Resetar banco de dados

# Autenticação
make init-auth        # Inicializar usuários/roles

# Docker
make docker-build     # Build imagem
make docker-run       # Executar container
make docker-stop      # Parar containers

# Backup
make backup           # Backup manual
make restore          # Restaurar backup

# Limpeza
make clean            # Limpar cache e arquivos temp
make clean-all        # Limpeza completa

# Ajuda
make help             # Listar todos os comandos
```

---

## 📡 Integrações Externas

### Mercado Pago (95% Completo)

```python
from app.integrations.mercadopago import MercadoPagoClient

# Criar pagamento PIX
client = MercadoPagoClient()
payment = await client.create_pix_payment(
    amount=100.0,
    description="Venda #123",
    payer_email="cliente@email.com"
)

# QR Code está em payment["point_of_interaction"]["transaction_data"]
qr_code = payment["point_of_interaction"]["transaction_data"]["qr_code"]
qr_code_base64 = payment["point_of_interaction"]["transaction_data"]["qr_code_base64"]

# Webhook processa automaticamente e atualiza banco
```

**Documentação**: `docs/INTEGRACAO_MERCADOPAGO.md`

### PagSeguro (100% Completo)

```python
from app.integrations.pagseguro import PagSeguroClient

# Criar pagamento PIX
client = PagSeguroClient()
payment = await client.create_pix_payment(
    amount=100.0,
    description="Venda #123",
    customer_name="João Silva",
    customer_email="joao@email.com",
    customer_cpf="12345678900"
)

# Criar pagamento com cartão
card_payment = await client.create_card_payment(
    amount=100.0,
    installments=3,
    card_encrypted="CARD_ENCRYPTED_DATA",
    holder_name="João Silva"
)
```

### Correios e Melhor Envio

```python
from app.integrations.correios import CorreiosClient
from app.integrations.melhorenvio import MelhorEnvioClient

# Calcular frete Correios
correios = CorreiosClient()
frete = await correios.calcular_frete(
    cep_origem="01310100",
    cep_destino="04543907",
    peso=1.0,  # kg
    servico="04014"  # SEDEX
)

# Calcular frete Melhor Envio
melhor_envio = MelhorEnvioClient()
fretes = await melhor_envio.calcular_frete(
    cep_destino="04543907",
    peso=1.0,
    altura=10,
    largura=20,
    comprimento=30
)
```

### Email e SMS

```python
from app.integrations.email import EmailClient
from app.integrations.sms import SMSClient

# Enviar email
email_client = EmailClient()
await email_client.send_email(
    to="cliente@email.com",
    subject="Pedido Confirmado",
    html_content="<h1>Obrigado pela compra!</h1>"
)

# Enviar SMS
sms_client = SMSClient()
await sms_client.send_sms(
    to="+5511999999999",
    message="Seu pedido foi confirmado!"
)

# Enviar WhatsApp
await sms_client.send_whatsapp(
    to="+5511999999999",
    message="Seu pedido foi enviado!"
)
```

### Mercado Livre

```python
from app.integrations.mercadolivre import MercadoLivreClient

# Criar anúncio
ml = MercadoLivreClient(access_token="...")
anuncio = await ml.create_item(
    title="Cimento CP-II 50kg",
    price=32.90,
    quantity=100,
    category_id="MLB123"
)

# Atualizar estoque
await ml.update_stock(item_id="MLB123456", quantity=50)

# Sincronização automática disponível em:
# app/modules/estoque/marketplace_sync_service.py
```

---

## 📊 Módulos Implementados

### ✅ Sprint 1 - Base (100%)
- **Produtos**: CRUD completo, código de barras, preços
- **Categorias**: Hierarquia de categorias
- **Estoque**: Controle de saldo, movimentações
- **Vendas**: Pedidos, itens, totais
- **PDV**: Interface de ponto de venda
- **Financeiro**: Contas a pagar/receber, fluxo de caixa
- **NF-e/NFC-e**: Estrutura básica, importação XML
- **Clientes**: Cadastro PF/PJ

### ✅ Sprint 2 - Gestão Avançada (100%)
- **Orçamentos**: Criação, conversão para venda
- **Lotes**: Controle por lote e validade
- **FIFO/LIFO**: Saída automática por lote
- **Curva ABC**: Classificação de produtos
- **Condições de Pagamento**: Múltiplas condições

### ✅ Sprint 3 - Mobilidade e Compras (100%)
- **API Mobile**: Endpoints otimizados
- **Compras**: Pedidos de compra, sugestões
- **Fornecedores**: Cadastro e avaliação

### ✅ Sprint 4 - Serviços (100%)
- **Ordens de Serviço**: Completo com técnicos
- **Número de Série**: Rastreabilidade

### ✅ Sprint 5 - WMS (100%)
- **Localização**: Endereçamento de estoque
- **Inventário Rotativo**: Contagens parciais
- **Acuracidade**: KPI de precisão

### ✅ Sprint 6 - Integrações (90%)
- **E-commerce**: Sincronização básica
- **Dashboard**: KPIs e métricas
- **Relatórios**: Diversos relatórios gerenciais
- **Conciliação Bancária**: Import OFX/CSV

### ✅ Sprint 7 - CRM (100%)
- **CRM**: Gestão de relacionamento
- **Fidelidade**: Programa de pontos
- **FAQ**: Sistema de ajuda

### ✅ Fase 1 - Segurança (100%)
- **Autenticação**: JWT com refresh token
- **RBAC**: Roles e permissões
- **Audit Log**: Rastreamento de ações
- **Rate Limiting**: Proteção DDoS
- **Logging**: Logs estruturados JSON
- **Health Checks**: Monitoramento

### ✅ Fase 2 - Compliance Brasil (100%)
- **PIX**: Geração de QR Code, webhooks
- **Boleto**: CNAB 240/400
- **Conciliação**: Matching automático
- **Certificado Digital**: A1 com assinatura XML
- **NF-e**: Geração completa de XML
- **SPED Fiscal**: EFD-ICMS/IPI
- **LGPD**: Consentimentos, anonimização

### ✅ Fase 3 - Escalabilidade (83%)
- **Redis Cache**: Sistema distribuído
- **Multiempresa**: Multi-tenant
- **Webhooks**: Celery tasks
- ⏳ **Import/Export**: Estrutura preparada

### 🔄 Fase 4 - Integrações (80%)
- **Mercado Pago**: 95% completo (PIX + Cartão)
- **PagSeguro**: 100% completo
- **Correios**: 100% completo
- **Melhor Envio**: 100% completo
- **Email/SMS**: 100% completo
- **Mercado Livre**: 100% completo
- ⏳ **Cielo**: Pendente
- ⏳ **Amazon**: Pendente

### ✅ Fase 5 - Analytics (100% Infra)
- **Metabase**: Docker-compose pronto
- ⏳ **ML**: Aguardando dados históricos

---

## 🎨 Boas Práticas

### 1. Separação de Responsabilidades

```
❌ ERRADO:
router.py contém SQL
service.py acessa banco diretamente
models.py tem lógica de negócio

✅ CORRETO:
router.py → service.py → repository.py → database
Cada camada tem responsabilidade única
```

### 2. Type Hints Obrigatórios

```python
# ✅ CORRETO
async def criar_produto(self, data: ProdutoCreate) -> ProdutoResponse:
    ...

# ❌ ERRADO
async def criar_produto(self, data):
    ...
```

### 3. Async/Await Everywhere

```python
# ✅ CORRETO
async def get_produto(self, id: int) -> Optional[Produto]:
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

# ❌ ERRADO
def get_produto(self, id: int):
    return self.db.query(Produto).filter(...).first()
```

### 4. Exceções Customizadas

```python
from app.core.exceptions import (
    NotFoundException,
    BusinessException,
    ValidationException
)

# ✅ CORRETO
if not produto:
    raise NotFoundException(f"Produto {id} não encontrado")

# ❌ ERRADO
if not produto:
    raise Exception("Produto não encontrado")
```

### 5. Documentação OpenAPI

```python
# ✅ CORRETO
@router.post(
    "/",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar produto",
    description="Cria um novo produto com validações",
    responses={
        201: {"description": "Produto criado com sucesso"},
        400: {"description": "Dados inválidos"},
        409: {"description": "Produto já existe"}
    }
)
async def criar_produto(...):
    """
    Criar novo produto

    - **codigo**: Código único do produto
    - **descricao**: Descrição do produto
    - **preco_venda**: Preço de venda (deve ser > 0)
    """
    pass

# ❌ ERRADO
@router.post("/")
async def criar_produto(...):
    pass
```

### 6. Validações no Service

```python
# ✅ CORRETO - Service
async def criar_produto(self, data: ProdutoCreate):
    # Validar código único
    if await self.repository.exists_by_codigo(data.codigo):
        raise BusinessException("Código já existe")

    # Validar categoria existe
    categoria = await self.categoria_repo.get(data.categoria_id)
    if not categoria:
        raise NotFoundException("Categoria não encontrada")

    # Criar produto
    return await self.repository.create(data)

# ❌ ERRADO - Repository
async def create(self, data):
    # Validações aqui estão no lugar errado!
    if self.exists(data.codigo):
        raise Exception("Código existe")
    ...
```

### 7. Testes Abrangentes

```python
# Testar casos de sucesso
async def test_criar_produto_sucesso():
    ...

# Testar casos de erro
async def test_criar_produto_codigo_duplicado():
    ...

async def test_criar_produto_categoria_invalida():
    ...

# Testar edge cases
async def test_criar_produto_preco_zero():
    ...
```

### 8. Commits Semânticos

```bash
# ✅ CORRETO
feat(produtos): adicionar campo codigo_interno
fix(vendas): corrigir cálculo de desconto
docs(api): atualizar documentação de autenticação
test(estoque): adicionar testes de movimentação
refactor(financeiro): simplificar lógica de juros

# ❌ ERRADO
update
fix bug
changes
wip
```

---

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro de Migração

```bash
# Resetar banco (CUIDADO: apaga dados!)
make db-reset

# Ou manualmente
alembic downgrade base
alembic upgrade head
```

#### 2. Token Inválido

```bash
# Reinicializar sistema de auth
python scripts/init_auth.py

# Verificar SECRET_KEY no .env
```

#### 3. Testes Falhando

```bash
# Limpar cache do pytest
pytest --cache-clear

# Executar com output verboso
pytest -vv

# Executar teste específico
pytest tests/test_auth.py::test_login -v
```

#### 4. Import Error

```bash
# Verificar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

#### 5. Banco de Dados Travado

```bash
# PostgreSQL
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'siscom';

# SQLite (fechar todas conexões)
rm siscom.db  # Recria com migrações
```

---

## 📚 Recursos Adicionais

### Documentação Técnica

- `docs/AUTHENTICATION.md` - Sistema de autenticação e RBAC
- `docs/LOGGING.md` - Logging estruturado e monitoramento
- `docs/RATE_LIMITING.md` - Proteção contra abuso
- `docs/BACKUP.md` - Estratégia de backup e recovery
- `docs/TESTING.md` - Guia de testes
- `docs/PAGAMENTOS.md` - Integrações de pagamento
- `docs/INTEGRACAO_MERCADOPAGO.md` - Mercado Pago detalhado

### Relatórios de Progresso

- `PROGRESSO_IMPLEMENTACAO.md` - Status atualizado de cada fase
- `NOVOS_RECURSOS.md` - Funcionalidades planejadas
- `RELATORIO_FINAL_SESSAO.md` - Resumo da última sessão
- `VALIDACAO_COMPLETA.md` - Validações e conformidades

### Especificação Original

- `PROMPT_MASTER_ERP.md` - Especificação completa dos 7 Sprints

---

## 🤝 Contribuindo

### Ao Adicionar Novo Módulo

1. **Criar estrutura padrão**:
   ```bash
   mkdir app/modules/novo_modulo
   touch app/modules/novo_modulo/{__init__.py,models.py,schemas.py,repository.py,service.py,router.py}
   ```

2. **Seguir o padrão dos 5 arquivos** (ver seção "Padrão de Módulos")

3. **Criar migração**:
   ```bash
   alembic revision --autogenerate -m "Adicionar módulo novo_modulo"
   ```

4. **Registrar router em main.py**:
   ```python
   from app.modules.novo_modulo.router import router as novo_modulo_router
   app.include_router(novo_modulo_router, prefix="/api/v1/novo-modulo", tags=["Novo Módulo"])
   ```

5. **Criar testes**:
   ```bash
   touch tests/test_novo_modulo.py
   ```

6. **Documentar**:
   - Atualizar `PROGRESSO_IMPLEMENTACAO.md`
   - Adicionar exemplos em `docs/` se necessário

### Ao Adicionar Nova Integração

1. **Criar client em `app/integrations/`**:
   ```python
   # app/integrations/servico.py
   class ServicoClient:
       def __init__(self):
           self.api_key = settings.SERVICO_API_KEY
           ...
   ```

2. **Criar router se necessário**:
   ```python
   # app/integrations/servico_router.py
   router = APIRouter()

   @router.post("/servico/acao")
   async def acao(...):
       ...
   ```

3. **Adicionar variáveis de ambiente em `.env.example`**

4. **Criar testes**:
   ```python
   # tests/test_servico.py
   @pytest.mark.asyncio
   async def test_servico_client():
       ...
   ```

5. **Documentar em `docs/INTEGRACAO_SERVICO.md`**

---

## 🎓 Para Novos Desenvolvedores

### Checklist de Onboarding

- [ ] Ler este CLAUDE.md completamente
- [ ] Ler `README.md`
- [ ] Configurar ambiente local (seguir "Setup do Ambiente")
- [ ] Executar testes: `make test`
- [ ] Explorar API docs: http://localhost:8000/docs
- [ ] Revisar estrutura de um módulo completo (ex: `app/modules/produtos/`)
- [ ] Entender fluxo: Router → Service → Repository
- [ ] Estudar sistema de autenticação: `docs/AUTHENTICATION.md`
- [ ] Ler sobre integrações: `docs/INTEGRACAO_MERCADOPAGO.md`
- [ ] Fazer primeiro commit seguindo padrão semântico

### Arquivos Essenciais para Ler

1. `main.py` - Entry point
2. `app/core/config.py` - Configurações
3. `app/core/database.py` - Setup do banco
4. `app/modules/auth/` - Sistema de autenticação
5. `app/modules/produtos/` - Exemplo completo de módulo
6. `PROGRESSO_IMPLEMENTACAO.md` - Estado atual do projeto

---

## 📞 Suporte

### Logs e Debugging

```python
# Usar logger estruturado
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("Operação realizada", extra={
    "user_id": user.id,
    "produto_id": produto.id,
    "action": "create"
})

logger.error("Erro ao processar", extra={
    "error": str(e),
    "trace": traceback.format_exc()
})
```

### Health Checks

```bash
# Verificar saúde da aplicação
curl http://localhost:8000/health

# Verificar readiness
curl http://localhost:8000/ready

# Verificar liveness
curl http://localhost:8000/live

# Ver métricas
curl http://localhost:8000/metrics
```

### Monitoramento com Sentry

```python
# .env
SENTRY_DSN=https://...@sentry.io/...

# Erros são automaticamente reportados ao Sentry
# quando SENTRY_DSN está configurado
```

---

## 🔄 Fluxo de Trabalho Git

### Branches

```
main (ou master)           # Produção
├── develop                # Desenvolvimento
│   ├── feature/nova-funcionalidade
│   ├── fix/correcao-bug
│   ├── refactor/melhoria
│   └── docs/documentacao
```

### Workflow

```bash
# 1. Criar branch
git checkout -b feature/nova-funcionalidade

# 2. Fazer alterações e commits
git add .
git commit -m "feat(modulo): descrição da mudança"

# 3. Executar testes
make test

# 4. Executar linters
make lint

# 5. Push
git push -u origin feature/nova-funcionalidade

# 6. Abrir Pull Request no GitHub
```

### Pre-commit Hooks

Configurados em `.pre-commit-config.yaml`:
- Black (formatação)
- isort (imports)
- flake8 (linting)
- mypy (type checking)
- bandit (security)

```bash
# Instalar hooks
pre-commit install

# Executar manualmente
pre-commit run --all-files
```

---

## 🎯 Objetivos de Qualidade

### Métricas

- ✅ Cobertura de testes: > 85%
- ✅ Type hints: 100% em código novo
- ✅ Documentação: Todos os endpoints
- ✅ Performance: < 200ms para endpoints CRUD
- ✅ Security: Rate limiting em todos os endpoints públicos

### Code Review Checklist

- [ ] Código segue padrão de 5 arquivos?
- [ ] Tem testes unitários?
- [ ] Tem testes de integração?
- [ ] Type hints estão completos?
- [ ] Documentação OpenAPI está clara?
- [ ] Segue princípios SOLID?
- [ ] Não há SQL em services/routers?
- [ ] Exceções são tratadas corretamente?
- [ ] Logging adequado?
- [ ] Migrations foram criadas?

---

## 📝 Notas Finais

### Filosofia do Projeto

1. **Simplicidade**: Código claro é melhor que código esperto
2. **Consistência**: Seguir padrões é mais importante que otimizar
3. **Testabilidade**: Se é difícil testar, está mal projetado
4. **Documentação**: Código é lido mais vezes do que escrito
5. **Segurança**: Sempre pensar em segurança primeiro

### Princípios SOLID

- **S**ingle Responsibility: Cada classe/função tem uma responsabilidade
- **O**pen/Closed: Aberto para extensão, fechado para modificação
- **L**iskov Substitution: Subclasses devem ser substituíveis
- **I**nterface Segregation: Interfaces específicas são melhores
- **D**ependency Inversion: Depender de abstrações, não de implementações

### Arquitetura Hexagonal (Ports & Adapters)

```
Domain (models) ← Services (business logic) ← Repositories (data access)
                        ↑
                    Routers (HTTP adapters)
                        ↑
                  FastAPI (framework)
```

---

**Última atualização**: 2025-11-20
**Versão**: 1.0.0
**Branch**: claude/claude-md-mi7h1tgt8tvary5r-01YbW6jafQw2dxzgrTpPc2tu
**Progresso Total**: 92%

---

Para dúvidas ou sugestões, consulte:
- Issues do projeto no GitHub
- Documentação em `docs/`
- Relatórios de progresso (`PROGRESSO_IMPLEMENTACAO.md`)

**Sistema pronto para produção! 🚀**
