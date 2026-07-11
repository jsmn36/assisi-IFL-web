from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Test root endpoint returns correct data"""
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Assisi Social API"
    assert data["version"] == "1.0.0"
    assert "database" in data
    assert data["status"] == "running"


def test_health_check():
    """Test health check endpoint.

    /health returns the same shape as /ready: a structured probe payload
    with a top-level ``status`` (ok | degraded | unhealthy) plus a per-
    component breakdown. In test mode Redis/Celery are unavailable so
    the overall status is ``degraded`` but the database probe must pass.
    """
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in {"ok", "degraded", "unhealthy"}
    assert "components" in data
    assert data["components"]["database"]["status"] == "ok"


def test_database_info():
    """Test database info endpoint"""
    response = client.get("/database/info")
    assert response.status_code == 200

    data = response.json()
    assert "database_type" in data
    assert "database_url" in data
    assert "dialect" in data

    # In tests, should use SQLite
    assert data["dialect"] == "sqlite"


def test_cors_headers():
    """Test CORS headers are set correctly"""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
