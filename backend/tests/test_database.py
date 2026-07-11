"""
Test database configuration and hybrid mode
"""
from app.database import get_db_info, init_db
import os


def test_database_info_structure():
    """Test database info returns correct structure"""
    info = get_db_info()

    assert "database_type" in info
    assert "database_url" in info
    assert "dialect" in info

    assert info["database_type"] in ["SQLite", "PostgreSQL"]


def test_sqlite_mode_default():
    """Test SQLite is used when DATABASE_URL not set"""
    # Save original DATABASE_URL
    original = os.environ.get("DATABASE_URL")

    try:
        # Remove DATABASE_URL
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Database should default to SQLite
        # (This test assumes test environment uses SQLite)
        info = get_db_info()
        assert "sqlite" in info["database_url"].lower()

    finally:
        # Restore original DATABASE_URL
        if original:
            os.environ["DATABASE_URL"] = original


from app.database import get_db


def test_get_db_generator():
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    db.close()


import os
from app import database


def test_database_url_override(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")
    url = database.get_database_url()
    assert "sqlite" in url


def test_engine_creation():
    engine = database.engine
    assert engine is not None


def test_session_close():
    db_gen = database.get_db()
    db = next(db_gen)
    try:
        assert db is not None
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


from app.database import init_db, get_db_info, engine


def test_init_db():
    result = init_db()
    assert result in ["SQLite", "PostgreSQL"]


def test_get_db_info():
    info = get_db_info()
    assert "database_type" in info
    assert "database_url" in info
    assert "dialect" in info
    assert info["dialect"] == engine.dialect.name
