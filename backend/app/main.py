"""
DigIdentity Engine — FastAPI Application
Entry point dell'applicazione backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import health, lead_workflow, payment

# Carica settings
settings = get_settings()

# Crea app FastAPI
app = FastAPI(
    title="DigIdentity Engine API",
    description="Backend per la Diagnosi Strategica Digitale automatizzata",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,  # Swagger UI solo in debug
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://digidentityagency.it",
        "https://www.digidentityagency.it",
        "http://localhost:3000",  # Frontend Next.js in dev
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(lead_workflow.router, prefix="/api", tags=["Lead Workflow"])
app.include_router(payment.router, tags=["Payment"])


@app.on_event("startup")
async def startup_event():
    """Eseguito all'avvio dell'applicazione."""
    print("[START] DigIdentity Engine avviato!")
    print(f"[INFO] Environment: {'DEBUG' if settings.debug else 'PRODUCTION'}")
    print(f"[URL] Base URL: {settings.app_base_url}")


@app.on_event("shutdown")
async def shutdown_event():
    """Eseguito allo shutdown dell'applicazione."""
    print("[STOP] DigIdentity Engine arrestato.")
