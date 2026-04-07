def test_index_route_returns_html(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.data.lower()
    assert b"doctype html" in body
    assert b"vitalai" in body


def test_health_route_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
