from __future__ import annotations

import json

from flask import Blueprint, current_app, g, jsonify

from main.ai.gemini_client import call_gemini
from main.business import aggregation_service
from main.business.utils.aggregation import (
    get_hydration_context,
    get_meal_context,
    get_mood_context,
    get_sleep_context,
    get_workout_context,
)
from main.persistence.db import get_db
from main.server.middleware.auth import require_auth

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/api/dashboard")
@require_auth
def dashboard():
    # TODO: [Logic-Issue-012]
    try:
        data = aggregation_service.get_dashboard_data(g.user_id)
        return jsonify(data), 200
    except Exception as e:
        current_app.logger.error("Dashboard error: %s", e)
        return jsonify({"error": "Failed to load dashboard"}), 500


@dashboard_bp.get("/api/insights/weekly")
@require_auth
def weekly_insights():
    # TODO: [Logic-Issue-014]
    fallback = {
        "positives": [],
        "concern": None,
        "suggestions": [],
        "error": "insight_unavailable",
    }
    try:
        db = get_db()
        meal_ctx = get_meal_context(g.user_id, db)
        workout_ctx = get_workout_context(g.user_id, db)
        sleep_ctx = get_sleep_context(g.user_id, db)
        hydration_ctx = get_hydration_context(g.user_id, db)
        mood_ctx = get_mood_context(g.user_id, db)

        prompt_lines = [
            "You are a wellness analyst. Return only valid JSON. "
            "No explanation, no markdown.",
            "Return exactly 2 positives, 1 concern, 3 suggestions.",
            "JSON schema: {\"positives\": [\"...\", \"...\"], "
            "\"concern\": \"...\", "
            "\"suggestions\": [\"...\", \"...\", \"...\"]}",
            "",
            "MEALS:",
            json.dumps(meal_ctx),
            "WORKOUTS:",
            json.dumps(workout_ctx),
            "SLEEP:",
            json.dumps(sleep_ctx),
            "HYDRATION:",
            json.dumps(hydration_ctx),
            "MOOD:",
            json.dumps(mood_ctx),
        ]
        prompt = "\n".join(prompt_lines)
        response_text = call_gemini(prompt, timeout=8)
        if not response_text:
            return jsonify(fallback), 200
        payload = json.loads(response_text)
        if not isinstance(payload, dict):
            return jsonify(fallback), 200
        required = {"positives", "concern", "suggestions"}
        if not required.issubset(payload.keys()):
            return jsonify(fallback), 200
        return jsonify(payload), 200
    except json.JSONDecodeError:
        return jsonify(fallback), 200
    except Exception as exc:
        current_app.logger.warning("Weekly insights failed: %s", exc)
        return jsonify(fallback), 200
