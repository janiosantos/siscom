#!/usr/bin/env python3
"""
Script de teste rápido para validar o mock service

Uso: python test_mock.py
"""
import requests
import json
import time


BASE_URL = "http://localhost:8001"


def print_section(title):
    """Imprimir título de seção"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def test_health():
    """Testar health check"""
    print_section("Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200


def test_cielo_credit_card():
    """Testar pagamento Cielo cartão de crédito"""
    print_section("Cielo - Cartão de Crédito")

    payload = {
        "MerchantOrderId": "TEST-ORDER-001",
        "Payment": {
            "Type": "CreditCard",
            "Amount": 15000,
            "Installments": 3,
            "Capture": True,
            "CreditCard": {
                "CardNumber": "4532000000000000",
                "Holder": "TESTE USUARIO",
                "ExpirationDate": "12/2028",
                "SecurityCode": "123",
                "Brand": "Visa"
            }
        }
    }

    response = requests.post(
        f"{BASE_URL}/cielo/1/sales",
        headers={
            "MerchantId": "mock-merchant",
            "MerchantKey": "mock-key",
            "Content-Type": "application/json"
        },
        json=payload
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Payment ID: {data['Payment']['PaymentId']}")
    print(f"Status: {data['Payment']['Status']}")
    print(f"Amount: R$ {data['Payment']['Amount'] / 100:.2f}")

    assert response.status_code == 200
    return data['Payment']['PaymentId']


def test_getnet_pix():
    """Testar pagamento GetNet PIX"""
    print_section("GetNet - PIX")

    # 1. Obter token OAuth
    token_response = requests.post(
        f"{BASE_URL}/getnet/auth/oauth/v2/token",
        data={
            "client_id": "mock-client",
            "client_secret": "mock-secret",
            "scope": "oob"
        }
    )
    token = token_response.json()["access_token"]
    print(f"Token obtido: {token[:20]}...")

    # 2. Criar pagamento PIX
    payload = {
        "seller_id": "SELLER-001",
        "amount": 15000,
        "currency": "BRL",
        "order": {
            "order_id": "TEST-PIX-001",
            "sales_tax": 0,
            "product_type": "service"
        }
    }

    response = requests.post(
        f"{BASE_URL}/getnet/v1/payments/pix",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=payload
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Payment ID: {data['payment_id']}")
    print(f"Status: {data['status']}")
    print(f"QR Code: {data['pix']['qrcode'][:50]}...")

    assert response.status_code == 200
    return data['payment_id']


def test_mercadopago_pix():
    """Testar pagamento Mercado Pago PIX"""
    print_section("Mercado Pago - PIX")

    payload = {
        "transaction_amount": 150.00,
        "description": "Teste ERP",
        "payment_method_id": "pix",
        "payer": {
            "email": "teste@teste.com"
        },
        "external_reference": "TEST-MP-001"
    }

    response = requests.post(
        f"{BASE_URL}/mercadopago/v1/payments",
        headers={
            "Authorization": "Bearer mock-token",
            "Content-Type": "application/json"
        },
        json=payload
    )

    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Payment ID: {data['id']}")
    print(f"Status: {data['status']}")
    print(f"QR Code: {data['point_of_interaction']['transaction_data']['qr_code'][:50]}...")

    assert response.status_code == 200
    return data['id']


def test_admin_stats():
    """Testar estatísticas administrativas"""
    print_section("Admin - Estatísticas")

    response = requests.get(f"{BASE_URL}/admin/stats")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

    assert response.status_code == 200


def test_approve_pix(payment_id):
    """Testar aprovação manual de PIX"""
    print_section(f"Admin - Aprovar PIX {payment_id}")

    response = requests.post(
        f"{BASE_URL}/admin/transactions/{payment_id}/approve"
    )

    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

    assert response.status_code == 200


def main():
    """Executar todos os testes"""
    print("\n🚀 Iniciando testes do Payment Gateway Mock\n")

    try:
        # Health check
        test_health()
        time.sleep(0.5)

        # Testar gateways
        cielo_payment_id = test_cielo_credit_card()
        time.sleep(0.5)

        getnet_payment_id = test_getnet_pix()
        time.sleep(0.5)

        mp_payment_id = test_mercadopago_pix()
        time.sleep(0.5)

        # Aprovar um PIX
        test_approve_pix(getnet_payment_id)
        time.sleep(0.5)

        # Estatísticas
        test_admin_stats()

        print_section("✅ TODOS OS TESTES PASSARAM!")

    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        return 1

    except requests.exceptions.ConnectionError:
        print("\n❌ ERRO: Não foi possível conectar ao mock service")
        print("Certifique-se de que o serviço está rodando:")
        print("  docker-compose up -d")
        print("  ou")
        print("  python -m app.main")
        return 1

    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
