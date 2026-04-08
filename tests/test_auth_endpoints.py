from __future__ import annotations

from main.application import auth as auth_module


def test_register_success(client, monkeypatch):
    def fake_register_user(
        display_name, email, password, jwt_secret, jwt_expiry_hours
    ):
        return (
            {
                "token": "test-token",
                "user_id": "user-1",
                "display_name": display_name,
            },
            201,
        )

    monkeypatch.setattr(
        auth_module.auth_service, "register_user", fake_register_user
    )

    response = client.post(
        "/api/register",
        json={
            "display_name": "Alex",
            "email": "alex@example.com",
            "password": "password1!",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["token"] == "test-token"
    assert data["display_name"] == "Alex"


def test_register_validation_error(client):
    response = client.post("/api/register", json={"display_name": "A"})

    assert response.status_code == 422
    data = response.get_json()
    assert data["error"] == "validation_error"
    assert data["fields"]


def test_login_success(client, monkeypatch):
    def fake_login_user(email, password, jwt_secret, jwt_expiry_hours):
        return ({"token": "login-token", "display_name": "Alex"}, 200)

    monkeypatch.setattr(
        auth_module.auth_service, "login_user", fake_login_user
    )

    response = client.post(
        "/api/login",
        json={"email": "alex@example.com", "password": "password1!"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["token"] == "login-token"
    assert data["display_name"] == "Alex"


def test_login_invalid_json(client):
    response = client.post(
        "/api/login",
        data="not-json",
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "invalid_json"
