from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "This module requires PostgreSQL mode. Set DATABASE_URL to enable."
    )

"""
Celery Configuration
Task queue and worker configuration
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Build URLs directly from settings attributes
BROKER_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"
RESULT_BACKEND = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2"

celery_app = Celery(
    "hotel_pms",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    result_expires=86400,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_rate_limit="100/m",
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "cleanup-old-tasks": {
            "task": "app.tasks.maintenance.cleanup_old_task_results",
            "schedule": crontab(hour=2, minute=0),
        },
        "daily-report": {
            "task": "app.tasks.reports.generate_daily_report",
            "schedule": crontab(hour=6, minute=0),
        },
        "check-reservation-reminders": {
            "task": "app.tasks.notifications.check_reservation_reminders",
            "schedule": crontab(minute="*/30"),
        },
    },
    task_routes={
        "app.tasks.emails.*": {"queue": "emails"},
        "app.tasks.reports.*": {"queue": "reports"},
        "app.tasks.notifications.*": {"queue": "notifications"},
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
