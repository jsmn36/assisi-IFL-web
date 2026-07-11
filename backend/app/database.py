"""
Hybrid Database Configuration
Supports both SQLite (default) and PostgreSQL (optional)
"""

import logging
import sys

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, with_loader_criteria

from app.config import settings
from app.core.tenant_context import get_tenant, is_bypassing

logger = logging.getLogger(__name__)

# Detect if running tests
IS_TESTING = "pytest" in sys.modules

# Backward-compatible module-level DATABASE_URL
DATABASE_URL = settings.effective_database_url


def _create_engine():
    """Create the appropriate engine based on configuration."""
    url = settings.effective_database_url

    if IS_TESTING:
        # Force SQLite for tests
        test_url = "sqlite:///./test.db"
        logger.info("Running tests - Forcing SQLite test database")
        eng = create_engine(
            test_url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            echo=False,
        )
        return eng, "SQLite", test_url

    if settings.is_postgresql_mode:
        logger.info("Using PostgreSQL database")
        eng = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )
        return eng, "PostgreSQL", url
    else:
        logger.info("Using SQLite database")
        eng = create_engine(
            url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
            echo=False,
        )

        # Enable WAL mode for SQLite (better concurrent read performance)
        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        return eng, "SQLite", url


engine, db_type, DATABASE_URL = _create_engine()

# Import shared Base used by all models so metadata is consistent
from app.db.base import Base  # noqa: E402

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """Dependency to provide a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Tenant isolation: session-level row filter ────────────────────────────
# Registered once per process. On every ORM select/update/delete that touches
# a model inheriting TenantScopedMixin, inject `tenant_id = <current>` so a
# handler cannot accidentally leak across tenants. The filter is skipped when
# (a) no tenant is set in context (pre-auth queries, Alembic, scripts) or
# (b) `bypass_tenant_filter()` is active (migrations, cross-tenant schedulers).
_TENANT_FILTER_FLAG = "_pms_tenant_filter_applied"


@event.listens_for(Session, "do_orm_execute")
def _apply_tenant_filter(execute_state):
    # Skip internal relationship loads re-using a parent statement — the
    # parent already applied the filter.
    if execute_state.is_relationship_load:
        return

    if not (
        execute_state.is_select
        or execute_state.is_update
        or execute_state.is_delete
    ):
        return

    if is_bypassing():
        return

    tenant_id = get_tenant()
    if tenant_id is None:
        return

    # Defer import to avoid circular refs at module-init time.
    from app.models.mixins import TenantScopedMixin

    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            TenantScopedMixin,
            lambda cls: cls.tenant_id == tenant_id,
            include_aliases=True,
        )
    )


@event.listens_for(Session, "before_flush")
def _apply_tenant_on_insert(session, flush_context, instances):
    """Autofill ``tenant_id`` on new rows from the current tenant context."""
    from app.models.mixins import TenantScopedMixin

    tenant_id = get_tenant()
    if tenant_id is None or is_bypassing():
        return

    for obj in session.new:
        if isinstance(obj, TenantScopedMixin) and getattr(obj, "tenant_id", None) is None:
            obj.tenant_id = tenant_id


def init_db():
    """Create all tables from metadata."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized (%s)", db_type)
    return db_type


def get_db_info():
    """Return database connection information."""
    display_url = DATABASE_URL
    if "@" in str(DATABASE_URL):
        display_url = str(DATABASE_URL).split("@")[-1]
    return {
        "database_type": db_type,
        "database_url": str(display_url),
        "dialect": engine.dialect.name,
    }


def get_database_url():
    """Return the database URL (backward-compat helper)."""
    import os

    return os.getenv("DATABASE_URL", "sqlite:///./pms.db")


def get_connection_pool_status(eng=None):
    """Get connection pool statistics."""
    target = eng or engine
    pool = target.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow(),
    }
