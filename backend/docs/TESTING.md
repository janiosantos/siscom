# Guia de Testes

## Visão Geral

O projeto implementa testes automatizados usando:
- **Pytest**: Framework de testes
- **pytest-asyncio**: Suporte para testes assíncronos
- **pytest-cov**: Cobertura de código
- **httpx**: Cliente HTTP assíncrono para testes de API

## Estrutura

```
tests/
├── conftest.py          # Fixtures compartilhadas
├── test_auth.py         # Testes de autenticação
├── test_health.py       # Testes de health checks
└── test_logging.py      # Testes de logging
```

## Instalação

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

## Executar Testes

### Todos os Testes

```bash
pytest
```

### Testes com Cobertura

```bash
pytest --cov=app --cov-report=html
```

Relatório HTML gerado em: `htmlcov/index.html`

### Testes Específicos

```bash
# Por arquivo
pytest tests/test_auth.py

# Por classe
pytest tests/test_auth.py::TestAuthEndpoints

# Por função
pytest tests/test_auth.py::TestAuthEndpoints::test_register_user

# Por marcador
pytest -m unit          # Apenas testes unitários
pytest -m integration   # Apenas testes de integração
pytest -m auth          # Apenas testes de autenticação
```

### Modo Verboso

```bash
pytest -v              # Verbose
pytest -vv             # Very verbose
pytest -s              # Mostra prints
```

### Executar Paralelamente

```bash
pip install pytest-xdist
pytest -n auto         # Usa todos os CPUs
pytest -n 4            # Usa 4 processos
```

## Marcadores (Markers)

Testes são organizados por marcadores:

- `@pytest.mark.unit`: Testes unitários (rápidos, isolados)
- `@pytest.mark.integration`: Testes de integração (com banco, API)
- `@pytest.mark.slow`: Testes que demoram mais tempo
- `@pytest.mark.auth`: Testes de autenticação
- `@pytest.mark.database`: Testes que usam banco de dados
- `@pytest.mark.api`: Testes de endpoints da API

## Fixtures

Fixtures são componentes reutilizáveis nos testes:

### Database Fixtures

```python
async def test_with_database(async_db_session):
    """Teste que usa banco de dados"""
    user = User(username="test")
    async_db_session.add(user)
    await async_db_session.commit()
```

### HTTP Client Fixtures

```python
async def test_api_endpoint(client: AsyncClient):
    """Teste de endpoint da API"""
    response = await client.get("/api/v1/produtos")
    assert response.status_code == 200
```

### Auth Fixtures

```python
async def test_authenticated_endpoint(client: AsyncClient, auth_headers: dict):
    """Teste com autenticação"""
    response = await client.get("/api/v1/vendas", headers=auth_headers)
    assert response.status_code == 200
```

## Escrever Testes

### Teste Unitário

```python
import pytest

@pytest.mark.unit
def test_password_hashing():
    """Teste de hash de senha"""
    from app.modules.auth.security import get_password_hash

    password = "MyPassword123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert len(hashed) > 50
```

### Teste de Integração (API)

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, admin_headers: dict):
    """Teste de criação de produto"""
    response = await client.post(
        "/api/v1/produtos",
        headers=admin_headers,
        json={
            "nome": "Cimento",
            "preco_venda": 25.90
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "Cimento"
    assert data["preco_venda"] == 25.90
```

### Teste com Banco de Dados

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.database
@pytest.mark.asyncio
async def test_user_creation(async_db_session: AsyncSession):
    """Teste de criação de usuário no banco"""
    from app.modules.auth.models import User
    from app.modules.auth.security import get_password_hash

    user = User(
        username="newuser",
        email="new@example.com",
        full_name="New User",
        hashed_password=get_password_hash("Pass123!")
    )

    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)

    assert user.id is not None
    assert user.username == "newuser"
```

### Teste de Exceções

```python
import pytest

@pytest.mark.unit
def test_invalid_input():
    """Teste de exceção com input inválido"""
    from app.modules.auth.schemas import UserCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        UserCreate(
            username="ab",  # Muito curto (mín: 3)
            email="invalid-email",  # Email inválido
            full_name="Name",
            password="weak"  # Senha fraca
        )
```

## Cobertura de Código

### Gerar Relatório

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Visualizar Relatório

```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Meta de Cobertura

- **Mínimo**: 50%
- **Recomendado**: 70%
- **Ideal**: 80%+

### Verificar Cobertura Mínima

```bash
pytest --cov=app --cov-fail-under=50
```

## Boas Práticas

### 1. Nomenclatura

```python
# Bom
def test_user_can_login_with_valid_credentials():
    pass

# Ruim
def test1():
    pass
```

### 2. AAA Pattern (Arrange-Act-Assert)

```python
async def test_create_product(client: AsyncClient):
    # Arrange
    product_data = {
        "nome": "Cimento",
        "preco_venda": 25.90
    }

    # Act
    response = await client.post("/api/v1/produtos", json=product_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["nome"] == "Cimento"
```

### 3. Um Conceito por Teste

```python
# Bom
def test_user_registration_creates_user():
    # Testa apenas criação de usuário
    pass

def test_user_registration_sends_email():
    # Testa apenas envio de email
    pass

# Ruim
def test_user_registration():
    # Testa criação E email E login E...
    pass
```

### 4. Testes Independentes

```python
# Bom - Cada teste cria seus próprios dados
@pytest.mark.asyncio
async def test_delete_user(async_db_session):
    user = User(username="deleteuser")
    async_db_session.add(user)
    await async_db_session.commit()

    # Delete user
    await async_db_session.delete(user)
    await async_db_session.commit()

# Ruim - Depende de estado externo
def test_delete_user():
    # Assume que usuário com ID 1 já existe
    delete_user(id=1)
```

### 5. Usar Fixtures

```python
# Bom - Usa fixture reutilizável
async def test_something(test_user: User):
    assert test_user.username == "testuser"

# Ruim - Duplicação de código
async def test_something():
    user = User(username="testuser")
    # ... código de setup duplicado
```

## Debugging

### Print Debug

```bash
pytest -s  # Mostra prints
```

```python
def test_something():
    print(f"Debug: value = {value}")
    assert value == expected
```

### PDB (Python Debugger)

```python
def test_something():
    import pdb; pdb.set_trace()
    # Execução para aqui
    assert something
```

### Pytest-PDB

```bash
pytest --pdb  # Para no primeiro erro
pytest --pdb --maxfail=1  # Para após primeira falha
```

## CI/CD

### GitHub Actions

`.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          files: ./coverage.xml
```

### Pre-commit Hook

`.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Executa testes antes de commit
pytest --maxfail=1 --disable-warnings -q

if [ $? -ne 0 ]; then
    echo "Testes falharam. Commit cancelado."
    exit 1
fi
```

## Troubleshooting

### Testes Assíncronos Não Funcionam

```bash
# Instalar pytest-asyncio
pip install pytest-asyncio

# Verificar pytest.ini
# asyncio_mode = auto
```

### Erro "fixture not found"

```python
# Verificar se fixture está em conftest.py
# Verificar escopo da fixture (function, module, session)
```

### Banco de Dados Não Reseta

```python
# Usar scope="function" em fixtures de banco
@pytest.fixture(scope="function")
async def async_db_session():
    # Cada teste tem sua própria sessão
```

### Testes Muito Lentos

```bash
# Executar em paralelo
pip install pytest-xdist
pytest -n auto

# Pular testes lentos
pytest -m "not slow"
```

### Import Error

```python
# Adicionar diretório raiz ao PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ou usar python -m pytest
python -m pytest
```

## Recursos Adicionais

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/)
- [Testing FastAPI](https://fastapi.tiangolo.com/tutorial/testing/)
- [HTTPX Documentation](https://www.python-httpx.org/)

## Próximos Passos

1. **Aumentar cobertura**: Meta 80%
2. **Testes de performance**: Locust, k6
3. **Testes E2E**: Selenium, Playwright
4. **Mutation Testing**: mutmut, cosmic-ray
5. **Property-based Testing**: Hypothesis
