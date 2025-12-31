"""
FastAPI Application - Backend asincrono per ActProof.ai
Production-ready with rate limiting and audit trail
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from actproof.api.routes import router
from actproof.api.rate_limiter import rate_limit_middleware, get_rate_limiter
from actproof.integrations import AuditMiddleware, AuditEventType
from pathlib import Path
import time

# Inizializza audit middleware
audit_middleware = AuditMiddleware(
    audit_log_path=Path("logs/audit.log"),
    enable_file_logging=True,
)

# Crea app FastAPI
app = FastAPI(
    title="ActProof.ai API",
    description="API per Repository Intelligence e Compliance EU AI Act",
    version="0.3.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare origini consentite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_handler(request: Request, call_next):
    """Middleware per rate limiting con tier-based quotas"""
    return await rate_limit_middleware(request, call_next)


# Middleware per audit trail automatico
@app.middleware("http")
async def audit_middleware_handler(request: Request, call_next):
    """Middleware per loggare tutte le richieste API"""
    start_time = time.time()
    
    # Estrai informazioni richiesta
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Esegui richiesta
    try:
        response = await call_next(request)
        success = response.status_code < 400
        
        # Logga evento
        audit_middleware.log_event(
            event_type=AuditEventType.API_REQUEST,
            operation=f"{request.method} {request.url.path}",
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            input_data={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
            },
            output_data={
                "status_code": response.status_code,
                "duration_ms": (time.time() - start_time) * 1000,
            },
        )
        
        return response
    except Exception as e:
        # Logga errore
        audit_middleware.log_event(
            event_type=AuditEventType.API_REQUEST,
            operation=f"{request.method} {request.url.path}",
            success=False,
            error_message=str(e),
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise


# Includi router
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ActProof.ai API",
        "version": "0.3.0",
        "status": "running",
        "features": {
            "fase_1": "Repository Intelligence & AI-BOM",
            "fase_2": "Compliance Engine & RAG",
            "fase_3": "Fairness & Bias Auditing",
            "fase_4": "AWS Marketplace & Audit Trail",
        },
        "endpoints": {
            "health": "/health",
            "api": "/api/v1",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
