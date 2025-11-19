# Módulo de Condições de Pagamento

Módulo completo para gerenciar condições de pagamento no ERP.

## Estrutura de Arquivos

```
/home/user/siscom/app/modules/condicoes_pagamento/
├── __init__.py           # Exportações do módulo
├── models.py             # Modelos SQLAlchemy (CondicaoPagamento, ParcelaPadrao)
├── schemas.py            # Schemas Pydantic com validações
├── repository.py         # Camada de acesso a dados
├── service.py            # Lógica de negócio
├── router.py             # Endpoints FastAPI
└── README.md             # Este arquivo
```

## Modelos

### CondicaoPagamento
- **id**: Integer (PK)
- **nome**: String(100) - Nome único da condição
- **descricao**: String(500) - Descrição opcional
- **tipo**: Enum (AVISTA, PRAZO, PARCELADO)
- **quantidade_parcelas**: Integer - Quantidade de parcelas
- **intervalo_dias**: Integer - Intervalo entre parcelas
- **entrada_percentual**: Numeric(5,2) - Percentual de entrada
- **ativa**: Boolean - Status da condição
- **created_at**: DateTime
- **updated_at**: DateTime
- **parcelas**: Relationship com ParcelaPadrao

### ParcelaPadrao
- **id**: Integer (PK)
- **condicao_id**: Integer (FK)
- **numero_parcela**: Integer - Número sequencial da parcela
- **dias_vencimento**: Integer - Dias até o vencimento
- **percentual_valor**: Numeric(5,2) - Percentual do valor total
- **created_at**: DateTime

## Regras de Negócio

### Validações por Tipo

#### AVISTA (À Vista)
- Deve ter exatamente 1 parcela
- Intervalo de dias deve ser 0
- Vencimento da parcela: 0 dias

#### PRAZO (A Prazo)
- Deve ter 1 ou mais parcelas
- Permite intervalos personalizados

#### PARCELADO
- Deve ter 2 ou mais parcelas
- Permite entrada + parcelas

### Validações Gerais
- Soma dos percentuais das parcelas DEVE ser exatamente 100%
- Numeração das parcelas deve ser sequencial (1, 2, 3...)
- Nome da condição deve ser único
- Quantidade de parcelas >= 1

## Endpoints da API

### POST /api/v1/condicoes-pagamento/
Cria nova condição de pagamento com parcelas.

### GET /api/v1/condicoes-pagamento/{id}
Busca condição específica com suas parcelas.

### GET /api/v1/condicoes-pagamento/
Lista condições com paginação e filtros.

### GET /api/v1/condicoes-pagamento/ativas/list
Lista apenas condições ativas (sem paginação).

### PUT /api/v1/condicoes-pagamento/{id}
Atualiza condição de pagamento.

### DELETE /api/v1/condicoes-pagamento/{id}
Inativa condição (soft delete).

### POST /api/v1/condicoes-pagamento/calcular/parcelas
Calcula parcelas para um valor específico.

## Exemplos de Uso

### 1. Criar Condição "À Vista"

```json
POST /api/v1/condicoes-pagamento/

{
    "nome": "À Vista",
    "descricao": "Pagamento à vista",
    "tipo": "AVISTA",
    "quantidade_parcelas": 1,
    "intervalo_dias": 0,
    "entrada_percentual": 0,
    "ativa": true,
    "parcelas": [
        {
            "numero_parcela": 1,
            "dias_vencimento": 0,
            "percentual_valor": 100.0
        }
    ]
}
```

### 2. Criar Condição "30/60/90"

```json
POST /api/v1/condicoes-pagamento/

{
    "nome": "30/60/90",
    "descricao": "3 parcelas - 30, 60 e 90 dias",
    "tipo": "PARCELADO",
    "quantidade_parcelas": 3,
    "intervalo_dias": 30,
    "entrada_percentual": 0,
    "ativa": true,
    "parcelas": [
        {
            "numero_parcela": 1,
            "dias_vencimento": 30,
            "percentual_valor": 33.33
        },
        {
            "numero_parcela": 2,
            "dias_vencimento": 60,
            "percentual_valor": 33.33
        },
        {
            "numero_parcela": 3,
            "dias_vencimento": 90,
            "percentual_valor": 33.34
        }
    ]
}
```

### 3. Criar Condição "50% Entrada + 30/60"

```json
POST /api/v1/condicoes-pagamento/

{
    "nome": "50% Entrada + 30/60",
    "descricao": "50% de entrada + 2 parcelas",
    "tipo": "PARCELADO",
    "quantidade_parcelas": 3,
    "intervalo_dias": 30,
    "entrada_percentual": 50,
    "ativa": true,
    "parcelas": [
        {
            "numero_parcela": 1,
            "dias_vencimento": 0,
            "percentual_valor": 50.0
        },
        {
            "numero_parcela": 2,
            "dias_vencimento": 30,
            "percentual_valor": 25.0
        },
        {
            "numero_parcela": 3,
            "dias_vencimento": 60,
            "percentual_valor": 25.0
        }
    ]
}
```

### 4. Calcular Parcelas para Venda

```json
POST /api/v1/condicoes-pagamento/calcular/parcelas

{
    "condicao_id": 1,
    "valor_total": 1000.00,
    "data_base": "2025-01-15"
}
```

**Resposta:**
```json
{
    "condicao": {
        "id": 1,
        "nome": "30/60/90",
        "tipo": "PARCELADO",
        ...
    },
    "valor_total": 1000.00,
    "parcelas": [
        {
            "numero_parcela": 1,
            "valor": 333.33,
            "vencimento": "2025-02-14",
            "percentual": 33.33
        },
        {
            "numero_parcela": 2,
            "valor": 333.33,
            "vencimento": "2025-03-16",
            "percentual": 33.33
        },
        {
            "numero_parcela": 3,
            "valor": 333.34,
            "vencimento": "2025-04-15",
            "percentual": 33.34
        }
    ]
}
```

## Casos de Uso

### 1. Cadastro de Condição
O service valida todas as regras de negócio antes de persistir.

### 2. Cálculo de Parcelas em Vendas
Ao finalizar uma venda, o sistema calcula automaticamente as parcelas com base na condição escolhida.

### 3. Ajuste de Arredondamento
O sistema garante que a soma das parcelas seja igual ao valor total, ajustando a última parcela se necessário.

### 4. Soft Delete
Condições inativas não são excluídas do banco, permitindo manter histórico de vendas antigas.

## Integração com Outros Módulos

### Vendas
- Ao criar uma venda, seleciona-se uma condição de pagamento ativa
- As parcelas são calculadas automaticamente

### Financeiro
- As parcelas calculadas geram títulos no contas a receber
- Cada parcela se torna um título a receber

### PDV
- Lista condições ativas para seleção rápida
- Calcula parcelas em tempo real

## Tecnologias

- **SQLAlchemy 2.0**: ORM async
- **Pydantic v2**: Validação de dados
- **FastAPI**: Framework web
- **PostgreSQL**: Banco de dados (recomendado)

## Estatísticas

- **Total de linhas**: ~1110 linhas
- **Arquivos**: 6 arquivos Python
- **Endpoints**: 7 endpoints REST
- **Modelos**: 2 modelos (CondicaoPagamento, ParcelaPadrao)
- **Schemas**: 11 schemas Pydantic
