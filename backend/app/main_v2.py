"""
DigIdentity Engine V2 — App FastAPI con Agent Inbox.

Avvio:
    uvicorn backend.app.main_v2:app --host 0.0.0.0 --port 8090 --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.services.agent.scheduler_service import scheduler_loop
from backend.app.api.leads import router as leads_router
from backend.app.api.payment import router as payment_router
from backend.app.api.agent.webhooks import router as agent_router

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("DigIdentity Engine V2 — Avvio in corso...")
    logger.info(f"  Ambiente: {settings.APP_ENV}")
    logger.info(f"  Base URL: {settings.APP_BASE_URL}")
    logger.info(f"  Supabase: {'ok' if settings.SUPABASE_URL else 'NO'}")
    logger.info(f"  Stripe: {'ok' if settings.STRIPE_SECRET_KEY else 'NO'}")
    logger.info(f"  Anthropic: {'ok' if settings.ANTHROPIC_API_KEY else 'NO'}")
    logger.info(f"  SMTP: {'ok' if settings.SMTP_USER else 'NO'}")
    logger.info(f"  Redis: {settings.REDIS_URL}")
    logger.info(f"  Agent Inbox: ATTIVO")
    logger.info("=" * 60)
    import asyncio
    scheduler_task = asyncio.create_task(scheduler_loop())
    logger.info("  Scheduler: AVVIATO")
    yield
    scheduler_task.cancel()
    logger.info("DigIdentity Engine V2 — Shutdown")


app = FastAPI(
    title="DigIdentity Engine V2",
    description="Engine + Agent Inbox omnicanale",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8090",
        "http://127.0.0.1:8090",
        settings.APP_BASE_URL,
        "https://admin.digidentityagency.it",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router esistenti (non modificati)
app.include_router(leads_router)
app.include_router(payment_router)

# Nuovo router agente
app.include_router(agent_router)


@app.get("/")
async def root():
    return {
        "service": "DigIdentity Engine V2",
        "version": "2.0.0",
        "status": "running",
        "environment": settings.APP_ENV,
        "agent_inbox": True,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    checks = {
        "api": "ok",
        "supabase": "ok" if settings.SUPABASE_URL else "missing",
        "stripe": "ok" if settings.STRIPE_SECRET_KEY else "missing",
        "anthropic": "ok" if settings.ANTHROPIC_API_KEY else "missing",
        "smtp": "ok" if settings.SMTP_USER else "missing",
        "redis": settings.REDIS_URL,
        "agent_inbox": "ok",
    }
    all_ok = all(v != "missing" for k, v in checks.items() if k != "redis")
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content={"status": "healthy" if all_ok else "degraded", "checks": checks},
    )
