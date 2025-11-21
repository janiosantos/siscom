"""
Payment Gateway Mock Service

Microserviço que simula Cielo, GetNet e Mercado Pago
para testes de integração do ERP.

Execução:
    uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

Endpoints:
    - Cielo: http://localhost:8001/cielo/*
    - GetNet: http://localhost:8001/getnet/*
    - Mercado Pago: http://localhost:8001/mercadopago/*
    - Admin: http://localhost:8001/admin/*
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.routers import cielo, getnet, mercadopago, admin
from app.config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Payment Gateway Mock Service",
    description="Simula Cielo, GetNet e Mercado Pago para testes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log todas as requisições"""
    start_time = time.time()

    # Log da requisição
    logger.info(f"→ {request.method} {request.url.path}")

    # Processar requisição
    response = await call_next(request)

    # Log da resposta
    duration = time.time() - start_time
    logger.info(
        f"← {request.method} {request.url.path} "
        f"[{response.status_code}] {duration:.3f}s"
    )

    return response


# Registrar routers
app.include_router(
    cielo.router,
    prefix="/cielo",
    tags=["Cielo"]
)

app.include_router(
    getnet.router,
    prefix="/getnet",
    tags=["GetNet"]
)

app.include_router(
    mercadopago.router,
    prefix="/mercadopago",
    tags=["Mercado Pago"]
)

app.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)


@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "service": "Payment Gateway Mock",
        "version": "1.0.0",
        "gateways": ["cielo", "getnet", "mercadopago"],
        "docs": "/docs",
        "admin": "/admin/stats"
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "payment-gateway-mock",
        "timestamp": time.time()
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global de exceções"""
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
