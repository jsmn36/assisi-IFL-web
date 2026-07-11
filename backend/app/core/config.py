import os
from typing import Optional

# Module-level Celery config


class Settings:
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    SECRET_KEY: str = "dev-secret-key"
    DEBUG: bool = True

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Cache TTL (seconds)
    CACHE_TTL_SHORT: int = 60
    CACHE_TTL_MEDIUM: int = 300
    CACHE_TTL_LONG: int = 3600
    CACHE_TTL_DAY: int = 86400

    # Celery Configuration
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 3600

    # Email Configuration
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@assisisocial.com"
    FROM_NAME: str = "Assisi Social"


settings = Settings()
