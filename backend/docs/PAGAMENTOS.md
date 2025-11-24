# Sistema de Pagamentos (PIX, Boleto, Conciliação)

## Visão Geral

Módulo completo para gestão de pagamentos no Brasil, incluindo:
- **PIX**: Integração com API BACEN ou Gateways (Mercado Pago, PagSeguro)
- **Boleto Bancário**: Geração, registro, CNAB 240/400
- **Conciliação Bancária**: Import OFX/CSV, matching automático

## Arquitetura

```
app/modules/pagamentos/
├── models.py          # Models SQLAlchemy
├── schemas.py         # Schemas Pydantic
├── services/
│   ├── pix_service.py         # Lógica PIX
│   ├── boleto_service.py      # Lógica Boleto
│   └── conciliacao_service.py # Lógica Conciliação
├── integrations/
│   ├── pix_bacen.py          # API BACEN PIX
│   ├── pix_mercadopago.py    # Mercado Pago PIX
│   ├── boleto_itau.py        # Boleto Itaú
│   ├── boleto_bradesco.py    # Boleto Bradesco
│   └── cnab/                 # CNAB 240/400
└── router.py          # Endpoints da API
```

## PIX

### Chaves PIX

#### Cadastrar Chave PIX

```bash
POST /api/v1/pagamentos/pix/chaves
Content-Type: application/json
Authorization: Bearer {token}

{
  "tipo": "email",
  "chave": "contato@empresa.com.br",
  "descricao": "Email principal",
  "banco": "Banco do Brasil",
  "agencia": "1234",
  "conta": "56789-0"
}
```

**Resposta:**
```json
{
  "id": 1,
  "tipo": "email",
  "chave": "contato@empresa.com.br",
  "descricao": "Email principal",
  "banco": "Banco do Brasil",
  "agencia": "1234",
  "conta": "56789-0",
  "ativa": true,
  "created_at": "2025-11-19T12:00:00Z"
}
```

#### Listar Chaves PIX

```bash
GET /api/v1/pagamentos/pix/chaves
```

### Transações PIX

#### Gerar Cobrança PIX

```bash
POST /api/v1/pagamentos/pix/cobrar
Content-Type: application/json

{
  "chave_pix_id": 1,
  "valor": 150.00,
  "descricao": "Pagamento Venda #123",
  "pagador_nome": "João Silva",
  "pagador_documento": "12345678901",
  "data_expiracao": "2025-11-20T23:59:59Z",
  "webhook_url": "https://meusite.com/webhooks/pix"
}
```

**Resposta:**
```json
{
  "id": 1,
  "txid": "ABC123XYZ456",
  "e2e_id": null,
  "valor": 150.00,
  "descricao": "Pagamento Venda #123",
  "status": "pendente",
  "data_criacao": "2025-11-19T12:00:00Z",
  "data_expiracao": "2025-11-20T23:59:59Z",
  "qr_code_texto": "00020126580014br.gov.bcb.pix...",
  "qr_code_imagem": "data:image/png;base64,iVBORw0KGg..."
}
```

#### Consultar Status

```bash
GET /api/v1/pagamentos/pix/transacoes/{txid}
```

#### Webhook de Confirmação

O sistema receberá webhooks quando um PIX for pago:

```bash
POST {webhook_url}
Content-Type: application/json

{
  "txid": "ABC123XYZ456",
  "e2e_id": "E12345678202511191200AbcD1234",
  "valor": 150.00,
  "pagador_nome": "João Silva",
  "pagador_documento": "12345678901",
  "data_pagamento": "2025-11-19T12:30:00Z"
}
```

### Integrações PIX

#### API BACEN (Direto)

Requer certificado digital e integração direta com BACEN.

```python
# app/modules/pagamentos/integrations/pix_bacen.py
from app.core.config import settings

class PixBacenClient:
    def __init__(self):
        self.cert_path = settings.PIX_CERT_PATH
        self.cert_password = settings.PIX_CERT_PASSWORD
        self.endpoint = settings.PIX_BACEN_ENDPOINT

    async def criar_cobranca(self, dados):
        # Implementação da integração BACEN
        pass
```

#### Mercado Pago

Mais simples, não requer certificado:

```python
# app/modules/pagamentos/integrations/pix_mercadopago.py
import mercadopago

class PixMercadoPagoClient:
    def __init__(self):
        self.sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

    async def criar_cobranca(self, valor, descricao):
        payment_data = {
            "transaction_amount": float(valor),
            "description": descricao,
            "payment_method_id": "pix",
            "payer": {...}
        }

        result = self.sdk.payment().create(payment_data)
        return result
```

## Boleto Bancário

### Configuração do Banco

#### Cadastrar Configuração

```bash
POST /api/v1/pagamentos/boletos/configuracoes
Content-Type: application/json

{
  "banco_codigo": "001",
  "banco_nome": "Banco do Brasil",
  "agencia": "1234",
  "agencia_dv": "5",
  "conta": "56789",
  "conta_dv": "0",
  "cedente_nome": "Minha Empresa LTDA",
  "cedente_documento": "12345678000190",
  "cedente_endereco": "Rua X, 123",
  "carteira": "17",
  "convenio": "123456",
  "percentual_juros": 1.0,
  "percentual_multa": 2.0
}
```

### Gerar Boleto

```bash
POST /api/v1/pagamentos/boletos
Content-Type: application/json

{
  "configuracao_id": 1,
  "valor": 500.00,
  "data_vencimento": "2025-12-01",
  "sacado_nome": "Maria Santos",
  "sacado_documento": "98765432100",
  "sacado_endereco": "Av Y, 456",
  "sacado_cep": "01310000",
  "sacado_cidade": "São Paulo",
  "sacado_uf": "SP",
  "instrucoes": "Não receber após o vencimento",
  "demonstrativo": "Pagamento referente a compra #456"
}
```

**Resposta:**
```json
{
  "id": 1,
  "nosso_numero": "00000000001",
  "numero_documento": "456",
  "codigo_barras": "00190000000000000000000000000000000000000000001",
  "linha_digitavel": "00190.00009 00000.000009 00000.000009 0 00000000000001",
  "valor": 500.00,
  "data_emissao": "2025-11-19",
  "data_vencimento": "2025-12-01",
  "sacado_nome": "Maria Santos",
  "status": "registrado",
  "pdf_path": "/boletos/boleto_00000000001.pdf"
}
```

### Download PDF

```bash
GET /api/v1/pagamentos/boletos/{id}/pdf
```

Retorna PDF do boleto para impressão.

### CNAB - Remessa/Retorno

#### Gerar Arquivo de Remessa (CNAB 240)

```bash
POST /api/v1/pagamentos/boletos/cnab/remessa
Content-Type: application/json

{
  "configuracao_id": 1,
  "boletos_ids": [1, 2, 3]
}
```

Retorna arquivo CNAB 240 para envio ao banco (registro de boletos).

#### Processar Arquivo de Retorno (CNAB 240)

```bash
POST /api/v1/pagamentos/boletos/cnab/retorno
Content-Type: multipart/form-data

arquivo: [arquivo_retorno.rem]
```

Processa arquivo de retorno do banco, atualizando status dos boletos (pagos, baixados, etc).

### Bibliotecas Python para Boleto

```python
# Opção 1: python-boleto (mais completa)
from boleto.itau import BoletoItau
from boleto.bradesco import BoletoBradesco

# Opção 2: pyboleto
from pyboleto.bank.itau import BoletoItau
```

## Conciliação Bancária

### Importar Extrato (OFX)

```bash
POST /api/v1/pagamentos/conciliacao/import-ofx
Content-Type: application/json

{
  "banco_codigo": "001",
  "agencia": "1234",
  "conta": "56789-0",
  "arquivo_base64": "PD94bWwgdmVyc2lvbj0iMS4wIi..."
}
```

### Importar Extrato (CSV)

```bash
POST /api/v1/pagamentos/conciliacao/import-csv
Content-Type: application/json

{
  "banco_codigo": "237",
  "agencia": "5678",
  "conta": "12345-6",
  "arquivo_base64": "ZGF0YTt2YWxvcjt0aXBvCjIwMjUtMTE...",
  "separador": ";",
  "encoding": "utf-8"
}
```

### Listar Lançamentos Não Conciliados

```bash
GET /api/v1/pagamentos/conciliacao/pendentes?banco=001&conta=56789-0
```

**Resposta:**
```json
[
  {
    "id": 1,
    "data": "2025-11-19",
    "descricao": "PIX RECEBIDO",
    "documento": "E12345678...",
    "valor": 150.00,
    "tipo": "C",
    "conciliado": false
  },
  {
    "id": 2,
    "data": "2025-11-19",
    "descricao": "BOLETO PAGO",
    "documento": "00000000001",
    "valor": 500.00,
    "tipo": "C",
    "conciliado": false
  }
]
```

### Conciliar Automaticamente

```bash
POST /api/v1/pagamentos/conciliacao/auto-conciliar
Content-Type: application/json

{
  "banco_codigo": "001",
  "data_inicio": "2025-11-01",
  "data_fim": "2025-11-30"
}
```

Algoritmo de matching automático:
1. **PIX**: Match por E2E ID
2. **Boleto**: Match por Nosso Número no campo documento
3. **Valor e Data**: Tolerância de ±0.01 e ±1 dia

**Resposta:**
```json
{
  "total_lancamentos": 10,
  "conciliados_automaticamente": 8,
  "pendentes": 2,
  "detalhes": [
    {
      "extrato_id": 1,
      "transacao_pix_id": 5,
      "valor": 150.00,
      "diferenca": 0.00
    },
    {
      "extrato_id": 2,
      "boleto_id": 3,
      "valor": 500.00,
      "diferenca": 0.00
    }
  ]
}
```

### Conciliação Manual

```bash
POST /api/v1/pagamentos/conciliacao/manual
Content-Type: application/json

{
  "extrato_bancario_id": 3,
  "tipo": "pix",
  "transacao_pix_id": 7,
  "observacoes": "Conciliado manualmente devido a diferença de data"
}
```

## Fluxos Completos

### Fluxo PIX

```
1. Cliente escolhe PIX no checkout
   ↓
2. Sistema gera cobrança PIX
   POST /api/v1/pagamentos/pix/cobrar
   ↓
3. Cliente recebe QR Code
   (exibe qr_code_imagem ou qr_code_texto)
   ↓
4. Cliente paga via app do banco
   ↓
5. Sistema recebe webhook de confirmação
   POST {webhook_url} com dados do pagamento
   ↓
6. Sistema atualiza status da transação
   status: pendente → aprovado
   ↓
7. Sistema confirma pedido/venda
```

### Fluxo Boleto

```
1. Cliente escolhe Boleto no checkout
   ↓
2. Sistema gera boleto
   POST /api/v1/pagamentos/boletos
   ↓
3. Sistema gera PDF do boleto
   GET /api/v1/pagamentos/boletos/{id}/pdf
   ↓
4. Cliente recebe/baixa PDF
   ↓
5. [OPCIONAL] Sistema envia arquivo de remessa ao banco
   POST /api/v1/pagamentos/boletos/cnab/remessa
   ↓
6. Cliente paga boleto em qualquer banco
   ↓
7. Banco envia arquivo de retorno (CNAB)
   ↓
8. Sistema processa arquivo de retorno
   POST /api/v1/pagamentos/boletos/cnab/retorno
   ↓
9. Sistema atualiza status do boleto
   status: registrado → pago
   ↓
10. Sistema confirma pedido/venda
```

### Fluxo Conciliação

```
1. Diariamente, importar extrato bancário
   POST /api/v1/pagamentos/conciliacao/import-ofx
   ↓
2. Executar conciliação automática
   POST /api/v1/pagamentos/conciliacao/auto-conciliar
   ↓
3. Revisar lançamentos não conciliados
   GET /api/v1/pagamentos/conciliacao/pendentes
   ↓
4. Conciliar manualmente os pendentes
   POST /api/v1/pagamentos/conciliacao/manual
   ↓
5. Gerar relatório de conciliação
   GET /api/v1/pagamentos/conciliacao/relatorio
```

## Configuração

### Variáveis de Ambiente

Adicionar ao `.env`:

```env
# PIX - API BACEN (Direto)
PIX_BACEN_ENDPOINT=https://api.pix.bcb.gov.br
PIX_CERT_PATH=/path/to/certificado.pem
PIX_CERT_PASSWORD=senha_do_certificado

# PIX - Mercado Pago (Gateway)
MERCADOPAGO_ACCESS_TOKEN=APP_USR-xxxx-xxxx-xxxx
MERCADOPAGO_PUBLIC_KEY=APP_USR-xxxx-xxxx-xxxx

# PIX - PagSeguro (Gateway)
PAGSEGURO_EMAIL=contato@empresa.com
PAGSEGURO_TOKEN=xxxx-xxxx-xxxx-xxxx

# Boletos
BOLETO_LOGO_PATH=/path/to/logo.png
BOLETO_PDF_DIR=/path/to/boletos/
```

## Dependências Python

```bash
pip install mercadopago
pip install pagseguro-python
pip install python-boleto
pip install pyofx  # Para parsing OFX
pip install qrcode  # Para gerar QR Code PIX
pip install pillow  # Para manipular imagens
```

Adicionar ao `requirements.txt`:

```txt
# Pagamentos
mercadopago==2.2.0
pagseguro-python==0.1.0
python-boleto==0.3.5
pyofx==0.3.0
qrcode[pil]==7.4.2
pillow==10.1.0
```

## Segurança

### Webhook Signature

Sempre validar assinatura dos webhooks:

```python
import hmac
import hashlib

def validar_webhook_mercadopago(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
```

### Certificado Digital

Para PIX BACEN e alguns bancos para boleto, é necessário certificado digital A1 ou A3.

**Gerar certificado de teste:**
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
```

## Testes

```python
import pytest
from app.modules.pagamentos.services.pix_service import PixService

@pytest.mark.asyncio
async def test_criar_cobranca_pix(async_db_session):
    service = PixService(async_db_session)

    cobranca = await service.criar_cobranca(
        chave_pix_id=1,
        valor=100.00,
        descricao="Teste"
    )

    assert cobranca.txid is not None
    assert cobranca.qr_code_texto is not None
```

## Monitoramento

### Métricas Importantes

1. **Taxa de sucesso PIX**: % de cobranças PIX pagas
2. **Taxa de sucesso Boleto**: % de boletos pagos
3. **Tempo médio de pagamento**: Tempo entre geração e confirmação
4. **Taxa de conciliação automática**: % de lançamentos conciliados automaticamente

### Alertas

- PIX não confirmado após 1 hora
- Boleto vencido não pago
- Lançamentos não conciliados após 3 dias
- Falha na geração de boleto
- Webhook não processado

## Troubleshooting

### PIX não gera QR Code

**Problema**: `qr_code_texto` retorna `None`

**Solução**:
1. Verificar se chave PIX está ativa
2. Verificar credenciais da API
3. Verificar logs de erro

### Boleto sem linha digitável

**Problema**: `linha_digitavel` retorna `None`

**Solução**:
1. Verificar configuração do banco
2. Verificar cálculo do DV (dígito verificador)
3. Verificar biblioteca de boleto instalada

### Conciliação não encontra matches

**Problema**: Nenhum lançamento conciliado automaticamente

**Solução**:
1. Verificar formato do extrato importado
2. Aumentar tolerância de data/valor
3. Verificar campo documento do extrato

## Próximos Passos

1. ✅ Implementar integração Mercado Pago PIX
2. ✅ Implementar geração de boleto Itaú
3. ✅ Implementar CNAB 240 remessa/retorno
4. ⏳ Adicionar suporte a outros bancos
5. ⏳ Implementar recorrência
6. ⏳ Implementar split de pagamentos
7. ⏳ Dashboard de pagamentos

## Referências

- [BACEN - PIX](https://www.bcb.gov.br/estabilidadefinanceira/pix)
- [FEBRABAN - CNAB](https://portal.febraban.org.br/pagina/3053/33/pt-br/cnab)
- [Mercado Pago Docs](https://www.mercadopago.com.br/developers/pt/docs)
- [PagSeguro Docs](https://dev.pagseguro.uol.com.br/docs)
