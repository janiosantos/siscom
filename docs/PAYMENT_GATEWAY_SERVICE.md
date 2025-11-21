# Payment Gateway Service - Guia de Uso

## 📋 Visão Geral

O **Payment Gateway Service** é um serviço unificado que abstrai a complexidade de múltiplos gateways de pagamento em uma interface única e consistente.

### Gateways Suportados
- ✅ **Cielo** - Cartão de crédito e débito
- ✅ **GetNet** (Santander) - Cartão de crédito, débito e PIX
- ✅ **Mercado Pago** - PIX e cartão de crédito

### Métodos de Pagamento
- 💳 **Cartão de Crédito** (com parcelamento até 12x)
- 💳 **Cartão de Débito**
- 🔑 **PIX** (QR Code)

---

## 🚀 Quick Start

### 1. Inicializar o Serviço

```python
from app.services.payment_gateway_service import (
    PaymentGatewayService,
    PaymentGateway,
    PaymentMethod
)
from decimal import Decimal

# Inicializa o serviço
service = PaymentGatewayService()

# Configura MercadoPago (obrigatório para usar MP)
service.initialize_mercadopago(
    access_token="SEU_ACCESS_TOKEN",
    public_key="SEU_PUBLIC_KEY"
)
```

### 2. Criar Pagamento com Cartão de Crédito

```python
# Pagamento parcelado com Cielo
result = await service.create_payment(
    gateway=PaymentGateway.CIELO,
    payment_method=PaymentMethod.CREDIT_CARD,
    amount=Decimal("1500.00"),
    order_id="VENDA-12345",
    customer_data={
        "name": "João Silva",
        "email": "joao@email.com"
    },
    card_data={
        "number": "4532000000000000",
        "holder": "JOAO SILVA",
        "expiration": "12/2028",
        "cvv": "123",
        "brand": "Visa"
    },
    installments=6,  # 6 parcelas
    capture=True     # Captura imediata
)

print(f"Pagamento criado: {result['payment_id']}")
print(f"Status: {result['status']}")
print(f"Gateway: {result['gateway']}")
```

### 3. Criar Pagamento PIX

```python
# PIX com GetNet
result = await service.create_payment(
    gateway=PaymentGateway.GETNET,
    payment_method=PaymentMethod.PIX,
    amount=Decimal("250.50"),
    order_id="VENDA-12346",
    customer_data={
        "name": "Maria Santos",
        "cpf": "12345678900",
        "email": "maria@email.com"
    }
)

# QR Code PIX
print(f"QR Code: {result['pix_qrcode']}")
print(f"Status: {result['status']}")  # pending
```

### 4. Consultar Pagamento

```python
# Consulta em qualquer gateway
result = await service.query_payment(
    gateway=PaymentGateway.CIELO,
    payment_id="abc-123-def-456"
)

print(f"Status atual: {result['status']}")
print(f"Valor: R$ {result['amount']:.2f}")
```

---

## 📚 API Completa

### create_payment()

Cria um novo pagamento em qualquer gateway.

**Parâmetros:**
```python
gateway: PaymentGateway          # CIELO, GETNET ou MERCADOPAGO
payment_method: PaymentMethod    # CREDIT_CARD, DEBIT_CARD ou PIX
amount: Decimal                  # Valor do pagamento
order_id: str                    # ID do pedido/venda
customer_data: Dict              # Dados do cliente
card_data: Optional[Dict]        # Dados do cartão (se aplicável)
installments: int = 1            # Número de parcelas (1-12)
capture: bool = True             # Auto-captura (default: True)
metadata: Optional[Dict] = None  # Metadados adicionais
```

**customer_data:**
```python
{
    "name": str,         # Nome do cliente
    "email": str,        # Email (obrigatório para MP)
    "cpf": str,          # CPF (obrigatório para GetNet)
    "phone": str         # Telefone (opcional)
}
```

**card_data (para pagamentos com cartão):**
```python
{
    "number": str,       # Número do cartão
    "holder": str,       # Nome do titular
    "expiration": str,   # MM/YYYY
    "cvv": str,          # Código de segurança
    "brand": str         # Visa, Master, Elo, etc
}
```

**Retorno Normalizado:**
```python
{
    "gateway": "cielo",
    "payment_id": "abc123",           # ID do pagamento no gateway
    "transaction_id": "xyz789",       # ID da transação
    "status": "captured",             # Status normalizado
    "amount": 150.00,                 # Valor em reais
    "installments": 3,                # Número de parcelas
    "captured": True,                 # Se foi capturado
    "authorization_code": "AUTH123",  # Código de autorização
    "pix_qrcode": "...",             # QR Code PIX (se aplicável)
    "created_at": "2025-11-21T12:00:00",
    "raw_response": {...}            # Resposta original do gateway
}
```

### capture_payment()

Captura um pagamento pré-autorizado.

```python
result = await service.capture_payment(
    gateway=PaymentGateway.CIELO,
    payment_id="abc-123",
    amount=Decimal("100.00")  # None = captura total
)
```

### cancel_payment()

Cancela/estorna um pagamento.

```python
result = await service.cancel_payment(
    gateway=PaymentGateway.GETNET,
    payment_id="xyz-456",
    amount=Decimal("50.00")  # None = cancelamento total
)
```

### query_payment()

Consulta status de um pagamento.

```python
result = await service.query_payment(
    gateway=PaymentGateway.MERCADOPAGO,
    payment_id="789"
)
```

---

## 🎯 Status de Pagamento

O serviço normaliza os status de todos os gateways:

| Status | Descrição | Gateways |
|--------|-----------|----------|
| **PENDING** | Aguardando pagamento | Todos (PIX) |
| **AUTHORIZED** | Pré-autorizado | Cielo, GetNet |
| **CAPTURED** | Capturado/Aprovado | Todos |
| **DENIED** | Negado | Todos |
| **CANCELLED** | Cancelado | Todos |
| **REFUNDED** | Estornado | Todos |

---

## 🔍 Exemplos Práticos

### Fluxo Completo com Pré-Autorização

```python
# 1. Cria pagamento com pré-autorização
payment = await service.create_payment(
    gateway=PaymentGateway.CIELO,
    payment_method=PaymentMethod.CREDIT_CARD,
    amount=Decimal("500.00"),
    order_id="VENDA-001",
    customer_data={"name": "Cliente"},
    card_data={...},
    capture=False  # Pré-autorização (não captura)
)

assert payment["status"] == PaymentStatus.AUTHORIZED

# 2. Verifica estoque, validações, etc...
# ...

# 3. Captura o pagamento
captured = await service.capture_payment(
    gateway=PaymentGateway.CIELO,
    payment_id=payment["payment_id"],
    amount=Decimal("500.00")
)

assert captured["status"] == PaymentStatus.CAPTURED
```

### Fallback entre Gateways

```python
gateways = [
    PaymentGateway.CIELO,
    PaymentGateway.GETNET,
    PaymentGateway.MERCADOPAGO
]

for gateway in gateways:
    try:
        result = await service.create_payment(
            gateway=gateway,
            payment_method=PaymentMethod.CREDIT_CARD,
            amount=Decimal("100.00"),
            order_id="VENDA-002",
            customer_data={"name": "Cliente", "cpf": "12345678900"},
            card_data={...}
        )

        if result["status"] in [PaymentStatus.AUTHORIZED, PaymentStatus.CAPTURED]:
            print(f"✅ Pagamento aprovado no {gateway.value}")
            break

    except Exception as e:
        print(f"❌ Falha no {gateway.value}: {e}")
        continue
```

### Processamento de PIX com Webhook

```python
# 1. Cria pagamento PIX
pix = await service.create_payment(
    gateway=PaymentGateway.GETNET,
    payment_method=PaymentMethod.PIX,
    amount=Decimal("350.00"),
    order_id="VENDA-003",
    customer_data={
        "name": "Cliente",
        "cpf": "12345678900"
    }
)

# 2. Exibe QR Code para cliente
qr_code = pix["pix_qrcode"]
print(f"Escaneie o QR Code: {qr_code}")

# 3. Webhook do gateway notifica quando pago
# (implementar endpoint de webhook que chama):
payment_status = await service.query_payment(
    gateway=PaymentGateway.GETNET,
    payment_id=pix["payment_id"]
)

if payment_status["status"] == PaymentStatus.CAPTURED:
    print("✅ PIX confirmado!")
```

---

## ⚠️ Validações e Regras

### Validações Automáticas

```python
# ❌ Valor mínimo: R$ 0,01
BusinessRuleException: "Valor mínimo de pagamento é R$ 0,01"

# ❌ Parcelas: 1 a 12
BusinessRuleException: "Número de parcelas deve estar entre 1 e 12"

# ❌ Dados do cartão obrigatórios
BusinessRuleException: "Dados do cartão são obrigatórios"

# ❌ Gateway não inicializado
BusinessRuleException: "MercadoPago não inicializado"
```

### Compatibilidade de Métodos

| Gateway | Crédito | Débito | PIX |
|---------|---------|--------|-----|
| Cielo | ✅ | ✅ | ❌ |
| GetNet | ✅ | ✅ | ✅ |
| Mercado Pago | ✅ | ❌ | ✅ |

---

## 🧪 Testes

### Mock para Testes

```python
from tests.mocks.payment_gateway_mock import PaymentGatewayMock

# Cria mock
mock = PaymentGatewayMock()

# Simula pagamento
response = mock.cielo_create_card_payment(
    amount=100.00,
    installments=3
)

# Usa em testes com patch
from unittest.mock import patch, AsyncMock

with patch.object(service.cielo, 'create_credit_card_payment',
                  new_callable=AsyncMock, return_value=response):
    result = await service.create_payment(...)
```

### Executar Testes

```bash
# Todos os testes de integração
pytest tests/test_payment_gateway_integration.py -v

# Testes específicos por gateway
pytest tests/test_payment_gateway_integration.py::TestCieloIntegration -v
pytest tests/test_payment_gateway_integration.py::TestGetNetIntegration -v
pytest tests/test_payment_gateway_integration.py::TestMercadoPagoIntegration -v
```

---

## 📊 Comparação de Gateways

### Cielo
- ✅ Maior aceitação no Brasil
- ✅ Suporte a múltiplas bandeiras
- ✅ Pré-autorização e captura posterior
- ❌ Sem PIX nativo
- 💰 Taxa: ~2,5% a 3,5%

### GetNet (Santander)
- ✅ Cartão + PIX integrado
- ✅ Boas taxas para clientes Santander
- ✅ OAuth2 seguro
- ⚡ Boa performance
- 💰 Taxa: ~2% a 3%

### Mercado Pago
- ✅ PIX instantâneo
- ✅ Checkout transparente
- ✅ Split de pagamento
- ✅ Marketplace integrado
- 💰 Taxa: ~3,5% a 5%

---

## 🔐 Segurança

### Boas Práticas

1. **Nunca armazene dados de cartão completos**
   ```python
   # ❌ ERRADO
   user.card_number = "4532000000000000"

   # ✅ CORRETO
   user.card_token = "TOKENIZED_CARD_ABC123"
   ```

2. **Use tokenização**
   ```python
   # Tokeniza cartão antes de salvar
   token = await service.cielo.tokenize_card(
       card_number="4532000000000000",
       card_holder="CLIENTE",
       card_expiration="12/2028"
   )
   ```

3. **Valide webhooks**
   ```python
   # Verifique assinatura do webhook
   signature = request.headers.get("X-Signature")
   if not verify_webhook_signature(payload, signature):
       raise Unauthorized()
   ```

4. **Use HTTPS**
   - Todos os gateways exigem HTTPS em produção

---

## 🚀 Deploy

### Variáveis de Ambiente

```bash
# Cielo
CIELO_MERCHANT_ID=your_merchant_id
CIELO_MERCHANT_KEY=your_merchant_key

# GetNet
GETNET_SELLER_ID=your_seller_id
GETNET_CLIENT_ID=your_client_id
GETNET_CLIENT_SECRET=your_client_secret

# Mercado Pago
MERCADOPAGO_ACCESS_TOKEN=your_access_token
MERCADOPAGO_PUBLIC_KEY=your_public_key
```

### Ambientes

```python
from app.integrations.cielo import CieloEnvironment
from app.integrations.getnet import GetNetEnvironment

# Desenvolvimento
service.cielo = CieloClient(environment=CieloEnvironment.SANDBOX)
service.getnet = GetNetClient(environment=GetNetEnvironment.SANDBOX)

# Produção
service.cielo = CieloClient(environment=CieloEnvironment.PRODUCTION)
service.getnet = GetNetClient(environment=GetNetEnvironment.PRODUCTION)
```

---

## 📞 Suporte

### Logs

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

# Logs automáticos do serviço
logger.info("Criando pagamento", extra={
    "gateway": "cielo",
    "order_id": "VENDA-123",
    "amount": 100.00
})
```

### Debugging

```python
# Ativa modo debug
import logging
logging.getLogger("app.services.payment_gateway_service").setLevel(logging.DEBUG)

# Vê resposta bruta do gateway
result = await service.create_payment(...)
print(result["raw_response"])
```

---

## 🎓 Recursos Adicionais

- [Documentação Cielo API 3.0](https://developercielo.github.io/manual/cielo-ecommerce)
- [Documentação GetNet](https://developers.getnet.com.br/api)
- [Documentação Mercado Pago](https://www.mercadopago.com.br/developers)

---

**Última atualização**: 2025-11-21
**Versão**: 1.0.0
**Autor**: ERP Materiais de Construção
