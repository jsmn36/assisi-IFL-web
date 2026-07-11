import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401  ensure models are registered
from app.db.base import Base

os.environ["CM_DATABASE_URL"] = "sqlite:///./test_cm.db"


@pytest.fixture(scope="session", autouse=True)
def _default_tenant_scope():
    """Set tenant_scope(1) for the whole pytest session by default.

    The multi-tenant rollout makes ``tenant_id`` NOT NULL on every domain
    table; the SQLAlchemy ``before_flush`` hook auto-stamps it from the
    current context. Pre-existing tests don't supply a tenant context, so
    without this fixture they all hit ``NOT NULL constraint failed``.

    Session-scoped (vs function-scoped) so module-level fixtures that
    seed data also see the context.

    Tests that need to exercise multi-tenant isolation (or no-context
    behavior) override this with their own ``tenant_scope(...)`` /
    ``bypass_tenant_filter()`` blocks — ContextVar nesting handles that
    correctly.
    """
    from app.core.tenant_context import tenant_scope

    with tenant_scope(1):
        yield


@pytest.fixture(scope="function")
def test_db():
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def admin_token(test_db):
    """Generate a mock admin token and override get_current_user for the test"""
    from app.core.security import create_access_token
    from app.api.dependencies import get_current_user
    from app.models.user import User
    from app.main import app

    mock_user = User(
        id=1,
        username="admin",
        email="admin@test.com",
        role="admin",
        hashed_password="x",
        is_active=True,
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    token = create_access_token(data={"sub": "1", "role": "admin"})
    yield token
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="function")
def test_user_token(test_db):
    """Generate a mock regular user token for testing"""
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": "2", "role": "staff"})
    return token
