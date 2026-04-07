from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify

from main.business import aggregation_service, ai_service
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
    context = aggregation_service.build_context(g.user_id, log_types=None, days=7)
    insights = ai_service.get_wellness_insights(
        g.user_id,
        context,
        current_app.config.get("GEMINI_API_KEY", ""),
        timeout_seconds=10,
    )

    if insights is None:
        return (
            jsonify(
                {
                    "positives": None,
                    "concern": None,
                    "suggestions": None,
                    "message": "Insights are temporarily unavailable. Please try again later.",
                }
            ),
            200,
        )

    return jsonify(insights), 200
