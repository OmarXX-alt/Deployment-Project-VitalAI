from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from main.application import logs as logs_module


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


def _setup_ai(monkeypatch):
    monkeypatch.setattr(logs_module, "get_db", lambda: object())
    monkeypatch.setattr(
        logs_module, "call_gemini", lambda prompt: "AI response"
    )
    monkeypatch.setattr(
        logs_module, "get_meal_context", lambda *args: {}
    )
    monkeypatch.setattr(
        logs_module, "get_workout_context", lambda *args: {}
    )
    monkeypatch.setattr(
        logs_module, "get_sleep_context", lambda *args: {}
    )
    monkeypatch.setattr(
        logs_module, "get_hydration_context", lambda *args: {}
    )
    monkeypatch.setattr(
        logs_module, "get_mood_context", lambda *args: {}
    )


def test_log_meal_success(client, monkeypatch):
    _setup_ai(monkeypatch)

    def fake_save_meal_log(user_id, meal_name, calories, meal_type, logged_at):
        return (
            {
                "meal_name": meal_name,
                "calories": calories,
                "meal_type": meal_type,
                "today_total_kcal": calories,
            },
            201,
        )

    monkeypatch.setattr(
        logs_module.log_service, "save_meal_log", fake_save_meal_log
    )

    response = client.post(
        "/api/logs/meal",
        headers=_auth_headers(client),
        json={
            "meal_name": "Oats",
            "calories": 300,
            "meal_type": "lunch",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["reaction"]["message"] == "AI response"


def test_log_workout_success(client, monkeypatch):
    _setup_ai(monkeypatch)

    def fake_save_workout_log(
        user_id,
        exercise_type,
        duration_minutes,
        sets,
        reps,
        intensity,
        logged_at,
    ):
        return (
            {
                "exercise_type": exercise_type,
                "duration_minutes": duration_minutes,
                "intensity": intensity,
                "sets": sets,
                "reps": reps,
            },
            201,
        )

    monkeypatch.setattr(
        logs_module.log_service, "save_workout_log", fake_save_workout_log
    )

    response = client.post(
        "/api/logs/workout",
        headers=_auth_headers(client),
        json={
            "exercise_type": "Run",
            "duration_minutes": 25,
            "intensity": "moderate",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["reaction"]["message"] == "AI response"


def test_log_sleep_success(client, monkeypatch):
    _setup_ai(monkeypatch)
    start = datetime.now(timezone.utc) - timedelta(hours=7)
    end = datetime.now(timezone.utc)

    def fake_save_sleep_log(user_id, sleep_start, sleep_end, quality_score):
        return (
            {
                "sleep_start": sleep_start.isoformat(),
                "sleep_end": sleep_end.isoformat(),
                "duration_minutes": 420,
                "quality_score": quality_score,
            },
            201,
        )

    monkeypatch.setattr(
        logs_module.log_service, "save_sleep_log", fake_save_sleep_log
    )

    response = client.post(
        "/api/logs/sleep",
        headers=_auth_headers(client),
        json={
            "sleep_start": start.isoformat(),
            "sleep_end": end.isoformat(),
            "quality_score": 4,
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["reaction"]["message"] == "AI response"


def test_log_hydration_success(client, monkeypatch):
    _setup_ai(monkeypatch)

    def fake_save_hydration_log(user_id, amount_ml, logged_at):
        return (
            {
                "amount_ml": amount_ml,
                "daily_total_ml": amount_ml,
                "pct_of_goal": 50.0,
            },
            201,
        )

    monkeypatch.setattr(
        logs_module.log_service, "save_hydration_log", fake_save_hydration_log
    )

    response = client.post(
        "/api/logs/hydration",
        headers=_auth_headers(client),
        json={"amount_ml": 500},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["reaction"]["message"] == "AI response"


def test_log_mood_success(client, monkeypatch):
    _setup_ai(monkeypatch)

    def fake_save_mood_log(user_id, mood_score, note):
        return (
            {
                "mood_score": mood_score,
                "note": note,
                "date": "2026-04-08",
            },
            201,
        )

    monkeypatch.setattr(
        logs_module.log_service, "save_mood_log", fake_save_mood_log
    )

    response = client.post(
        "/api/logs/mood",
        headers=_auth_headers(client),
        json={"mood_score": 1, "note": "Tough day"},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["reaction"]["message"] == "AI response"
    assert data["wellness_resource"] is not None
