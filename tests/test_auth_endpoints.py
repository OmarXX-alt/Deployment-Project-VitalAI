from __future__ import annotations

from main.application import auth as auth_module


def test_register_success(client, monkeypatch):
    captured = {}

    def fake_register_user(
        display_name,
        email,
        password,
        jwt_secret,
        jwt_expiry_hours,
        daily_calorie_target=None,
        hydration_goal=None,
        wellness_goal=None,
    ):
        captured["daily_calorie_target"] = daily_calorie_target
        captured["hydration_goal"] = hydration_goal
        captured["wellness_goal"] = wellness_goal
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
            "daily_calorie_target": 2200,
            "hydration_goal": 2500,
            "wellness_goal": "better_sleep",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["display_name"] == "Alex"
    assert "token" not in data
    cookie_headers = response.headers.getlist("Set-Cookie")
    auth_cookie = next(
        (header for header in cookie_headers if "vitalai_auth" in header),
        None,
    )
    assert auth_cookie is not None
    assert "HttpOnly" in auth_cookie
    assert captured["daily_calorie_target"] == 2200
    assert captured["hydration_goal"] == 2500
    assert captured["wellness_goal"] == "better_sleep"


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
    assert data["display_name"] == "Alex"
    assert "token" not in data
    cookie_headers = response.headers.getlist("Set-Cookie")
    auth_cookie = next(
        (header for header in cookie_headers if "vitalai_auth" in header),
        None,
    )
    assert auth_cookie is not None
    assert "HttpOnly" in auth_cookie


def test_login_invalid_json(client):
    response = client.post(
        "/api/login",
        data="not-json",
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "invalid_json"
