# ERP para Loja de Materiais de Construção

Sistema ERP completo desenvolvido em Python com FastAPI, SQLAlchemy 2.0 e Pydantic v2.

## 🚀 Stack Tecnológica

- **Backend**: Python 3.12+ com FastAPI
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrações**: Alembic
- **Validação**: Pydantic v2
- **Database**: PostgreSQL (produção), SQLite (testes)
- **Arquitetura**: Monólito Modular + Repository Pattern + Service Layer

## 📦 Módulos Implementados

### Sprint 1 - Base
- ✅ Produtos e Categorias
- ✅ Gestão de Estoque
- ✅ Vendas e PDV
- ✅ Financeiro (Contas a Pagar/Receber)
- ✅ NF-e/NFC-e
- ✅ Fluxo de Caixa

### Sprint 2 - Gestão Avançada
- ✅ Orçamentos
- ✅ Controle por Lote/Validade
- ✅ FIFO/LIFO
- ✅ Curva ABC
- ✅ Condições de Pagamento

### Sprint 3 - Mobilidade e Compras
- ✅ API Mobile
- ✅ Sugestão de Compras
- ✅ Gestão de Fornecedores
- ✅ Pedidos de Compra

### Sprint 4 - Serviços
- ✅ Ordens de Serviço completas
- ✅ Gestão de Técnicos
- ✅ Controle de Número de Série

### Sprint 5 - WMS
- ✅ Localização de Estoque
- ✅ Inventário Rotativo
- ✅ Acuracidade de Estoque

### Sprint 6 - Integrações
- ✅ Integração E-commerce
- ✅ Dashboard e KPIs
- ✅ Relatórios Gerenciais
- ✅ Conciliação Bancária (OFX)

### Sprint 7 - CRM e Performance
- ✅ CRM Básico
- ✅ Programa de Fidelidade
- ✅ Otimização SQL
- ✅ FAQ Integrado

## 🏗️ Arquitetura

```
erp/
├── app/
│   ├── core/           # Configurações, database, segurança
│   ├── modules/        # Módulos do ERP
│   │   ├── produtos/
│   │   ├── estoque/
│   │   ├── vendas/
│   │   ├── financeiro/
│   │   └── ...
│   ├── utils/          # Utilitários compartilhados
│   └── tests/          # Testes unitários e integração
├── alembic/            # Migrações do banco
├── main.py             # Ponto de entrada
└── requirements.txt    # Dependências
```

Cada módulo segue o padrão:
- `models.py` - Modelos SQLAlchemy
- `schemas.py` - Schemas Pydantic
- `repository.py` - Acesso a dados
- `service.py` - Regras de negócio
- `router.py` - Endpoints FastAPI

## 🔧 Instalação

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# Executar migrações
alembic upgrade head

# Iniciar servidor
python main.py
```

## 📚 Documentação da API

Após iniciar o servidor, acesse:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Testes específicos de um módulo
pytest app/tests/test_produtos.py
```

## 🔐 Segurança

- Autenticação JWT
- Hash de senhas com bcrypt
- Validação de dados com Pydantic
- Proteção contra SQL Injection (ORM)
- CORS configurável

## 📊 Funcionalidades Fiscais

- Leitura de XML de NF-e
- Emissão de NFC-e (Cupom Fiscal)
- Cálculo automático de impostos
- Integração com SEFAZ

## 🤝 Contribuição

Este projeto segue os princípios de:
- Clean Code
- SOLID
- Repository Pattern
- Service Layer
- DDD funcional

## 📝 Licença

Proprietário - Todos os direitos reservados

## 👨‍💻 Desenvolvimento

Desenvolvido seguindo as especificações do PROMPT_MASTER_ERP.md
