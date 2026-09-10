import logging
import sys
from pathlib import Path
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


LEAKED_DEV_JWT_SECRETS = {
    "a_very_secure_random_string_12345",
    "changeme",
    "secret",
}
LEAKED_SERVICE_TOKENS = {
    "pos-inv-sync-secret",
}


def _is_production(env: str) -> bool:
    return env.lower() in {"production", "prod"}


class Settings(BaseSettings):
    # Database
    DATABASE_URL: Optional[str] = None
    CRM_DATABASE_URL: Optional[str] = None

    # App
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # CORS — comma-separated list of allowed origins.
    # In production, set this to explicit allowed domains (no wildcards).
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://localhost:3000,http://localhost:3001,http://localhost:3002,"
        "http://127.0.0.1:5173,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002"
    )

    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Redis/Celery (PostgreSQL mode only)
    REDIS_URL: Optional[str] = None
    CELERY_BROKER_URL: Optional[str] = None

    # Storage
    EXPORT_DIR: Path = Path.home() / ".assisi-social" / "exports"
    DB_DIR: Path = Path.home() / ".assisi-social"

    # Security
    PMS_SERVICE_TOKEN: Optional[str] = None
    INTERNAL_SERVICE_TOKEN: Optional[str] = None

    # Feature kill-switches
    CRM_ENFORCE_CONSENT: bool = False

    # Audit log retention. 0 disables the retention sweeper.
    AUDIT_RETENTION_DAYS: int = 365

    @property
    def is_postgresql_mode(self) -> bool:
        return self.DATABASE_URL is not None

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in {"production", "prod"}

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def effective_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        db_path = self.DB_DIR / "pms.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        if "pytest" in sys.modules:
            return self

        prod = _is_production(self.APP_ENV)

        if not self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
            msg = (
                "JWT_SECRET_KEY must be at least 32 characters. "
                "Generate one with `python -c \"import secrets; print(secrets.token_urlsafe(64))\"`."
            )
            if prod:
                raise ValueError(msg)
            logger.warning("%s (APP_ENV=%s — dev warn only)", msg, self.APP_ENV)

        if self.JWT_SECRET_KEY in LEAKED_DEV_JWT_SECRETS:
            msg = "JWT_SECRET_KEY matches a known leaked development value. Rotate it before going to production."
            if prod:
                raise ValueError(msg)
            logger.warning("%s (APP_ENV=%s — dev warn only)", msg, self.APP_ENV)

        if self.INTERNAL_SERVICE_TOKEN and self.INTERNAL_SERVICE_TOKEN in LEAKED_SERVICE_TOKENS:
            msg = "INTERNAL_SERVICE_TOKEN matches a known leaked development value. Rotate it before going to production."
            if prod:
                raise ValueError(msg)
            logger.warning("%s (APP_ENV=%s — dev warn only)", msg, self.APP_ENV)

        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()


if settings.is_production and not settings.INTERNAL_SERVICE_TOKEN:
    raise RuntimeError(
        "INTERNAL_SERVICE_TOKEN is required in production (APP_ENV=production). "
        "Set it to a securely-generated secret."
    )
