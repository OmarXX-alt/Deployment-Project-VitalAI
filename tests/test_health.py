def test_health_returns_ok(client):
    """Health endpoint should always respond without DB dependencies."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
