def test_create_guest(client):
    response = client.post(
        "/api/v1/guests",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-1234",
        },
    )
    assert response.status_code == 201
    assert response.json()["full_name"] == "John Doe"


def test_search_guests(client, test_db):
    response = client.get("/api/v1/guests?query=Doe")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
