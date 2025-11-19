# Rate Limiting

## Visão Geral

O sistema implementa rate limiting (limitação de taxa) para proteger a API contra:
- Ataques de força bruta (brute force)
- Abuso de recursos
- Ataques DDoS
- Scraping não autorizado

## Tecnologia

- **slowapi**: FastAPI wrapper do Flask-Limiter
- **Storage**: Redis (produção) ou Memory (desenvolvimento)
- **Estratégia**: Fixed Window

## Limites Padrão

### Globais

| Limite | Descrição |
|--------|-----------|
| 200 requisições/minuto | Limite padrão por IP/usuário |
| 5000 requisições/hora | Limite máximo por hora |

### Por Endpoint

| Endpoint | Limite | Motivo |
|----------|--------|--------|
| POST /auth/login | 5/minuto | Proteção contra brute force |
| POST /auth/register | 3/hora | Prevenir spam de contas |
| POST /api/v1/* | 60/minuto | Operações de escrita |
| GET /api/v1/* | 200/minuto | Operações de leitura |
| GET /api/v1/relatorios/exportar | 10/hora | Operações pesadas |
| Endpoints públicos | 30/minuto | Sem autenticação |

## Identificação de Clientes

O rate limiting identifica clientes de duas formas:

1. **Usuário Autenticado**: `user:{user_id}`
   - Mais permissivo
   - Permite múltiplos dispositivos
   - Limites por usuário, não por IP

2. **IP Address**: `{ip_address}`
   - Para usuários não autenticados
   - Mais restritivo
   - Proteção básica

## Headers de Resposta

Todas as respostas incluem headers informativos:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1637251200
```

| Header | Descrição |
|--------|-----------|
| X-RateLimit-Limit | Limite total permitido |
| X-RateLimit-Remaining | Requisições restantes |
| X-RateLimit-Reset | Timestamp quando o limite reseta |

## Resposta de Rate Limit Excedido

**Status Code**: `429 Too Many Requests`

```json
{
  "error": "Rate limit exceeded",
  "detail": "5 per 1 minute"
}
```

## Uso em Código

### Aplicar Rate Limit a Endpoint

```python
from app.middleware.rate_limit import limiter

@router.post("/vendas")
@limiter.limit("30 per minute")  # 30 requisições por minuto
async def criar_venda(venda_data: VendaCreate):
    return {"message": "Venda criada"}
```

### Limites Pré-definidos

```python
from app.middleware.rate_limit import (
    LOGIN_LIMIT,      # "5 per minute"
    REGISTER_LIMIT,   # "3 per hour"
    WRITE_LIMIT,      # "60 per minute"
    READ_LIMIT,       # "200 per minute"
    PUBLIC_LIMIT,     # "30 per minute"
    EXPORT_LIMIT,     # "10 per hour"
)

@router.post("/produtos")
@limiter.limit(WRITE_LIMIT)
async def criar_produto(produto_data: ProdutoCreate):
    return {"message": "Produto criado"}
```

### Múltiplos Limites

```python
# Endpoint com múltiplos limites
@router.post("/nfe/emitir")
@limiter.limit("10 per minute")  # Limite por minuto
@limiter.limit("100 per hour")   # Limite por hora
async def emitir_nfe(nfe_data: NFeCreate):
    return {"message": "NF-e emitida"}
```

### Limites Dinâmicos

```python
from fastapi import Request

def get_dynamic_limit(request: Request) -> str:
    """Limite dinâmico baseado no tipo de usuário"""
    user = getattr(request.state, "user", None)

    if user and user.is_superuser:
        return "1000 per minute"  # Superuser tem limite maior
    elif user:
        return "100 per minute"   # Usuário autenticado
    else:
        return "30 per minute"    # Usuário anônimo

@router.get("/produtos")
@limiter.limit(get_dynamic_limit)
async def listar_produtos(request: Request):
    return {"produtos": []}
```

### Isentar Endpoint de Rate Limiting

```python
from slowapi import Limiter

# Usar limiter.exempt em endpoints que não devem ter limite
@router.get("/health")
@limiter.exempt
async def health_check():
    return {"status": "healthy"}
```

## Configuração

### Desenvolvimento (Memory Storage)

No `.env`:

```env
# Rate limiting usa memória (não persiste entre restarts)
REDIS_URL=memory://
```

### Produção (Redis Storage)

No `.env`:

```env
# Rate limiting usa Redis (persiste entre restarts)
REDIS_URL=redis://localhost:6379/0
```

### Configurar Redis

**Docker Compose**:

```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

**Iniciar Redis**:

```bash
docker-compose up -d redis
```

## Estratégias de Rate Limiting

### Fixed Window (Padrão)

- Reseta em intervalos fixos (ex: a cada minuto exato)
- Simples e eficiente
- Vulnerável a "burst" no início do período

```python
limiter = Limiter(
    key_func=get_identifier,
    strategy="fixed-window"
)
```

### Sliding Window

- Mais suave, evita "bursts"
- Mais complexo computacionalmente

```python
limiter = Limiter(
    key_func=get_identifier,
    strategy="moving-window"
)
```

## Monitoramento

### Logs de Rate Limit

Quando rate limit é excedido, é gerado log:

```json
{
  "level": "WARNING",
  "event": "rate_limit_exceeded",
  "ip_address": "192.168.1.100",
  "user_id": 123,
  "endpoint": "/api/v1/vendas",
  "limit": "60 per minute",
  "timestamp": "2025-11-19T12:34:56.789Z"
}
```

### Métricas Importantes

1. **Taxa de 429 (Too Many Requests)**:
   - Alta taxa pode indicar ataque
   - Ou limites muito restritivos

2. **IPs com alto volume**:
   - Monitorar IPs que batem no limite frequentemente

3. **Endpoints mais limitados**:
   - Identificar endpoints que precisam ajuste de limites

## Whitelist / Blacklist

### Permitir IPs Específicos

```python
WHITELISTED_IPS = ["192.168.1.100", "10.0.0.1"]

def get_identifier(request: Request) -> str:
    ip = get_remote_address(request)

    # IPs whitelistados não têm limite
    if ip in WHITELISTED_IPS:
        return "unlimited"

    # Outros seguem lógica normal
    user = getattr(request.state, "user", None)
    if user:
        return f"user:{user.id}"
    return ip
```

### Bloquear IPs Específicos

```python
from fastapi import HTTPException, status

BLACKLISTED_IPS = ["1.2.3.4", "5.6.7.8"]

@app.middleware("http")
async def block_blacklisted_ips(request: Request, call_next):
    ip = get_remote_address(request)

    if ip in BLACKLISTED_IPS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP bloqueado"
        )

    response = await call_next(request)
    return response
```

## Testes

### Testar Rate Limiting

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_rate_limit(client: AsyncClient):
    """Testa rate limit no login (5 por minuto)"""

    # Faz 5 tentativas (deve passar)
    for i in range(5):
        response = await client.post("/api/v1/auth/login", json={
            "username": "test",
            "password": "wrong"
        })
        assert response.status_code in [200, 401]

    # 6ª tentativa deve ser bloqueada
    response = await client.post("/api/v1/auth/login", json={
        "username": "test",
        "password": "wrong"
    })
    assert response.status_code == 429
    assert "rate limit" in response.json()["error"].lower()
```

### Verificar Headers

```python
@pytest.mark.asyncio
async def test_rate_limit_headers(client: AsyncClient):
    response = await client.get("/api/v1/produtos")

    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

    limit = int(response.headers["X-RateLimit-Limit"])
    remaining = int(response.headers["X-RateLimit-Remaining"])

    assert remaining < limit
```

## Troubleshooting

### Rate Limit Não Funciona

**Problema**: Limites não são aplicados

**Soluções**:
1. Verificar se `setup_rate_limiting(app)` foi chamado
2. Verificar se Redis está rodando (em produção)
3. Verificar logs de startup para erros

### Limites Muito Restritivos

**Problema**: Usuários legítimos sendo bloqueados

**Soluções**:
1. Aumentar limites para endpoints específicos
2. Diferenciar limites por tipo de usuário
3. Usar sliding window ao invés de fixed window

### Redis Não Conecta

**Problema**: `Error connecting to Redis`

**Soluções**:
1. Verificar se Redis está rodando: `docker ps`
2. Verificar REDIS_URL no `.env`
3. Usar `memory://` para desenvolvimento

### Limites Resetan Inesperadamente

**Problema**: Usando memory storage (não persiste)

**Solução**: Usar Redis em produção

```env
REDIS_URL=redis://localhost:6379/0
```

## Boas Práticas

1. **Diferentes limites por endpoint**:
   - Endpoints de autenticação: mais restritivos
   - Endpoints de leitura: mais permissivos
   - Endpoints pesados (relatórios): muito restritivos

2. **Usar Redis em produção**:
   - Persiste limites entre restarts
   - Permite múltiplas instâncias da API

3. **Monitorar 429s**:
   - Taxa alta pode indicar ataque
   - Ou necessidade de ajustar limites

4. **Informar o cliente**:
   - Headers X-RateLimit-* ajudam clientes a se adaptarem
   - Mensagens de erro claras

5. **Whitelist para serviços internos**:
   - Serviços de monitoramento
   - Health checks
   - Serviços internos conhecidos

6. **Rate limit progressivo**:
   - Aumentar limites para usuários premium
   - Diminuir para usuários suspeitos

## Segurança

### Proteção Implementada

✅ **Brute Force**: Login limitado a 5 tentativas/minuto
✅ **DDoS**: Limite global de 200 req/minuto por IP
✅ **Scraping**: Limites por hora previnem scraping massivo
✅ **Spam**: Registro limitado a 3/hora

### Proteções Adicionais Recomendadas

- **CAPTCHA**: Após múltiplas falhas de login
- **Account Lockout**: Bloquear conta após N tentativas
- **IP Blacklist**: Bloquear IPs maliciosos automaticamente
- **Web Application Firewall (WAF)**: CloudFlare, AWS WAF

## Performance

### Impacto

- **Memory Storage**: ~0.1ms por requisição
- **Redis Storage**: ~1-2ms por requisição

### Otimização

1. **Redis Local**: Menor latência
2. **Redis Cluster**: Alta disponibilidade
3. **Cache de Headers**: Reduzir overhead

## Próximos Passos

1. **Rate Limiting Adaptativo**: Ajustar limites dinamicamente
2. **IP Geolocation**: Limites diferentes por região
3. **Cost-based Rate Limiting**: Limites baseados em "custo" da operação
4. **API Keys**: Limites específicos por API key
