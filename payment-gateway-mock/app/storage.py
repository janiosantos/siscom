"""
Armazenamento em memória para transações
"""
from typing import Dict, Optional, List
from app.models import Transaction, WebhookConfig
import logging

logger = logging.getLogger(__name__)


class InMemoryStorage:
    """Storage simples em memória"""

    def __init__(self):
        self.transactions: Dict[str, Transaction] = {}
        self.webhooks: Dict[str, List[WebhookConfig]] = {}
        self.stats = {
            "total_transactions": 0,
            "approved": 0,
            "denied": 0,
            "cancelled": 0,
            "refunded": 0
        }

    def save_transaction(self, transaction: Transaction) -> Transaction:
        """Salvar transação"""
        self.transactions[transaction.id] = transaction
        self.stats["total_transactions"] += 1
        logger.info(f"Transação salva: {transaction.id} - {transaction.status}")
        return transaction

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Buscar transação por ID"""
        return self.transactions.get(transaction_id)

    def update_transaction(self, transaction_id: str, updates: dict) -> Optional[Transaction]:
        """Atualizar transação"""
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            return None

        for key, value in updates.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)

        logger.info(f"Transação atualizada: {transaction_id}")
        return transaction

    def list_transactions(
        self,
        gateway: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Transaction]:
        """Listar transações com filtros"""
        transactions = list(self.transactions.values())

        if gateway:
            transactions = [t for t in transactions if t.gateway == gateway]

        if status:
            transactions = [t for t in transactions if t.status == status]

        # Ordenar por data (mais recente primeiro)
        transactions.sort(key=lambda x: x.created_at, reverse=True)

        return transactions[:limit]

    def register_webhook(self, gateway: str, webhook: WebhookConfig):
        """Registrar webhook"""
        if gateway not in self.webhooks:
            self.webhooks[gateway] = []
        self.webhooks[gateway].append(webhook)
        logger.info(f"Webhook registrado para {gateway}: {webhook.url}")

    def get_webhooks(self, gateway: str) -> List[WebhookConfig]:
        """Obter webhooks de um gateway"""
        return self.webhooks.get(gateway, [])

    def update_stats(self, status: str):
        """Atualizar estatísticas"""
        if status in self.stats:
            self.stats[status] += 1

    def get_stats(self) -> dict:
        """Obter estatísticas"""
        return {
            **self.stats,
            "cielo_transactions": len([
                t for t in self.transactions.values()
                if t.gateway == "cielo"
            ]),
            "getnet_transactions": len([
                t for t in self.transactions.values()
                if t.gateway == "getnet"
            ]),
            "mercadopago_transactions": len([
                t for t in self.transactions.values()
                if t.gateway == "mercadopago"
            ])
        }

    def clear_all(self):
        """Limpar todos os dados (útil para testes)"""
        self.transactions.clear()
        self.webhooks.clear()
        self.stats = {
            "total_transactions": 0,
            "approved": 0,
            "denied": 0,
            "cancelled": 0,
            "refunded": 0
        }
        logger.info("Storage limpo")


# Singleton global
storage = InMemoryStorage()
