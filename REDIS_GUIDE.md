# Guia Completo - Redis

Como descobrir em qual porta o Redis está rodando e como conectar.

---

## 🔍 Descobrir Porta do Redis

### Método 1: Verificar Processos (Linux/Mac)

```bash
# Ver todos os processos Redis com portas
sudo lsof -i -P -n | grep redis

# Ou com netstat
sudo netstat -tlnp | grep redis

# Ou com ss (mais moderno)
ss -tlnp | grep redis
```

**Saída exemplo:**
```
redis-ser 1234 redis    6u  IPv4  12345      0t0  TCP 127.0.0.1:6379 (LISTEN)
redis-ser 1234 redis    7u  IPv6  12346      0t0  TCP [::1]:6379 (LISTEN)
```
↑ Redis rodando na porta **6379**

### Método 2: Verificar Docker Containers

```bash
# Listar containers Redis
docker ps | grep redis

# Ver portas específicas
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep redis
```

**Saída exemplo:**
```
siscom-redis-dev    0.0.0.0:6380->6379/tcp
```
↑ Redis no container na porta **6379**, mapeado para **6380** no host

### Método 3: Tentar Conectar em Portas Comuns

```bash
# Testar porta padrão 6379
redis-cli -h localhost -p 6379 ping

# Testar porta 6380 (nossa configuração)
redis-cli -h localhost -p 6380 ping

# Se responder PONG, está funcionando!
```

### Método 4: Verificar Arquivo de Configuração

```bash
# Redis instalado via apt/yum
cat /etc/redis/redis.conf | grep "^port"

# Redis via Homebrew (Mac)
cat /usr/local/etc/redis.conf | grep "^port"

# Redis via Docker Compose
cat docker-compose.dev.yml | grep -A 2 "redis:" | grep ports
```

### Método 5: Ver Logs do Redis

```bash
# Logs do sistema (Linux)
sudo journalctl -u redis | grep "port"

# Logs do Docker
docker logs siscom-redis-dev 2>&1 | head -20
```

---

## 🔌 Como Conectar ao Redis

### Opção 1: Via redis-cli (Linha de Comando)

```bash
# Porta padrão (6379)
redis-cli

# Porta específica
redis-cli -h localhost -p 6380

# Com senha (se configurada)
redis-cli -h localhost -p 6380 -a sua_senha

# Testar conexão
redis-cli -h localhost -p 6380 ping
# Deve retornar: PONG
```

**Comandos úteis no redis-cli:**
```redis
# Testar conexão
PING

# Ver informações do servidor
INFO server

# Ver porta atual
INFO server | grep tcp_port

# Listar todas as chaves
KEYS *

# Ver quantidade de chaves
DBSIZE

# Ver chave específica
GET chave

# Definir chave
SET minhaChave "meuValor"

# Deletar chave
DEL minhaChave

# Limpar tudo (cuidado!)
FLUSHALL

# Sair
EXIT
```

### Opção 2: Via Python (Programaticamente)

```python
import redis

# Conectar
r = redis.Redis(
    host='localhost',
    port=6380,  # Nossa porta configurada
    db=0,
    decode_responses=True
)

# Testar conexão
try:
    r.ping()
    print("✅ Conectado ao Redis!")

    # Ver informações
    info = r.info('server')
    print(f"Redis versão: {info['redis_version']}")
    print(f"Porta: {info['tcp_port']}")

except redis.ConnectionError:
    print("❌ Não conseguiu conectar ao Redis")
```

### Opção 3: Via Docker Exec

```bash
# Entrar no container Redis
docker exec -it siscom-redis-dev redis-cli

# Ou executar comando direto
docker exec siscom-redis-dev redis-cli PING
```

---

## 🚀 Iniciar Redis

### Método 1: Docker (Recomendado para Dev)

```bash
# Redis standalone na porta 6380
docker run -d \
  --name redis-dev \
  -p 6380:6379 \
  redis:7-alpine

# Verificar
docker ps | grep redis
redis-cli -p 6380 ping
```

### Método 2: Docker Compose (Nosso Projeto)

```bash
# Iniciar apenas Redis
docker-compose -f docker-compose.dev.yml up -d redis

# Ver logs
docker-compose -f docker-compose.dev.yml logs -f redis

# Parar
docker-compose -f docker-compose.dev.yml down redis
```

### Método 3: Instalação Local

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl status redis-server
```

**Mac (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Windows:**
```bash
# Via WSL2 (recomendado)
wsl -d Ubuntu
sudo apt install redis-server
sudo service redis-server start

# Ou usar Docker Desktop
```

---

## 🔧 Configuração no Projeto SISCOM

### Nossa Configuração Atual

**docker-compose.dev.yml:**
```yaml
redis:
  image: redis:7-alpine
  container_name: siscom-redis-dev
  ports:
    - "6380:6379"  # Porta 6380 no host → 6379 no container
```

**.env:**
```bash
REDIS_URL=redis://localhost:6380/0
```

**Celery:**
```bash
CELERY_BROKER_URL=redis://localhost:6380/1
CELERY_RESULT_BACKEND=redis://localhost:6380/1
```

### Por Que Porta 6380?

1. **Evita conflito** com Redis local (porta 6379)
2. **Permite rodar ambos** simultaneamente
3. **Não interfere** com outros projetos

---

## 🐛 Troubleshooting

### Erro: "Could not connect to Redis"

**Verificar se está rodando:**
```bash
# Linux/Mac
ps aux | grep redis

# Ou
sudo lsof -i :6380
```

**Se não estiver, iniciar:**
```bash
# Via Docker Compose
docker-compose -f docker-compose.dev.yml up -d redis

# Ou Docker direto
docker run -d -p 6380:6379 redis:7-alpine
```

### Erro: "Connection refused"

**Causa:** Redis não está rodando ou porta errada

**Solução:**
```bash
# Testar portas comuns
redis-cli -p 6379 ping  # Porta padrão
redis-cli -p 6380 ping  # Nossa porta

# Ver se algo está na porta
sudo lsof -i :6380
```

### Erro: "NOAUTH Authentication required"

**Causa:** Redis configurado com senha

**Solução:**
```bash
# Conectar com senha
redis-cli -p 6380 -a sua_senha

# Ou no código Python
r = redis.Redis(host='localhost', port=6380, password='sua_senha')
```

### Redis travado/lento

```bash
# Ver latência
redis-cli -p 6380 --latency

# Ver estatísticas
redis-cli -p 6380 INFO stats

# Limpar cache (cuidado!)
redis-cli -p 6380 FLUSHALL
```

---

## 📊 Monitorar Redis

### Ver atividade em tempo real

```bash
# Monitor (mostra todos os comandos)
redis-cli -p 6380 MONITOR

# Ver estatísticas
redis-cli -p 6380 INFO all

# Ver conexões
redis-cli -p 6380 CLIENT LIST
```

### Benchmark

```bash
# Testar performance
redis-benchmark -h localhost -p 6380 -q

# Testar comandos específicos
redis-benchmark -h localhost -p 6380 -t set,get -n 100000 -q
```

---

## 🔐 Segurança

### Adicionar senha (Produção)

**redis.conf:**
```conf
requirepass sua_senha_forte
```

**Conectar com senha:**
```bash
redis-cli -p 6380 -a sua_senha_forte

# Ou
redis-cli -p 6380
AUTH sua_senha_forte
```

**No código:**
```python
r = redis.Redis(
    host='localhost',
    port=6380,
    password='sua_senha_forte',
    db=0
)
```

---

## 📚 Comandos Úteis Redis

### Gerenciamento de Chaves

```redis
# Listar todas as chaves
KEYS *

# Buscar por padrão
KEYS user:*

# Verificar se existe
EXISTS minhaChave

# Tipo da chave
TYPE minhaChave

# TTL (tempo de expiração)
TTL minhaChave

# Definir expiração
EXPIRE minhaChave 3600  # 1 hora

# Remover expiração
PERSIST minhaChave
```

### Strings

```redis
SET chave "valor"
GET chave
DEL chave
INCR contador
DECR contador
```

### Listas

```redis
LPUSH lista "item1"
RPUSH lista "item2"
LRANGE lista 0 -1
LPOP lista
```

### Hashes

```redis
HSET user:1 nome "João"
HSET user:1 idade "30"
HGET user:1 nome
HGETALL user:1
```

### Sets

```redis
SADD tags "python"
SADD tags "redis"
SMEMBERS tags
```

---

## 🎯 Resumo Rápido

### Descobrir porta:
```bash
sudo lsof -i -P -n | grep redis
```

### Conectar:
```bash
redis-cli -p 6380
```

### Testar:
```bash
redis-cli -p 6380 ping
```

### Iniciar (Docker):
```bash
docker-compose -f docker-compose.dev.yml up -d redis
```

### Ver informações:
```bash
redis-cli -p 6380 INFO server
```

---

## 📞 No Nosso Projeto

**Redis está configurado?** Sim, porta **6380**

**Precisa estar rodando?** Não! O backend funciona sem Redis (usa memória)

**Como iniciar?**
```bash
docker-compose -f docker-compose.dev.yml up -d redis
```

**Como verificar?**
```bash
redis-cli -p 6380 ping
```

**Última atualização:** 2025-11-24
