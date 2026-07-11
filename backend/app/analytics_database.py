"""
Analytics Database Configuration
Separate database for analytics metrics, optimized for reads and decoupled from PMS.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings
import sys
import logging

logger = logging.getLogger(__name__)

# Detect if running tests
IS_TESTING = "pytest" in sys.modules


class AnalyticsBase(DeclarativeBase):
    """Base class for all Analytics SQLAlchemy models"""

    pass


def _get_analytics_url():
    """Resolve the analytics database URL."""
    if IS_TESTING:
        return "sqlite:///./analytics_test.db"
    # In production, use a separate analytics DB if configured,
    # otherwise fall back to the main database URL.
    import os

    url = os.getenv("ANALYTICS_DATABASE_URL")
    if url:
        return url
    return settings.effective_database_url


ANALYTICS_DATABASE_URL = _get_analytics_url()

if IS_TESTING:
    logger.info("Running tests - Forcing SQLite test database for analytics")
    analytics_engine = create_engine(
        ANALYTICS_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=False,
    )
elif settings.is_postgresql_mode:
    logger.info("Using PostgreSQL for analytics")
    analytics_engine = create_engine(
        ANALYTICS_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )
else:
    logger.info("Using SQLite for analytics")
    analytics_engine = create_engine(
        ANALYTICS_DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=False,
    )

AnalyticsSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=analytics_engine,
)


def get_analytics_db():
    db = AnalyticsSessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_analytics_db():
    AnalyticsBase.metadata.create_all(bind=analytics_engine)
    logger.info("Analytics Database initialized")


def get_analytics_db_url():
    return ANALYTICS_DATABASE_URL


def get_pms_db_url():
    """Helper to expose PMS database URL"""
    from app.database import DATABASE_URL

    return DATABASE_URL
