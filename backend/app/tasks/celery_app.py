"""
DigIdentity Engine — Celery Configuration
Task queue per pipeline asincrone.
"""

from celery import Celery
from app.config import get_settings

settings = get_settings()

# Inizializza Celery
celery_app = Celery(
    "digidentity_engine",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
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
    task_time_limit=600,  # 10 minuti max per task
    task_soft_time_limit=540,  # Warning a 9 minuti
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
)

print("[OK] Celery configurato")
print(f"   Broker: {settings.celery_broker_url}")
print(f"   Backend: {settings.celery_result_backend}")
