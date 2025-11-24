# Sistema de Logging Estruturado

## Visão Geral

O sistema implementa logging estruturado com formato JSON, correlation IDs para rastreamento distribuído e integração opcional com Sentry para monitoramento de erros.

## Características

### 1. Logging em JSON

Todos os logs são formatados em JSON estruturado, facilitando:
- Parsing automatizado
- Indexação em sistemas como ELK Stack, Splunk, Datadog
- Queries eficientes
- Análise de logs

Exemplo de log:
```json
{
  "timestamp": "2025-11-19T12:34:56.789Z",
  "level": "INFO",
  "logger": "api.request",
  "module": "correlation",
  "function": "dispatch",
  "line": 45,
  "environment": "production",
  "application": "ERP Materiais de Construção",
  "version": "1.0.0",
  "event": "http_request",
  "method": "POST",
  "path": "/api/v1/vendas",
  "status_code": 201,
  "duration_ms": 45.23,
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "client_ip": "192.168.1.100",
  "user_id": "user_123"
}
```

### 2. Correlation IDs

Cada requisição recebe um ID único (`X-Correlation-ID`) que permite:
- Rastrear uma requisição através de múltiplos serviços
- Correlacionar logs de diferentes componentes
- Debug de fluxos complexos

**Como funciona:**
- Cliente pode enviar header `X-Correlation-ID`
- Se não enviado, é gerado automaticamente (UUID)
- ID é retornado no header da resposta
- Todos os logs da requisição incluem o correlation ID

### 3. Categorias de Logs

#### Logs de Requisições HTTP
Automaticamente gerados pelo middleware:
```python
from app.core.logging import log_request

log_request(
    method="POST",
    path="/api/v1/vendas",
    status_code=201,
    duration_ms=45.23,
    correlation_id="...",
    user_id="user_123"
)
```

#### Logs de Eventos de Negócio
Para rastrear eventos importantes:
```python
from app.core.logging import log_business_event

log_business_event(
    event_name="venda_criada",
    correlation_id=correlation_id,
    user_id=user_id,
    venda_id=venda.id,
    valor_total=venda.valor_total,
    cliente_id=venda.cliente_id
)
```

#### Logs de Erros
Para logging estruturado de exceções:
```python
from app.core.logging import log_error

try:
    # código
except Exception as e:
    log_error(
        error=e,
        correlation_id=correlation_id,
        user_id=user_id,
        context={"venda_id": venda_id}
    )
```

### 4. Níveis de Log

Configurável via variável de ambiente `LOG_LEVEL`:

- **DEBUG**: Informações detalhadas de debug (apenas desenvolvimento)
- **INFO**: Eventos normais da aplicação
- **WARNING**: Eventos incomuns mas não erros
- **ERROR**: Erros que afetam funcionalidade
- **CRITICAL**: Erros críticos que podem parar a aplicação

**Produção:** Recomendado `INFO` ou `WARNING`
**Desenvolvimento:** `DEBUG`

### 5. Integração com Sentry (Opcional)

Para monitoramento de erros em produção:

1. Criar conta no [Sentry](https://sentry.io)
2. Obter DSN do projeto
3. Configurar no `.env`:
```env
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

**Benefícios:**
- Rastreamento automático de exceções
- Agregação de erros similares
- Stack traces completos
- Contexto de usuário e requisição
- Alertas por email/Slack
- Release tracking

## Health Checks

### Endpoints Disponíveis

#### GET /health
Health check básico - verifica se aplicação está rodando

**Resposta:**
```json
{
  "status": "healthy",
  "application": "ERP Materiais de Construção",
  "version": "1.0.0",
  "timestamp": "2025-11-19T12:34:56.789Z"
}
```

#### GET /ready
Readiness check - verifica dependências (banco de dados)

**Resposta (sucesso):**
```json
{
  "status": "ready",
  "application": "ERP Materiais de Construção",
  "version": "1.0.0",
  "timestamp": "2025-11-19T12:34:56.789Z",
  "checks": {
    "database": {
      "status": "healthy",
      "type": "postgresql"
    }
  }
}
```

**Resposta (falha):**
```json
{
  "status": "not_ready",
  "checks": {
    "database": {
      "status": "unhealthy",
      "type": "postgresql"
    }
  }
}
```

#### GET /live
Liveness check - para Kubernetes/Docker

**Resposta:**
```json
{
  "status": "alive",
  "timestamp": "2025-11-19T12:34:56.789Z"
}
```

#### GET /metrics
Métricas básicas do sistema

**Resposta:**
```json
{
  "application": "ERP Materiais de Construção",
  "version": "1.0.0",
  "timestamp": "2025-11-19T12:34:56.789Z",
  "system": {
    "cpu_percent": 12.5,
    "memory_mb": 245.67,
    "threads": 8
  },
  "environment": "production"
}
```

## Uso em Módulos

### Exemplo Básico

```python
from app.core.logging import get_logger, log_business_event
from app.middleware.correlation import get_correlation_id

logger = get_logger(__name__)

async def criar_venda(venda_data, user_id):
    correlation_id = get_correlation_id()

    logger.info("Criando nova venda", extra={
        "correlation_id": correlation_id,
        "user_id": user_id,
        "cliente_id": venda_data.cliente_id
    })

    try:
        venda = await venda_service.criar(venda_data)

        # Log de evento de negócio
        log_business_event(
            event_name="venda_criada",
            correlation_id=correlation_id,
            user_id=user_id,
            venda_id=venda.id,
            valor_total=venda.valor_total
        )

        return venda

    except Exception as e:
        logger.error("Erro ao criar venda", extra={
            "correlation_id": correlation_id,
            "user_id": user_id,
            "error": str(e)
        }, exc_info=True)
        raise
```

### Exemplo com Context Manager

```python
import time
from app.core.logging import get_logger

logger = get_logger(__name__)

async def processo_longo():
    correlation_id = get_correlation_id()

    start = time.time()
    logger.info("Iniciando processo longo", extra={"correlation_id": correlation_id})

    try:
        # código do processo
        resultado = await executar_processo()

        duration = (time.time() - start) * 1000
        logger.info("Processo concluído", extra={
            "correlation_id": correlation_id,
            "duration_ms": duration,
            "resultado": resultado
        })

    except Exception as e:
        duration = (time.time() - start) * 1000
        logger.error("Processo falhou", extra={
            "correlation_id": correlation_id,
            "duration_ms": duration
        }, exc_info=True)
        raise
```

## Configuração

### Variáveis de Ambiente

Adicionar ao `.env`:

```env
# Logging
LOG_LEVEL=INFO
SENTRY_DSN=  # Opcional

# Debug
DEBUG=False  # True em desenvolvimento, False em produção
```

### Kubernetes/Docker

Para integração com Kubernetes:

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: erp-api
    image: erp-api:latest
    livenessProbe:
      httpGet:
        path: /live
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 30
    readinessProbe:
      httpGet:
        path: /ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 10
```

## Monitoramento

### Agregação de Logs

Logs estruturados podem ser facilmente agregados usando:

**ELK Stack (Elasticsearch + Logstash + Kibana):**
```bash
# Logstash pipeline
input {
  file {
    path => "/var/log/erp/*.log"
    codec => "json"
  }
}

filter {
  # Logs já estão em JSON, sem necessidade de parsing
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "erp-logs-%{+YYYY.MM.dd}"
  }
}
```

**CloudWatch (AWS):**
```python
# Logs automaticamente parseados por serem JSON
# Criar metric filters para alertas
```

### Queries Úteis

**Encontrar todas requisições de um usuário:**
```
user_id:"user_123"
```

**Rastrear uma requisição específica:**
```
correlation_id:"a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

**Requisições lentas (>1000ms):**
```
event:"http_request" AND duration_ms:>1000
```

**Erros em produção:**
```
level:"ERROR" AND environment:"production"
```

**Eventos de vendas criadas:**
```
event:"venda_criada"
```

## Melhores Práticas

1. **Sempre inclua correlation_id** nos logs
2. **Use log_business_event** para eventos importantes de negócio
3. **Não logue informações sensíveis** (senhas, tokens, dados de cartão)
4. **Em produção, use nível INFO ou WARNING**
5. **Configure Sentry para monitorar erros**
6. **Agregue logs em sistema centralizado**
7. **Crie alertas para erros críticos**
8. **Monitore métricas de performance** (duration_ms)

## Troubleshooting

### Logs não aparecem
- Verificar `LOG_LEVEL` no `.env`
- Verificar se logging está configurado em `main.py`

### Correlation ID não aparece
- Verificar se `CorrelationIdMiddleware` está registrado
- Verificar ordem dos middlewares (deve ser o primeiro)

### Sentry não funciona
- Verificar `SENTRY_DSN` no `.env`
- Verificar instalação: `pip install sentry-sdk`
- Verificar logs de startup para mensagens do Sentry

### Performance degradada
- Reduzir nível de log em produção (INFO ou WARNING)
- Desabilitar SQLAlchemy echo
- Configurar log rotation
