from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_database_info():
    response = client.get("/database/info")
    assert response.status_code == 200
    assert response.json()["db"] == "postgres"
