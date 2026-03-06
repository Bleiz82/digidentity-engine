"""
DigIdentity Engine — Celery Configuration
Task queue per pipeline asincrone.
"""

from celery import Celery
from app.core.config import get_settings

settings = get_settings()

# Inizializza Celery
celery_app = Celery(
    "digidentity_engine",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.free_report_task", "app.tasks.premium_report_task"]
)

# Configurazione
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Rome",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=1800,  # 30 minuti max per task
    task_soft_time_limit=1500,  # Warning a 25 minuti
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

print("[OK] Celery configurato")
print(f"   Broker: {settings.REDIS_URL}")
print(f"   Backend: {settings.REDIS_URL}")
