"""
Ponto de entrada principal da aplicação ERP
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import setup_logging, setup_sentry, get_logger
from app.middleware.correlation import CorrelationIdMiddleware
from app.middleware.rate_limit import setup_rate_limiting, limiter
from app.middleware.security_headers import setup_security_headers

# Configura logging estruturado
setup_logging()
logger = get_logger(__name__)

# Configura Sentry (se configurado)
if settings.SENTRY_DSN:
    setup_sentry()
    logger.info("Sentry integration enabled")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    logger.info("Starting application", extra={
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production"
    })
    await init_db()
    logger.info("Database initialized successfully")
    yield
    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Application shutdown complete")


# Criação da aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema ERP completo para loja de materiais de construção",
    lifespan=lifespan,
)


# ============================================================================
# Exception Handlers Globais
# ============================================================================
from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import ERPException

@app.exception_handler(ERPException)
async def erp_exception_handler(request: Request, exc: ERPException):
    """Handler para todas as exceções customizadas do ERP"""
    logger.warning(
        f"ERP Exception: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "error_message": exc.message,
        }
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


# Configuração de Rate Limiting
setup_rate_limiting(app)

# Configuração de Security Headers
setup_security_headers(app)

# Configuração de Middlewares

# Middleware de Correlation ID (deve ser o primeiro)
app.add_middleware(CorrelationIdMiddleware)

# Configuração CORS (mais restritivo em produção)
cors_config = {
    "allow_origins": settings.ALLOWED_ORIGINS,
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allow_headers": ["*"],
}

# Em produção, restringe headers permitidos
if not settings.DEBUG:
    cors_config["allow_headers"] = [
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "X-Correlation-ID",
    ]
    cors_config["expose_headers"] = ["X-Correlation-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
    cors_config["max_age"] = 600  # Cache preflight por 10 minutos

app.add_middleware(CORSMiddleware, **cors_config)


# Importação e registro dos routers dos módulos

# Autenticação e Autorização
try:
    from app.modules.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticação"])
except ImportError:
    pass

# Sprint 1
try:
    from app.modules.produtos.router import router as produtos_router
    app.include_router(produtos_router, prefix="/api/v1/produtos", tags=["Produtos"])
except ImportError:
    pass

try:
    from app.modules.categorias.router import router as categorias_router
    app.include_router(categorias_router, prefix="/api/v1/categorias", tags=["Categorias"])
except ImportError:
    pass

try:
    from app.modules.estoque.router import router as estoque_router
    app.include_router(estoque_router, prefix="/api/v1/estoque", tags=["Estoque"])
except ImportError:
    pass

try:
    from app.modules.vendas.router import router as vendas_router
    app.include_router(vendas_router, prefix="/api/v1/vendas", tags=["Vendas"])
except ImportError:
    pass

try:
    from app.modules.pdv.router import router as pdv_router
    app.include_router(pdv_router, prefix="/api/v1/pdv", tags=["PDV"])
except ImportError:
    pass

try:
    from app.modules.financeiro.router import router as financeiro_router
    app.include_router(financeiro_router, prefix="/api/v1/financeiro", tags=["Financeiro"])
except ImportError:
    pass

try:
    from app.modules.nfe.router import router as nfe_router
    app.include_router(nfe_router, prefix="/api/v1/nfe", tags=["NF-e/NFC-e"])
except ImportError:
    pass

try:
    from app.modules.condicoes_pagamento.router import router as condicoes_pagamento_router
    app.include_router(condicoes_pagamento_router, prefix="/api/v1/condicoes-pagamento", tags=["Condições de Pagamento"])
except ImportError:
    pass

try:
    from app.modules.clientes.router import router as clientes_router
    app.include_router(clientes_router, prefix="/api/v1/clientes", tags=["Clientes"])
except ImportError:
    pass

# Sprint 2
try:
    from app.modules.orcamentos.router import router as orcamentos_router
    app.include_router(orcamentos_router, prefix="/api/v1/orcamentos", tags=["Orçamentos"])
except ImportError:
    pass

try:
    from app.modules.pedidos_venda.router import router as pedidos_venda_router
    app.include_router(pedidos_venda_router, prefix="/api/v1/pedidos-venda", tags=["Pedidos de Venda"])
except ImportError:
    pass

try:
    from app.modules.documentos_auxiliares.router import router as documentos_auxiliares_router
    app.include_router(documentos_auxiliares_router, prefix="/api/v1/documentos-auxiliares", tags=["Documentos Auxiliares"])
except ImportError:
    pass

# Sprint 3
try:
    from app.modules.compras.router import router as compras_router
    app.include_router(compras_router, prefix="/api/v1/compras", tags=["Compras"])
except ImportError:
    pass

try:
    from app.modules.fornecedores.router import router as fornecedores_router
    app.include_router(fornecedores_router, prefix="/api/v1/fornecedores", tags=["Fornecedores"])
except ImportError:
    pass

try:
    from app.modules.mobile.router import router as mobile_router
    app.include_router(mobile_router, prefix="/api/v1/mobile", tags=["Mobile"])
except ImportError:
    pass

# Sprint 4
try:
    from app.modules.os.router import router as os_router
    app.include_router(os_router, prefix="/api/v1/os", tags=["Ordens de Serviço"])
except ImportError:
    pass

# Sprint 6
try:
    from app.modules.ecommerce.router import router as ecommerce_router
    app.include_router(ecommerce_router, prefix="/api/v1/ecommerce", tags=["E-commerce"])
except ImportError:
    pass

try:
    from app.modules.relatorios.router import router as relatorios_router
    app.include_router(relatorios_router, prefix="/api/v1/relatorios", tags=["Relatórios"])
except ImportError:
    pass

# Sprint 7
try:
    from app.modules.crm.router import router as crm_router
    app.include_router(crm_router, prefix="/api/v1/crm", tags=["CRM"])
except ImportError:
    pass

# Pagamentos (Fase 2 - Compliance Brasil)
try:
    from app.modules.pagamentos.router import router as pagamentos_router
    app.include_router(pagamentos_router, prefix="/api/v1/pagamentos", tags=["Pagamentos"])
except ImportError:
    pass

# Integrações de Pagamento (Fase 4)
try:
    from app.integrations.mercadopago_router import router as mercadopago_router
    app.include_router(mercadopago_router, prefix="/api/v1/integrations", tags=["Integrações"])
except ImportError:
    pass

try:
    from app.integrations.pagseguro_router import router as pagseguro_router
    app.include_router(pagseguro_router, prefix="/api/v1/integrations", tags=["Integrações"])
except ImportError:
    pass

# Integrações de Frete (Fase 4)
try:
    from app.integrations.frete_router import router as frete_router
    app.include_router(frete_router, prefix="/api/v1/integrations", tags=["Integrações"])
except ImportError:
    pass

# Integrações de Comunicação (Fase 4)
try:
    from app.integrations.comunicacao_router import router as comunicacao_router
    app.include_router(comunicacao_router, prefix="/api/v1/integrations", tags=["Integrações"])
except ImportError:
    pass

# Integrações de Marketplaces (Fase 4)
try:
    from app.integrations.marketplace_router import router as marketplace_router
    app.include_router(marketplace_router, prefix="/api/v1/integrations", tags=["Integrações"])
except ImportError:
    pass

# Import/Export Avançado (Fase 3)
try:
    from app.modules.importexport.router import router as importexport_router
    app.include_router(importexport_router, prefix="/api/v1/importexport", tags=["Import/Export"])
except ImportError:
    pass

# Gateway Cielo (Fase 4)
try:
    from app.integrations.cielo_router import router as cielo_router
    app.include_router(cielo_router, prefix="/api/v1/integrations", tags=["Integrações"])
except ImportError:
    pass

# Gateway GetNet (Fase 4)
try:
    from app.integrations.getnet_router import router as getnet_router
    app.include_router(getnet_router, prefix="/api/v1/integrations", tags=["Integrações"])
except ImportError:
    pass

# Gateway Sicoob (Fase 4)
try:
    from app.integrations.sicoob_router import router as sicoob_router
    app.include_router(sicoob_router, prefix="/api/v1/integrations", tags=["Integrações"])
except ImportError:
    pass

# Analytics e Machine Learning (Fase 5)
try:
    from app.analytics.router import router as analytics_router
    app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics & ML"])
except ImportError:
    pass


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz"""
    return {
        "message": "ERP Materiais de Construção - API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# Registra endpoints de health check
from app.core.health import router as health_router
app.include_router(health_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
