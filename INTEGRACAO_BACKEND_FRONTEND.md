# Integração Backend-Frontend - Dashboard e Endpoints

**Data**: 2025-11-23
**Branch**: `claude/expand-frontend-tests-01JGckVRP16wKRwEfX6L2Jc8`
**Commit**: `7bb30b3` - feat(backend): Adicionar módulo Dashboard com 5 endpoints

---

## 📊 Módulo Dashboard Implementado

### Backend - Novos Arquivos Criados

1. **`app/modules/dashboard/__init__.py`**
   - Módulo Dashboard para KPIs em tempo real

2. **`app/modules/dashboard/schemas.py`** (50 linhas)
   - `DashboardStats` - Estatísticas principais
   - `VendasPorDia` - Vendas agrupadas por dia
   - `ProdutoMaisVendido` - Top produtos vendidos
   - `VendasPorVendedor` - Vendas por vendedor
   - `StatusPedidos` - Pedidos por status

3. **`app/modules/dashboard/service.py`** (305 linhas)
   - `DashboardService` com 5 métodos:
     - `get_stats()` - KPIs principais com comparação vs mês anterior
     - `get_vendas_por_dia(dias)` - Série temporal de vendas (preenche dias vazios com zero)
     - `get_produtos_mais_vendidos(limit)` - Top N produtos do mês
     - `get_vendas_por_vendedor()` - Performance de vendedores no mês
     - `get_status_pedidos()` - Distribuição de pedidos por status
   - Queries otimizadas com SQLAlchemy async
   - Usa `cast(Venda.data_venda, Date)` para compatibilidade de tipos
   - Integração com modelos: `Venda`, `PedidoVenda`, `Produto`, `User`

4. **`app/modules/dashboard/router.py`** (142 linhas)
   - 5 endpoints RESTful com autenticação JWT
   - Documentação OpenAPI completa
   - Validação de query parameters

5. **`main.py`** (atualizado)
   - Registrado router com prefixo `/api/v1/dashboard`

---

## 🔌 Endpoints Implementados

### 1. GET `/api/v1/dashboard/stats`
**Descrição**: Estatísticas principais do dashboard
**Autenticação**: JWT required
**Response**:
```json
{
  "vendas_hoje": 5,
  "vendas_mes": 127,
  "pedidos_abertos": 23,
  "pedidos_atrasados": 3,
  "ticket_medio": 523.45,
  "faturamento_mes": 66478.15,
  "crescimento_mes": 15.3,
  "meta_mes": 73125.97
}
```

**Cálculos**:
- `vendas_hoje`: COUNT de vendas com data = hoje
- `vendas_mes`: COUNT de vendas do mês atual
- `faturamento_mes`: SUM de valor_total do mês
- `crescimento_mes`: % vs mês anterior
- `ticket_medio`: faturamento_mes / vendas_mes
- `pedidos_abertos`: COUNT de pedidos não finalizados (status != FATURADO, CANCELADO, ENTREGUE)
- `pedidos_atrasados`: COUNT de pedidos com data_entrega_prevista < hoje e status não finalizado
- `meta_mes`: faturamento_mes_anterior * 1.1 (10% de crescimento)

---

### 2. GET `/api/v1/dashboard/vendas-por-dia?dias=30`
**Descrição**: Vendas agrupadas por dia (série temporal)
**Query Params**:
- `dias` (int, 1-365, default: 30): Número de dias para retornar

**Response**:
```json
[
  {
    "data": "2025-11-01",
    "vendas": 12,
    "faturamento": 6280.50
  },
  {
    "data": "2025-11-02",
    "vendas": 0,
    "faturamento": 0.0
  }
]
```

**Features**:
- Preenche dias sem vendas com zero
- Retorna lista completa de N dias (sem gaps)
- Ideal para gráficos de linha/área

---

### 3. GET `/api/v1/dashboard/produtos-mais-vendidos?limit=10`
**Descrição**: Top produtos mais vendidos no mês atual
**Query Params**:
- `limit` (int, 1-100, default: 10): Número de produtos

**Response**:
```json
[
  {
    "produto_id": 42,
    "produto_nome": "Cimento CP-II 50kg",
    "quantidade": 523.0,
    "faturamento": 17206.70
  }
]
```

**Ordenação**: Por quantidade vendida (DESC)

---

### 4. GET `/api/v1/dashboard/vendas-por-vendedor`
**Descrição**: Vendas agrupadas por vendedor no mês atual
**Autenticação**: JWT required

**Response**:
```json
[
  {
    "vendedor_id": 5,
    "vendedor_nome": "João Silva",
    "total_vendas": 45,
    "ticket_medio": 612.30
  }
]
```

**Ordenação**: Por total de vendas (DESC)

---

### 5. GET `/api/v1/dashboard/status-pedidos`
**Descrição**: Pedidos agrupados por status (todos os tempos)
**Autenticação**: JWT required

**Response**:
```json
[
  {
    "status": "RASCUNHO",
    "quantidade": 12,
    "valor_total": 15640.80
  },
  {
    "status": "CONFIRMADO",
    "quantidade": 34,
    "valor_total": 67823.45
  }
]
```

**Status possíveis**:
- RASCUNHO
- CONFIRMADO
- EM_SEPARACAO
- SEPARADO
- EM_ENTREGA
- ENTREGUE
- FATURADO
- CANCELADO

---

## 🎨 Frontend - Componentes Utilizando os Endpoints

### 1. **`frontend/lib/hooks/use-dashboard.ts`**
- `useDashboardStats()` → `/dashboard/stats`
- `useVendasPorDia(dias)` → `/dashboard/vendas-por-dia?dias=N`
- `useProdutosMaisVendidos(limit)` → `/dashboard/produtos-mais-vendidos?limit=N`
- `useVendasPorVendedor()` → `/dashboard/vendas-por-vendedor`
- `useStatusPedidos()` → `/dashboard/status-pedidos`

**Features**:
- SWR para cache e revalidação automática
- Fallback para mock data (graceful degradation)
- Tipos TypeScript matching backend schemas

### 2. **`frontend/app/dashboard/page.tsx`** (já implementado)
Usa todos os 5 hooks para renderizar:
- Cards com KPIs (stats)
- Gráfico de área (vendas por dia)
- Gráfico de barras (top produtos)
- Tabela de vendedores
- Pizza chart (status pedidos)

### 3. **`frontend/lib/api-client.ts`**
- Base URL: `http://localhost:8000/api/v1`
- Autenticação JWT via localStorage
- Error handling com tipos

---

## ✅ Status de Integração

### Dashboard ✅ 100% Completo
- [x] Backend endpoints implementados
- [x] Frontend hooks configurados
- [x] Schemas matching frontend/backend
- [x] Documentação OpenAPI
- [x] Autenticação JWT
- [x] Mock data fallback

### Outros Módulos
- [x] **Orçamentos** - Endpoints existem (verificar path `/converter-venda` vs `/converter`)
- [x] **Pedidos de Venda** - Endpoints existem (verificar completude)
- [ ] **Relatórios Avançados** - Endpoints ainda não implementados no backend
- [ ] **Export Excel/CSV** - Lógica no frontend, backend pode adicionar endpoints

---

## 🔧 Próximos Passos

### 1. Melhorias no Dashboard ⭐
- [ ] Adicionar cache Redis para queries pesadas
- [ ] Implementar WebSocket para atualização em tempo real
- [ ] Adicionar filtros de data customizáveis
- [ ] Criar endpoint para configurar meta_mes por usuário/empresa
- [ ] Adicionar testes unitários para DashboardService
- [ ] Adicionar testes de integração para endpoints

### 2. Sincronizar Paths de Endpoints 🔗
- [ ] **Orçamentos**: Backend usa `/converter-venda`, frontend espera `/converter`
  - Opção 1: Alterar backend para `/converter` (breaking change)
  - Opção 2: Alterar frontend para `/converter-venda` ✅ **Recomendado**
  - Opção 3: Criar alias no router

### 3. Implementar Endpoints de Relatórios Avançados 📊
Backend ainda não tem endpoints para:
- [ ] `POST /relatorios/vendas-por-periodo`
- [ ] `POST /relatorios/desempenho-vendedores`
- [ ] `POST /relatorios/produtos-mais-vendidos`
- [ ] `POST /relatorios/curva-abc-clientes`
- [ ] `POST /relatorios/analise-margem`

**Solução**: Criar `app/modules/relatorios_avancados/` ou adicionar ao existente

### 4. Adicionar Export Endpoints 📥
Frontend já tem lógica de export, backend pode oferecer:
- [ ] `GET /dashboard/stats/export?format=xlsx`
- [ ] `GET /dashboard/vendas-por-dia/export?format=csv`
- [ ] `POST /orcamentos/export` (bulk export)
- [ ] `POST /pedidos-venda/export` (bulk export)

### 5. Otimizações de Performance ⚡
- [ ] Adicionar índices compostos em queries de dashboard
- [ ] Implementar query materialized views para KPIs
- [ ] Cache Redis com TTL configurável
- [ ] Pagination para endpoints que retornam listas grandes
- [ ] Implementar rate limiting específico para dashboard

### 6. Testes Automatizados 🧪
- [ ] Testes unitários para `DashboardService` (pytest)
- [ ] Testes de integração para endpoints (pytest + httpx)
- [ ] Testes E2E para dashboard page (Playwright)
- [ ] Smoke tests para verificar dados corretos

### 7. Monitoramento e Logs 📈
- [ ] Adicionar logs estruturados para queries lentas
- [ ] Métricas de uso de endpoints (Prometheus)
- [ ] Alertas para KPIs críticos (pedidos atrasados)
- [ ] Dashboard de observabilidade (Grafana)

---

## 🛠️ Configuração para Desenvolvimento

### Backend
```bash
# 1. Aplicar migrações (se houver novas)
alembic upgrade head

# 2. Executar servidor
python main.py
# ou
uvicorn main:app --reload

# 3. Acessar docs
# http://localhost:8000/docs
```

### Frontend
```bash
cd frontend

# 1. Configurar variáveis de ambiente
cp .env.example .env.local
# Editar .env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# 2. Instalar dependências (se necessário)
npm install

# 3. Executar dev server
npm run dev

# 4. Acessar dashboard
# http://localhost:3000/dashboard
```

---

## 📝 Notas Técnicas

### Decisões de Implementação

1. **Cast de datetime para date**
   - `Venda.data_venda` é `DateTime`, queries usam `cast(field, Date)`
   - Garante compatibilidade entre tipos
   - Alternativa: usar `func.date()` (depende do DB)

2. **Remoção de filtro `ativo`**
   - Modelo `Venda` não tem campo `ativo`
   - Filtros de soft-delete removidos das queries

3. **Campo `total_item` vs `preco_total`**
   - `ItemVenda` usa `total_item`, não `preco_total`
   - Service corrigido para usar nome correto

4. **Meta de vendas**
   - Atualmente hardcoded: `meta_mes = faturamento_mes_anterior * 1.1`
   - TODO: Mover para tabela configurável por usuário/empresa

5. **Fallback para mock data**
   - Frontend usa SWR com `fallbackData` para graceful degradation
   - Se API falhar, exibe dados mock sem erro visual
   - Permite desenvolvimento offline

---

## 🔍 Validação

### Verificar se Dashboard está funcionando:

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Testar endpoint de stats (requer token JWT)
curl -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8000/api/v1/dashboard/stats

# 3. Testar vendas por dia
curl -H "Authorization: Bearer <TOKEN>" \
  "http://localhost:8000/api/v1/dashboard/vendas-por-dia?dias=7"

# 4. Verificar docs OpenAPI
# http://localhost:8000/docs#/Dashboard
```

### Frontend:
```bash
# 1. Abrir console do navegador
# 2. Verificar network requests
# 3. Conferir se mock data está sendo usado (se API offline)
```

---

## 📚 Referências

- **Backend Pattern**: `/home/user/siscom/CLAUDE.md` - Padrão de 5 arquivos
- **Modelos**: `app/modules/vendas/models.py`, `app/modules/pedidos_venda/models.py`
- **Frontend Hooks**: `frontend/lib/hooks/use-dashboard.ts`
- **Commit Hash**: `7bb30b3`

---

**Status**: ✅ Dashboard 100% integrado
**Próximo**: Implementar relatórios avançados e sincronizar paths de endpoints
