# AI Coding Agent Instructions for ERP Sistema

## Quick Start
- **Language**: Python 3.12+ with FastAPI (async-first)
- **Main entry**: `main.py` - FastAPI app with router registration
- **Database**: SQLAlchemy 2.0 async with PostgreSQL/SQLite
- **Run dev**: `make run` (Uvicorn reload), Tests: `make test`
- **Architecture**: Modular monolith with ~25 feature modules

## Architecture Overview

### Module Structure (Each feature folder pattern)
```
app/modules/{feature}/
├── models.py      # SQLAlchemy ORM models (extend Base from app.core.database)
├── schemas.py     # Pydantic request/response models
├── router.py      # FastAPI endpoints with full docstrings
├── service.py     # Business logic and validations (never touches DB directly)
├── repository.py  # Data access layer (queries only, no business logic)
└── dependencies.py (optional) # FastAPI dependency injection
```

**Critical**: Service layer applies business rules BEFORE repository calls. Service raises `ERPException` subclasses (not generic errors). Repository is thin and query-focused.

### Core Infrastructure
- `app/core/config.py` - Settings from `.env` via Pydantic
- `app/core/database.py` - AsyncSession factory, Base class, init_db/close_db
- `app/core/exceptions.py` - Custom exceptions (NotFoundException, ValidationException, InsufficientStockException, BusinessRuleException)
- `app/core/logging.py` - JSON structured logging with correlation IDs
- `app/core/security.py` - JWT token handling, password hashing

### Integration Points
- **Payment Gateways**: `app/integrations/{provider}_router.py` for API routes + `{provider}.py` for integration logic (Mercado Pago, Cielo, GetNet, Sicoob)
- **Marketplaces/Shipping**: MercadoLivre, Melhor Envio routers + modules
- **Email/SMS**: `app/integrations/email.py` and `sms.py` with Jinja2 templates

## Key Patterns & Conventions

### Exception Handling
Always raise specific `ERPException` subclasses in service layer:
```python
# Good - in service.py
if not produto:
    raise NotFoundException(f"Produto {id} não encontrado")
if quantidade > estoque:
    raise InsufficientStockException(nome, estoque, quantidade)
```
Main router automatically catches and returns appropriate HTTP status codes.

### Database & Queries
- **Async patterns only**: Use `await` everywhere, never blocking calls
- **Session management**: Inject via `Depends(get_db)` in routers
- **Transactions**: Automatic via get_db context manager - no manual commit needed
- **Alembic migrations**: `make migrate-create msg="description"` then edit `alembic/versions/`

### Testing Patterns
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.auth`
- Fixtures in `tests/conftest.py` provide `async_db_engine`, `async_db_session`, `authenticated_client`
- Test file naming: `test_{module}.py` in `tests/` root
- Async test functions: Use `async def test_*` with `pytest-asyncio`
- Run tests: `make test` (with coverage), `make test-fast` (no coverage)

### Request/Response Models
Use Pydantic v2 schemas with Config class:
```python
class ProdutoResponse(BaseModel):
    id: int
    descricao: str
    preco_venda: float
    
    model_config = ConfigDict(from_attributes=True)  # For ORM mapping
```

### Router Docstrings
Every endpoint needs docstring with:
- Brief description
- **Validações**: Business rule checks
- **Exemplo de requisição** (if POST/PUT)
- Returns/Raises info (Pydantic handles response model)

### Logging
Structured JSON logging via `get_logger(__name__)`:
```python
from app.core.logging import get_logger
logger = get_logger(__name__)
logger.info("User login", extra={"user_id": 123, "ip": "192.168.1.1"})
```

## Critical Developer Workflows

### Create New Feature Module
1. Create folder: `app/modules/{feature_name}/`
2. Add `__init__.py` (empty or with imports)
3. Create files in order: models → schemas → repository → service → router
4. Register router in `main.py` with try/except import
5. Import models in `app/models.py` for SQLAlchemy metadata
6. Add Alembic migration if new tables: `make migrate-create msg="add_{feature}"`

### Run & Debug Locally
- Dev server: `make run` (auto-reload on file changes, http://localhost:8000)
- API docs: http://localhost:8000/docs (Swagger) or /redoc
- Database: `make db-shell` opens PostgreSQL CLI
- Redis: `make redis-shell` if caching needed

### Code Quality
- Format: `make format` (Black + isort)
- Lint: `make lint` (flake8, mypy, bandit)
- All checks: `make all` (format, lint, test)

## Data Flow Example: Create Produto
1. **Router** (HTTP POST `/api/v1/produtos/`) receives `ProdutoCreate` schema
2. **Service.create_produto()** validates:
   - Código barras unique (query via repository)
   - Categoria exists & active (category repository)
   - preco_venda >= preco_custo
   - Raises ValidationException if fails
3. **Repository.create()** inserts row and returns ORM instance
4. **Router** returns `ProdutoResponse` (Pydantic auto-converts ORM to dict)
5. FastAPI middleware logs request with correlation ID, Sentry tracks errors

## Common Tasks

### Add New Endpoint
Edit `app/modules/{feature}/router.py`:
```python
@router.post("/", response_model=OutputSchema, status_code=status.HTTP_201_CREATED)
async def create_item(data: InputSchema, db: AsyncSession = Depends(get_db)):
    """Create new item. **Validações**: ..."""
    service = ItemService(db)
    return await service.create(data)
```

### Add New Column to Table
1. Edit model in `app/modules/{feature}/models.py` 
2. Run `make migrate-create msg="add_column_name"`
3. Edit generated file in `alembic/versions/` to ensure migration is correct
4. Run `make migrate` to apply
5. Update schema files to include new field

### Handle External API Integration
1. Create `app/integrations/{api_name}.py` with class for API calls
2. Create `app/integrations/{api_name}_router.py` for endpoints
3. Wrap in try/except with proper logging and fallback behavior
4. Store API keys in `.env` and load via `settings`

## Important Files & Their Roles
- `main.py` - Don't edit directly unless adding global middleware/exception handlers
- `app/core/` - Shared infrastructure (config, database, logging, exceptions)
- `requirements.txt` - Pin exact versions; test changes with `make test`
- `.env` - Local dev overrides (ignored by git, use `.env.example`)
- `pytest.ini` - Test configuration (markers, coverage settings)
- `Makefile` - All common tasks defined as targets

## Async Patterns
- **Always async in routers/services**: DB queries, API calls, file I/O
- **Never use time.sleep()**: Use `asyncio.sleep()`
- **Concurrent requests**: Multiple coroutines naturally concurrent via FastAPI/Uvicorn

## Multi-tenant Patterns
Some modules support multi-empresa (tenant ID). Always filter by tenant in queries if present in module. Check `models.py` for `empresa_id` field.

## Compliance Features
- **LGPD**: `app/modules/lgpd/` handles data deletion/consent
- **NFe/Fiscal**: Certificate handling in config, signing via `signxml` library
- **Payments**: PCI compliance via gateway integrations (never store card data locally)

## Gotchas & Tips
- **SQLite in tests**: Uses file-based, not in-memory (async limitation)
- **Correlation IDs**: Automatically injected via middleware, use in logging
- **Rate limiting**: Configured via `slowapi` in `app.middleware.rate_limit`
- **CORS**: More restrictive in production (check `main.py` conditional)
- **Docker**: Single Dockerfile for all services; compose files for dev/prod
