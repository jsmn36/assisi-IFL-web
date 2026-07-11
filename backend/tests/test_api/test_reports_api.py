def test_list_report_templates(client):
    response = client.get("/api/v1/reports/templates")
    assert response.status_code == 200
    body = response.json()
    assert "templates" in body
    assert body["count"] >= 20


def test_get_template_not_found(client):
    response = client.get("/api/v1/reports/templates/not-a-template")
    assert response.status_code == 404


def test_generate_template_with_invalid_range(client):
    response = client.get(
        "/api/v1/reports/templates/revenue_summary/generate",
        params={
            "property_id": 1,
            "start_date": "2026-01-10",
            "end_date": "2026-01-01",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "end_date must be after start_date"


def test_generate_template_success(client):
    response = client.get(
        "/api/v1/reports/templates/revenue_summary/generate",
        params={
            "property_id": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["template"]["template_id"] == "revenue_summary"
    assert body["period"]["start_date"] == "2026-01-01"
    assert "summary" in body


def test_revenue_summary_endpoint(client):
    response = client.get(
        "/api/v1/reports/revenue/summary",
        params={
            "property_id": 1,
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["template"]["template_id"] == "revenue_summary"
    assert "recognized_revenue" in body["summary"]
