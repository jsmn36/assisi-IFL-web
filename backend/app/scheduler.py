"""
Scheduled task runner for SQLite mode.
In PostgreSQL mode, use Celery instead (app/tasks/celery_app.py).
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
import logging

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def start_scheduler():
    if settings.is_postgresql_mode:
        logger.info("PostgreSQL mode: scheduler disabled (use Celery)")
        return
    scheduler.start()
    logger.info("APScheduler started (SQLite mode)")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
