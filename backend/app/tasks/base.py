"""
Base Task Classes
In PostgreSQL mode, these provide Celery task base classes.
In SQLite mode, this module is not imported — use APScheduler.
"""
from app.config import settings

if not settings.is_postgresql_mode:
    raise ImportError(
        "Celery task bases require PostgreSQL mode. " "Set DATABASE_URL to enable."
    )

from celery import Task
from app.database import SessionLocal
from app.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session lifecycle management."""

    _db = None

    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


class CachedTask(Task):
    """Base task with deduplication via cache."""

    def apply_async(self, args=None, kwargs=None, task_id=None, **options):
        cache_key = self.get_cache_key(args, kwargs)
        if cache.exists(cache_key, namespace="tasks"):
            logger.info(f"Task {self.name} already running, skipping")
            return None
        cache.set(cache_key, "running", namespace="tasks", ttl=3600)
        return super().apply_async(args, kwargs, task_id, **options)

    def get_cache_key(self, args, kwargs):
        import hashlib
        import json

        key_data = {"name": self.name, "args": args or [], "kwargs": kwargs or {}}
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def after_return(self, *args, **kwargs):
        cache_key = self.get_cache_key(args, kwargs)
        cache.delete(cache_key, namespace="tasks")


class RetryTask(Task):
    """Base task with exponential backoff retry."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True
