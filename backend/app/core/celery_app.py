"""
DigIdentity Engine — Configurazione Celery.
"""

from celery import Celery

try:
    from backend.app.core.config import settings
except ImportError:
    from app.core.config import settings

celery_app = Celery(
    "digidentity",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "backend.app.tasks.free_report_task",
        "backend.app.tasks.premium_report_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Rome",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=60,
    task_max_retries=3,
)
