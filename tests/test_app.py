def test_index_route_returns_json(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.get_json() == {"message": "Welcome to VitalAI"}


def test_health_route_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
