from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "This module requires PostgreSQL mode. Set DATABASE_URL to enable."
    )

"""
Celery Application Configuration
"""
from celery import Celery
from app.core.config import settings

# Get Celery configuration from settings with fallbacks
broker_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = getattr(settings, "CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

celery_app = Celery(
    "pms_hotel",
    broker=broker_url,
    backend=result_backend,
    include=["app.tasks.email_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit (warning before kill)
    worker_prefetch_multiplier=1,  # Prevent task prefetching issues
    task_acks_late=True,  # Acknowledge after task completes, not before
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (memory leaks)
)

# Optional: Configure periodic tasks (celery beat)
celery_app.conf.beat_schedule = {
    "send-check-in-reminders-every-hour": {
        "task": "app.tasks.email_tasks.send_check_in_reminders",
        "schedule": 3600.0,  # Run every hour (in seconds)
        "options": {"timezone": "UTC"},  # FIX: Explicit timezone for beat schedule
    },
}
