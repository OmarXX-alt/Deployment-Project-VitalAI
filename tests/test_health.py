"""Test suite for health and liveness probes."""


def test_health_returns_ok(client):
    """Health endpoint must pass unconditionally without db dependencies."""
    # FIX: Asserts that GET /health guarantees a 200 (Rule 3)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
