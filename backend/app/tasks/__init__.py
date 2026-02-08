"""Tasks package initialization."""
from app.tasks.celery_app import celery_app
from app.tasks.free_report_task import task_free_report
from app.tasks.premium_report_task import task_premium_report

__all__ = ["celery_app", "task_free_report", "task_premium_report"]
