# Integração Mercado Pago - Documentação

## Visão Geral

Integração completa com a API do Mercado Pago para processar pagamentos PIX, criar checkouts e receber notificações via webhook.

## Configuração

### Variáveis de Ambiente

Adicione no arquivo `.env`:

```bash
# Mercado Pago - Credenciais de Teste
MERCADOPAGO_ACCESS_TOKEN=TEST-127924860584293-111909-8eb99a40f34eb5ba5c03fa2979196258-184641661
MERCADOPAGO_PUBLIC_KEY=TEST-040da26c-318d-46ff-b42e-4ef22fbf755f

# Mercado Pago - Credenciais de Produção (quando disponível)
# MERCADOPAGO_ACCESS_TOKEN=APP_USR-seu-access-token-producao
# MERCADOPAGO_PUBLIC_KEY=APP_USR-sua-public-key-producao
```

### URL Base da API

- **Teste/Produção**: `https://api.mercadopago.com`

## Endpoints Disponíveis

Todos os endpoints estão sob o prefixo `/api/v1/integrations/mercadopago`

### 1. Criar Pagamento PIX

**POST** `/api/v1/integrations/mercadopago/pix`

Cria um pagamento PIX e retorna QR Code para pagamento instantâneo.

**Headers:**
```
Authorization: Bearer {seu-jwt-token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "valor": 150.00,
  "descricao": "Venda #1234 - Material de Construção",
  "email_pagador": "cliente@email.com",
  "external_reference": "VENDA-1234"
}
```

**Response (201 Created):**
```json
{
  "id": 123456789,
  "status": "pending",
  "qr_code": "00020126580014br.gov.bcb.pix...",
  "qr_code_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "ticket_url": "https://www.mercadopago.com.br/payments/123456789/ticket",
  "transaction_id": 123456789,
  "valor": 150.00,
  "data_criacao": "2025-11-19T10:30:00Z",
  "external_reference": "VENDA-1234"
}
```

**Exemplo de Uso:**
```bash
curl -X POST "http://localhost:8000/api/v1/integrations/mercadopago/pix" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "valor": 150.00,
    "descricao": "Venda #1234",
    "email_pagador": "cliente@email.com",
    "external_reference": "VENDA-1234"
  }'
```

### 2. Consultar Pagamento

**GET** `/api/v1/integrations/mercadopago/pagamento/{payment_id}`

Consulta o status atual de um pagamento no Mercado Pago.

**Headers:**
```
Authorization: Bearer {seu-jwt-token}
```

**Response (200 OK):**
```json
{
  "id": 123456789,
  "status": "approved",
  "status_detail": "accredited",
  "valor": 150.00,
  "data_criacao": "2025-11-19T10:30:00Z",
  "data_aprovacao": "2025-11-19T10:31:23Z",
  "metodo_pagamento": "pix",
  "external_reference": "VENDA-1234"
}
```

**Status Possíveis:**
- `pending`: Pagamento pendente
- `approved`: Pagamento aprovado
- `rejected`: Pagamento rejeitado
- `cancelled`: Pagamento cancelado
- `refunded`: Pagamento reembolsado
- `in_process`: Em processamento

**Exemplo de Uso:**
```bash
curl -X GET "http://localhost:8000/api/v1/integrations/mercadopago/pagamento/123456789" \
  -H "Authorization: Bearer eyJhbGc..."
```

### 3. Cancelar Pagamento

**DELETE** `/api/v1/integrations/mercadopago/pagamento/{payment_id}`

Cancela um pagamento pendente no Mercado Pago.

**Headers:**
```
Authorization: Bearer {seu-jwt-token}
```

**Response (200 OK):**
```json
{
  "sucesso": true,
  "status": "cancelled"
}
```

**Exemplo de Uso:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/integrations/mercadopago/pagamento/123456789" \
  -H "Authorization: Bearer eyJhbGc..."
```

### 4. Webhook (Notificações)

**POST** `/api/v1/integrations/mercadopago/webhook`

Endpoint para receber notificações do Mercado Pago quando há alterações em pagamentos.

**⚠️ IMPORTANTE:** Este endpoint NÃO requer autenticação (é chamado pelo sistema do Mercado Pago).

**Request Body (exemplo):**
```json
{
  "id": 123456,
  "live_mode": false,
  "type": "payment",
  "date_created": "2025-11-19T10:31:23Z",
  "user_id": "184641661",
  "api_version": "v1",
  "action": "payment.updated",
  "data": {
    "id": "123456789"
  }
}
```

**Response (200 OK):**
```json
{
  "sucesso": true
}
```

**Configuração no Mercado Pago:**

1. Acesse: https://www.mercadopago.com.br/developers/panel/webhooks
2. Configure a URL do webhook:
   ```
   https://seu-dominio.com/api/v1/integrations/mercadopago/webhook
   ```
3. Selecione os eventos:
   - `payment` (Pagamentos)
   - `merchant_order` (Ordens de compra)

### 5. Criar Preferência de Checkout

**POST** `/api/v1/integrations/mercadopago/checkout/preferencia`

Cria uma preferência de checkout (Checkout Pro) e retorna URL para redirecionar o cliente.

**Headers:**
```
Authorization: Bearer {seu-jwt-token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "items": [
    {
      "title": "Cimento CP-II 50kg",
      "quantity": 10,
      "unit_price": 35.90,
      "currency_id": "BRL"
    },
    {
      "title": "Areia Média (m³)",
      "quantity": 2,
      "unit_price": 80.00,
      "currency_id": "BRL"
    }
  ],
  "external_reference": "VENDA-5678",
  "notification_url": "https://seu-dominio.com/api/v1/integrations/mercadopago/webhook"
}
```

**Response (200 OK):**
```json
{
  "id": "987654321",
  "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=987654321",
  "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id=987654321"
}
```

**Exemplo de Uso:**
```bash
curl -X POST "http://localhost:8000/api/v1/integrations/mercadopago/checkout/preferencia" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "title": "Produto X",
        "quantity": 1,
        "unit_price": 100.00,
        "currency_id": "BRL"
      }
    ],
    "external_reference": "VENDA-5678"
  }'
```

### 6. Health Check

**GET** `/api/v1/integrations/mercadopago/health`

Verifica se a integração com Mercado Pago está funcionando.

**Response (200 OK):**
```json
{
  "status": "ok",
  "mercadopago": "conectado",
  "ambiente": "teste"
}
```

**Exemplo de Uso:**
```bash
curl -X GET "http://localhost:8000/api/v1/integrations/mercadopago/health"
```

## Fluxo de Pagamento PIX

```
1. Cliente seleciona produtos e finaliza compra
   ↓
2. Sistema cria pagamento PIX via POST /mercadopago/pix
   ↓
3. Mercado Pago retorna QR Code
   ↓
4. Cliente escaneia QR Code e paga via app do banco
   ↓
5. Mercado Pago notifica via webhook quando pagamento é aprovado
   ↓
6. Sistema processa webhook e atualiza status da venda
   ↓
7. Cliente recebe confirmação
```

## Integração com Sistema Interno

### Salvar Transação PIX no Banco de Dados

Após criar o pagamento, salve no banco de dados local:

```python
from app.modules.pagamentos.models import TransacaoPix, StatusPagamento

# Criar pagamento no Mercado Pago
mp_client = get_mp_client()
resultado = await mp_client.criar_pagamento_pix(
    valor=valor,
    descricao=descricao,
    email_pagador=email_pagador,
    external_reference=f"VENDA-{venda_id}"
)

# Salvar no banco de dados local
transacao = TransacaoPix(
    chave_pix_id=chave_pix_id,
    venda_id=venda_id,
    cliente_id=cliente_id,
    valor=valor,
    descricao=descricao,
    txid=str(resultado['id']),  # ID do Mercado Pago
    integration_id=resultado['id'],  # Para consultas futuras
    integration_provider="mercadopago",
    qr_code_texto=resultado['qr_code'],
    qr_code_base64=resultado['qr_code_base64'],
    status=StatusPagamento.PENDENTE,
    data_criacao=datetime.utcnow()
)
db.add(transacao)
await db.commit()
```

### Processar Webhook

Quando o webhook for chamado, atualize o status no banco de dados:

```python
# No endpoint do webhook
webhook_data = await request.json()

# Processar dados do webhook
mp_client = get_mp_client()
dados_processados = await mp_client.processar_webhook(webhook_data)

# Buscar transação no banco de dados
payment_id = dados_processados['id']
transacao = await db.query(TransacaoPix).filter(
    TransacaoPix.integration_id == payment_id
).first()

if transacao:
    # Atualizar status
    transacao.status = converter_status_mp(dados_processados['status'])

    if dados_processados['status'] == 'approved':
        transacao.data_aprovacao = datetime.utcnow()

        # Atualizar status da venda
        venda = await db.get(Venda, transacao.venda_id)
        venda.status_pagamento = StatusPagamento.APROVADO

    await db.commit()
```

## Testes

### Credenciais de Teste

Use as credenciais fornecidas no `.env` para testes:
- **Access Token**: `TEST-127924860584293-111909-8eb99a40f34eb5ba5c03fa2979196258-184641661`
- **Public Key**: `TEST-040da26c-318d-46ff-b42e-4ef22fbf755f`

### Cartões de Teste

Para testar checkout (cartão de crédito):

| Cartão           | Número              | CVV | Validade |
|------------------|---------------------|-----|----------|
| Mastercard       | 5031 4332 1540 6351 | 123 | 11/25    |
| Visa             | 4235 6477 2802 5682 | 123 | 11/25    |
| American Express | 3753 651535 56885   | 1234| 11/25    |

**Status do pagamento:**
- **APRO** (Aprovado): Usar `APRO` como nome do titular
- **CONT** (Pendente): Usar `CONT` como nome do titular
- **OTHE** (Rejeitado): Usar `OTHE` como nome do titular

### PIX de Teste

No ambiente de teste, o QR Code gerado é válido, mas o pagamento não será processado automaticamente. Para simular aprovação:

1. Crie o pagamento PIX
2. Acesse o painel de desenvolvedor do Mercado Pago
3. Aprove manualmente o pagamento de teste
4. O webhook será chamado automaticamente

## Segurança

### Validação de Webhook

O Mercado Pago envia um header `x-signature` para validar a autenticidade do webhook:

```python
import hmac
import hashlib

def validar_webhook_mp(x_signature: str, x_request_id: str, data: dict) -> bool:
    """Valida assinatura do webhook do Mercado Pago"""
    secret = settings.MERCADOPAGO_WEBHOOK_SECRET  # Obter no painel MP

    # Criar string para assinar
    template = f"id:{data['data']['id']};request-id:{x_request_id};ts:{data['date_created']};"

    # Calcular HMAC SHA256
    hmac_sha256 = hmac.new(
        secret.encode(),
        template.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac_sha256 == x_signature
```

### Rate Limiting

Os endpoints possuem rate limiting configurado no sistema:
- **Autenticados**: 100 requisições/minuto
- **Webhook** (não autenticado): 60 requisições/minuto

## Logs e Monitoramento

Todos os eventos são logados com níveis apropriados:

```python
# Sucesso
logger.info(f"Pagamento PIX criado - ID: {payment_id}, Valor: {valor}")

# Erro
logger.error(f"Erro ao criar pagamento PIX: {str(e)}")

# Webhook
logger.info(f"Webhook processado - Payment ID: {payment_id}, Status: {status}")
```

## Documentação Oficial

- **API Reference**: https://documenter.getpostman.com/view/15366798/2sAXjKasp4
- **Developers Panel**: https://www.mercadopago.com.br/developers
- **Webhooks**: https://www.mercadopago.com.br/developers/panel/webhooks
- **Credenciais**: https://www.mercadopago.com.br/developers/panel/credentials

## Próximos Passos

1. ✅ Implementar client Mercado Pago (`mercadopago.py`)
2. ✅ Criar endpoints REST (`mercadopago_router.py`)
3. ✅ Integrar com `main.py`
4. ⏳ Criar testes automatizados (`test_mercadopago.py`)
5. ⏳ Implementar persistência em banco de dados
6. ⏳ Implementar processamento de webhooks completo
7. ⏳ Adicionar validação de assinatura de webhooks
8. ⏳ Configurar webhooks no painel do Mercado Pago
9. ⏳ Migrar para credenciais de produção

## Suporte

Para dúvidas ou problemas:
- Documentação da API: https://documenter.getpostman.com/view/15366798/2sAXjKasp4
- Suporte Mercado Pago: https://www.mercadopago.com.br/developers/support
