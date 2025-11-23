"""
Módulo de Integrações - Gateways de Pagamento e APIs Externas
"""

# Import routers para disponibilizar no namespace do módulo
from . import comunicacao_router
from . import frete_router
from . import marketplace_router
from . import mercadopago_router
from . import pagseguro_router

__all__ = [
    "comunicacao_router",
    "frete_router",
    "marketplace_router",
    "mercadopago_router",
    "pagseguro_router",
]
