# Payment Gateway Mock Service

Microserviço que simula **Cielo**, **GetNet** e **Mercado Pago** para testes de integração do ERP.

## 🚀 Quick Start

### Opção 1: Docker (Recomendado)

```bash
# Build e executar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar
docker-compose down
```

### Opção 2: Python Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
python -m app.main

# Ou com uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 📡 Endpoints

**Base URL**: `http://localhost:8001`

### Documentação Interativa
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Health Check
```bash
curl http://localhost:8001/health
```

## 🎯 APIs Disponíveis

### Cielo

**Base Path**: `/cielo`

```bash
# Criar venda com cartão de crédito
curl -X POST http://localhost:8001/cielo/1/sales \
  -H "Content-Type: application/json" \
  -H "MerchantId: your-merchant-id" \
  -H "MerchantKey: your-merchant-key" \
  -d '{
    "MerchantOrderId": "ORDER-001",
    "Payment": {
      "Type": "CreditCard",
      "Amount": 15000,
      "Installments": 3,
      "Capture": true,
      "CreditCard": {
        "CardNumber": "4532000000000000",
        "Holder": "JOÃO SILVA",
        "ExpirationDate": "12/2028",
        "SecurityCode": "123",
        "Brand": "Visa"
      }
    }
  }'

# Consultar pagamento
curl http://localhost:8001/cielo/1/sales/{payment_id}

# Capturar pré-autorização
curl -X PUT http://localhost:8001/cielo/1/sales/{payment_id}/capture

# Cancelar/estornar
curl -X PUT http://localhost:8001/cielo/1/sales/{payment_id}/void

# Tokenizar cartão
curl -X POST http://localhost:8001/cielo/1/card \
  -H "Content-Type: application/json" \
  -d '{
    "CustomerName": "CLIENTE",
    "CardNumber": "4532000000000000",
    "Holder": "CLIENTE",
    "ExpirationDate": "122028",
    "Brand": "Visa"
  }'
```

### GetNet

**Base Path**: `/getnet`

```bash
# OAuth2 Token
curl -X POST http://localhost:8001/getnet/auth/oauth/v2/token \
  -d "client_id=your-client-id" \
  -d "client_secret=your-secret" \
  -d "scope=oob"

# Pagamento com cartão de crédito
curl -X POST http://localhost:8001/getnet/v1/payments/credit \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "seller_id": "SELLER-001",
    "amount": 15000,
    "currency": "BRL",
    "order": {
      "order_id": "ORDER-001",
      "sales_tax": 0,
      "product_type": "service"
    }
  }'

# Pagamento PIX
curl -X POST http://localhost:8001/getnet/v1/payments/pix \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "seller_id": "SELLER-001",
    "amount": 15000,
    "currency": "BRL",
    "order": {
      "order_id": "ORDER-PIX-001"
    }
  }'

# Consultar pagamento
curl http://localhost:8001/getnet/v1/payments/{payment_id}

# Cancelar
curl -X POST http://localhost:8001/getnet/v1/payments/credit/{payment_id}/cancel

# Tokenizar cartão
curl -X POST http://localhost:8001/getnet/v1/tokens/card \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "card_number": "5555444433332222",
    "customer_id": "CUSTOMER-001"
  }'
```

### Mercado Pago

**Base Path**: `/mercadopago`

```bash
# Criar pagamento PIX
curl -X POST http://localhost:8001/mercadopago/v1/payments \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_amount": 150.00,
    "description": "Venda ERP",
    "payment_method_id": "pix",
    "payer": {
      "email": "cliente@email.com"
    },
    "external_reference": "ORDER-001"
  }'

# Criar pagamento com cartão
curl -X POST http://localhost:8001/mercadopago/v1/payments \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_amount": 150.00,
    "description": "Venda ERP",
    "payment_method_id": "visa",
    "installments": 3,
    "payer": {
      "email": "cliente@email.com"
    }
  }'

# Consultar pagamento
curl http://localhost:8001/mercadopago/v1/payments/{payment_id}

# Cancelar
curl -X PUT http://localhost:8001/mercadopago/v1/payments/{payment_id} \
  -H "Content-Type: application/json" \
  -d '{"status": "cancelled"}'

# Estornar
curl -X POST http://localhost:8001/mercadopago/v1/payments/{payment_id}/refunds
```

## 🛠️ Endpoints Administrativos

**Base Path**: `/admin`

### Estatísticas

```bash
# Estatísticas gerais
curl http://localhost:8001/admin/stats

# Listar transações
curl http://localhost:8001/admin/transactions

# Filtrar por gateway
curl http://localhost:8001/admin/transactions?gateway=cielo

# Filtrar por status
curl http://localhost:8001/admin/transactions?status=captured

# Detalhes de transação
curl http://localhost:8001/admin/transactions/{transaction_id}
```

### Controles

```bash
# Aprovar PIX manualmente (simula pagamento do cliente)
curl -X POST http://localhost:8001/admin/transactions/{pix_payment_id}/approve

# Configurar taxa de aprovação (0.0 a 1.0)
curl -X POST "http://localhost:8001/admin/config/approval-rate?rate=1.0"

# Limpar todas as transações
curl -X DELETE http://localhost:8001/admin/transactions
```

## 📊 Comportamento do Mock

### Taxa de Aprovação

Por padrão, **90%** dos pagamentos são aprovados automaticamente.

Você pode mudar essa taxa via API admin:

```bash
# 100% de aprovação
curl -X POST "http://localhost:8001/admin/config/approval-rate?rate=1.0"

# 50% de aprovação
curl -X POST "http://localhost:8001/admin/config/approval-rate?rate=0.5"

# 0% de aprovação (todos negados)
curl -X POST "http://localhost:8001/admin/config/approval-rate?rate=0.0"
```

### PIX

- Sempre retorna **PENDING** inicialmente
- Use `/admin/transactions/{id}/approve` para aprovar manualmente
- Gera QR Code simulado (base64)

### Cartão de Crédito/Débito

- 90% de aprovação (configurável)
- Gera IDs únicos realistas
- Suporta pré-autorização e captura posterior
- Tokenização funcional

## 🧪 Usando com o ERP

### 1. Configurar URLs

No `.env` do ERP, aponte para o mock:

```bash
# Cielo
CIELO_API_URL=http://localhost:8001/cielo
CIELO_MERCHANT_ID=mock-merchant
CIELO_MERCHANT_KEY=mock-key

# GetNet
GETNET_API_URL=http://localhost:8001/getnet
GETNET_CLIENT_ID=mock-client
GETNET_CLIENT_SECRET=mock-secret

# Mercado Pago
MERCADOPAGO_API_URL=http://localhost:8001/mercadopago
MERCADOPAGO_ACCESS_TOKEN=mock-token
```

### 2. Executar Mock

```bash
docker-compose up -d
```

### 3. Executar Testes do ERP

```bash
cd ../siscom
pytest tests/test_payment*.py -v
```

## 📝 Exemplos de Integração

### Python com requests

```python
import requests

# Cielo
response = requests.post(
    "http://localhost:8001/cielo/1/sales",
    headers={
        "MerchantId": "mock-id",
        "MerchantKey": "mock-key",
        "Content-Type": "application/json"
    },
    json={
        "MerchantOrderId": "ORDER-001",
        "Payment": {
            "Type": "CreditCard",
            "Amount": 15000,
            "Installments": 3,
            "Capture": True,
            "CreditCard": {
                "CardNumber": "4532000000000000",
                "Holder": "TESTE",
                "ExpirationDate": "12/2028",
                "Brand": "Visa"
            }
        }
    }
)

print(response.json())
```

### Com o PaymentGatewayService do ERP

```python
from app.services.payment_gateway_service import (
    PaymentGatewayService,
    PaymentGateway,
    PaymentMethod
)
from decimal import Decimal

# Configurar para usar mock (via env vars)
service = PaymentGatewayService()

# Criar pagamento
result = await service.create_payment(
    gateway=PaymentGateway.CIELO,
    payment_method=PaymentMethod.CREDIT_CARD,
    amount=Decimal("150.00"),
    order_id="ORDER-001",
    customer_data={"name": "Cliente Teste"},
    card_data={
        "number": "4532000000000000",
        "holder": "TESTE",
        "expiration": "12/2028",
        "brand": "Visa",
        "cvv": "123"
    }
)

print(result)
# {
#   "gateway": "cielo",
#   "payment_id": "uuid...",
#   "status": "captured",
#   ...
# }
```

## 🔍 Monitoramento

### Ver logs em tempo real

```bash
docker-compose logs -f
```

### Estatísticas

```bash
curl http://localhost:8001/admin/stats | jq
```

Saída exemplo:
```json
{
  "service": "payment-gateway-mock",
  "stats": {
    "total_transactions": 150,
    "approved": 135,
    "denied": 15,
    "cancelled": 2,
    "refunded": 1,
    "cielo_transactions": 50,
    "getnet_transactions": 60,
    "mercadopago_transactions": 40
  },
  "transactions_count": 150
}
```

## 🎛️ Variáveis de Ambiente

```bash
# Taxa de aprovação (0.0 a 1.0)
MOCK_APPROVAL_RATE=0.90

# Porta do serviço
MOCK_PORT=8001

# Log level
MOCK_LOG_LEVEL=INFO

# Delay nas respostas (ms)
MOCK_DELAY_MS=0
```

## 🐛 Troubleshooting

### Porta 8001 já em uso

```bash
# Mudar porta no docker-compose.yml
ports:
  - "8002:8001"  # Host:Container
```

### Limpar dados

```bash
curl -X DELETE http://localhost:8001/admin/transactions
```

### Reiniciar serviço

```bash
docker-compose restart
```

## 📚 Documentação

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health**: http://localhost:8001/health
- **Stats**: http://localhost:8001/admin/stats

## 🤝 Contribuindo

Este é um mock service interno para testes. Sugestões de melhorias:

1. Webhooks automáticos (notificações assíncronas)
2. Simulação de erros específicos
3. Delays configuráveis por gateway
4. Persistência em banco (SQLite)
5. Interface web de admin

## 📄 Licença

Interno - ERP SISCOM
