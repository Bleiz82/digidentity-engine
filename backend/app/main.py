"""
DigIdentity Engine — Applicazione FastAPI principale.

Avvio:
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

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
    logger.info(f"  Stripe Links: Premium={'si' if settings.STRIPE_LINK_PREMIUM else 'no'}, Consulenza={'si' if settings.STRIPE_LINK_CONSULENZA else 'no'}")
    logger.info(f"  Anthropic: {'configurato' if settings.ANTHROPIC_API_KEY else 'NON configurato'}")
    logger.info(f"  OpenAI: {'configurato' if settings.OPENAI_API_KEY else 'NON configurato'}")
    logger.info(f"  Perplexity: {'configurato' if settings.PERPLEXITY_API_KEY else 'NON configurato'}")
    logger.info(f"  SerpAPI: {'configurato' if settings.SERPAPI_KEY else 'NON configurato'}")
    logger.info(f"  PageSpeed: {'configurato' if settings.GOOGLE_PAGESPEED_API_KEY else 'NON configurato'}")
    logger.info(f"  Apify: {'configurato' if settings.APIFY_API_KEY else 'NON configurato'}")
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
    version="1.1.0",
    lifespan=lifespan,
)


# --- Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS — in produzione APP_BASE_URL sara' il dominio reale
cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]
if settings.APP_BASE_URL and settings.APP_BASE_URL not in cors_origins:
    cors_origins.append(settings.APP_BASE_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "stripe-signature"],
)

# Router
app.include_router(leads_router)
app.include_router(payment_router)


@app.get("/")
async def root():
    """Health check e informazioni di base."""
    return {
        "service": "DigIdentity Engine",
        "version": "1.1.0",
        "status": "running",
        "environment": settings.APP_ENV,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check dettagliato per monitoring."""
    # Check Redis
    redis_status = "unknown"
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, socket_timeout=3)
        r.ping()
        redis_status = "ok"
    except Exception as e:
        redis_status = f"error: {str(e)[:80]}"

    checks = {
        "api": "ok",
        "supabase": "configured" if settings.SUPABASE_URL else "missing",
        "stripe": "configured" if settings.STRIPE_SECRET_KEY else "missing",
        "anthropic": "configured" if settings.ANTHROPIC_API_KEY else "missing",
        "openai": "configured" if settings.OPENAI_API_KEY else "missing",
        "perplexity": "configured" if settings.PERPLEXITY_API_KEY else "not_configured",
        "pagespeed": "configured" if settings.GOOGLE_PAGESPEED_API_KEY else "not_configured",
        "serpapi": "configured" if settings.SERPAPI_KEY else "missing",
        "smtp": "configured" if settings.SMTP_USER else "missing",
        "redis": redis_status,
    }

    critical_ok = all(
        v not in ("missing",)
        for k, v in checks.items()
        if k in ("api", "supabase", "stripe", "anthropic", "openai", "serpapi", "smtp")
    )
    redis_ok = redis_status == "ok"

    return JSONResponse(
        status_code=200 if (critical_ok and redis_ok) else 503,
        content={
            "status": "healthy" if (critical_ok and redis_ok) else "degraded",
            "checks": checks,
        },
    )
