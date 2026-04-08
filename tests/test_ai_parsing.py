from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from main.application import dashboard as dashboard_module


def _make_token(client, user_id="user-123"):
    secret = client.application.config["JWT_SECRET"]
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _auth_headers(client, user_id="user-123"):
    token = _make_token(client, user_id=user_id)
    return {"Authorization": f"Bearer {token}"}


def _setup_context(monkeypatch):
    monkeypatch.setattr(dashboard_module, "get_db", lambda: object())
    monkeypatch.setattr(
        dashboard_module, "get_meal_context", lambda *a: {}
    )
    monkeypatch.setattr(
        dashboard_module, "get_workout_context", lambda *a: {}
    )
    monkeypatch.setattr(
        dashboard_module, "get_sleep_context", lambda *a: {}
    )
    monkeypatch.setattr(
        dashboard_module, "get_hydration_context", lambda *a: {}
    )
    monkeypatch.setattr(
        dashboard_module, "get_mood_context", lambda *a: {}
    )


def test_weekly_insights_valid_json(client, monkeypatch):
    _setup_context(monkeypatch)
    response_json = (
        "{\"positives\": [\"a\", \"b\"], "
        "\"concern\": \"c\", "
        "\"suggestions\": [\"d\", \"e\", \"f\"]}"
    )
    monkeypatch.setattr(
        dashboard_module,
        "call_gemini",
        lambda *args, **kwargs: response_json,
    )

    response = client.get(
        "/api/insights/weekly",
        headers=_auth_headers(client),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["positives"] == ["a", "b"]
    assert data["concern"] == "c"
    assert data["suggestions"] == ["d", "e", "f"]


def test_weekly_insights_invalid_json(client, monkeypatch):
    _setup_context(monkeypatch)
    monkeypatch.setattr(
        dashboard_module,
        "call_gemini",
        lambda *args, **kwargs: "not-json",
    )

    response = client.get(
        "/api/insights/weekly",
        headers=_auth_headers(client),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["error"] == "insight_unavailable"


def test_weekly_insights_missing_keys(client, monkeypatch):
    _setup_context(monkeypatch)
    response_json = "{\"positives\": [], \"concern\": \"x\"}"
    monkeypatch.setattr(
        dashboard_module,
        "call_gemini",
        lambda *args, **kwargs: response_json,
    )

    response = client.get(
        "/api/insights/weekly",
        headers=_auth_headers(client),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["error"] == "insight_unavailable"
