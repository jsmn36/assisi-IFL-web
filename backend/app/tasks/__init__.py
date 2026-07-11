"""
Celery Tasks
Background task definitions.
In SQLite mode, these modules are not available — use APScheduler instead.
"""
from app.config import settings
import logging

logger = logging.getLogger(__name__)

celery_app = None

if settings.is_postgresql_mode:
    try:
        from app.core.celery_config import celery_app as _celery_app

        celery_app = _celery_app
    except Exception as e:
        logger.warning("Failed to load Celery: %s", e)
else:
    logger.info("SQLite mode: Celery tasks disabled")

__all__ = ["celery_app"]
