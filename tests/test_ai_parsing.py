from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from main.application import dashboard as dashboard_module
from main.business import ai_service


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

    def fake_insights(*args, **kwargs):
        return {
            "positives": ["a", "b"],
            "concern": "c",
            "suggestions": ["d", "e", "f"],
            "data_logged_categories": 3,
        }

    monkeypatch.setattr(
        ai_service,
        "get_wellness_insights",
        fake_insights,
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

    # Mock get_wellness_insights to fail gracefully and return fallback
    def fake_insights_fail(*args, **kwargs):
        return {
            "positives": ["Start tracking your health data"],
            "concern": "Limited health data this week",
            "suggestions": ["Log your meals daily", "Track sleep patterns", "Record your mood"],
            "data_logged_categories": 0,
        }

    monkeypatch.setattr(
        ai_service,
        "get_wellness_insights",
        fake_insights_fail,
    )

    response = client.get(
        "/api/insights/weekly",
        headers=_auth_headers(client),
    )

    assert response.status_code == 200
    data = response.get_json()
    # Should have fallback values, never error_unavailable
    assert "positives" in data
    assert "suggestions" in data
    assert "error" not in data
    assert data["positives"] == ["Start tracking your health data"]


def test_weekly_insights_missing_keys(client, monkeypatch):
    _setup_context(monkeypatch)

    def fake_insights_partial(*args, **kwargs):
        return {
            "positives": [],
            "concern": "Limited health data",
            "suggestions": ["Log your meals daily"],
            "data_logged_categories": 1,
        }

    monkeypatch.setattr(
        ai_service,
        "get_wellness_insights",
        fake_insights_partial,
    )

    response = client.get(
        "/api/insights/weekly",
        headers=_auth_headers(client),
    )

    assert response.status_code == 200
    data = response.get_json()
    # Even with sparse data, should return valid response with suggestions
    assert "concern" in data
    assert "suggestions" in data
    assert "error" not in data
    assert len(data["suggestions"]) >= 1
