"""
DigIdentity Engine — Applicazione FastAPI principale.

Avvio:
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.api.leads import router as leads_router
from backend.app.api.payment import router as payment_router

# Logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hooks: startup e shutdown."""
    logger.info("=" * 60)
    logger.info("DigIdentity Engine — Avvio in corso...")
    logger.info(f"  Ambiente: {settings.APP_ENV}")
    logger.info(f"  Base URL: {settings.APP_BASE_URL}")
    logger.info(f"  Supabase: {'configurato' if settings.SUPABASE_URL else 'NON configurato'}")
    logger.info(f"  Stripe: {'configurato' if settings.STRIPE_SECRET_KEY else 'NON configurato'}")
    logger.info(f"  Anthropic: {'configurato' if settings.ANTHROPIC_API_KEY else 'NON configurato'}")
    logger.info(f"  SerpAPI: {'configurato' if settings.SERPAPI_KEY else 'NON configurato'}")
    logger.info(f"  SMTP: {'configurato' if settings.SMTP_USER else 'NON configurato'}")
    logger.info(f"  Redis: {settings.REDIS_URL}")
    logger.info("=" * 60)
    yield
    logger.info("DigIdentity Engine — Shutdown")


app = FastAPI(
    title="DigIdentity Engine",
    description=(
        "Sistema automatico di lead generation e diagnosi digitale per PMI italiane. "
        "API per gestione lead, scraping, generazione report AI, pagamenti Stripe."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        settings.APP_BASE_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router
app.include_router(leads_router)
app.include_router(payment_router)


@app.get("/")
async def root():
    """Health check e informazioni di base."""
    return {
        "service": "DigIdentity Engine",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.APP_ENV,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check dettagliato per monitoring."""
    checks = {
        "api": "ok",
        "supabase": "configured" if settings.SUPABASE_URL else "missing",
        "stripe": "configured" if settings.STRIPE_SECRET_KEY else "missing",
        "anthropic": "configured" if settings.ANTHROPIC_API_KEY else "missing",
        "smtp": "configured" if settings.SMTP_USER else "missing",
        "redis": settings.REDIS_URL,
    }
    all_ok = all(v != "missing" for k, v in checks.items() if k != "redis")
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "healthy" if all_ok else "degraded", "checks": checks},
    )
