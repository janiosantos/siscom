"""
Ponto de entrada principal da aplicação ERP
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Criação da aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema ERP completo para loja de materiais de construção",
    lifespan=lifespan,
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Importação e registro dos routers dos módulos
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

# Sprint 2
try:
    from app.modules.orcamentos.router import router as orcamentos_router
    app.include_router(orcamentos_router, prefix="/api/v1/orcamentos", tags=["Orçamentos"])
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


@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz"""
    return {
        "message": "ERP Materiais de Construção - API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
