from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_lifecycle():
    res = client.post(
        "/uploads",
        data={"title": "Test post", "content": "hello", "type": "image", "hashtags": "#t"},
        files={"file": ("pic.png", b"\x89PNGfakeimage", "image/png")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Test post"
    assert body["media_url"].endswith(f"/uploads/{body['id']}/media")

    listed = client.get("/uploads")
    assert listed.status_code == 200
    assert any(u["id"] == body["id"] for u in listed.json())

    media = client.get(f"/uploads/{body['id']}/media")
    assert media.status_code == 200
    assert media.content == b"\x89PNGfakeimage"
    assert media.headers["content-type"] == "image/png"

    deleted = client.delete(f"/uploads/{body['id']}")
    assert deleted.status_code == 200
    assert client.delete(f"/uploads/{body['id']}").status_code == 404


def test_upload_without_file():
    res = client.post("/uploads", data={"title": "Notice only", "type": "notice"})
    assert res.status_code == 200
    body = res.json()
    assert body["media_url"] is None
    assert client.get(f"/uploads/{body['id']}/media").status_code == 404
    client.delete(f"/uploads/{body['id']}")


def test_upload_https_forwarded():
    res = client.post(
        "/uploads",
        data={"title": "https"},
        files={"file": ("a.txt", b"x", "text/plain")},
        headers={"x-forwarded-proto": "https"},
    )
    assert res.json()["media_url"].startswith("https://")
    client.delete(f"/uploads/{res.json()['id']}")


def test_media_not_found():
    assert client.get("/uploads/999999/media").status_code == 404
