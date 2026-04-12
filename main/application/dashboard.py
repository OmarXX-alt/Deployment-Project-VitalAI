from __future__ import annotations

import json

from flask import Blueprint, current_app, g, jsonify

from main.ai.gemini_client import call_gemini
from main.business import aggregation_service, ai_service
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
    try:
        db = get_db()
        
        # Gather all context from each domain (even if sparse)
        meal_ctx = get_meal_context(g.user_id, db)
        workout_ctx = get_workout_context(g.user_id, db)
        sleep_ctx = get_sleep_context(g.user_id, db)
        hydration_ctx = get_hydration_context(g.user_id, db)
        mood_ctx = get_mood_context(g.user_id, db)
        
        current_app.logger.info(f"Insights - Meal: {meal_ctx}")
        current_app.logger.info(f"Insights - Workout: {workout_ctx}")
        current_app.logger.info(f"Insights - Sleep: {sleep_ctx}")
        current_app.logger.info(f"Insights - Hydration: {hydration_ctx}")
        current_app.logger.info(f"Insights - Mood: {mood_ctx}")
        
        # Combine all data (aggregate as much as possible)
        aggregated_context = {
            "meals": meal_ctx,
            "workouts": workout_ctx,
            "sleep": sleep_ctx,
            "hydration": hydration_ctx,
            "mood": mood_ctx,
        }
        
        # Generate insights from whatever data is available
        insights = ai_service.get_wellness_insights(
            user_id=g.user_id,
            context=aggregated_context,
            timeout_seconds=15
        )
        
        current_app.logger.info(f"Wellness Insights result: {insights}")
        
        # Always return insights (business layer never returns None now)
        if insights is None:
            # Fallback if something really goes wrong
            current_app.logger.error("Wellness insights returned None unexpectedly")
            return jsonify({
                "positives": ["You're on your wellness journey"],
                "concern": "Haven't collected much data yet",
                "suggestions": ["Start by logging your meals", "Track your sleep patterns", "Record your mood daily"],
                "note": "Keep logging to get better insights!"
            }), 200
        
        return jsonify(insights), 200
        
    except Exception as exc:
        current_app.logger.error(f"Weekly insights exception: {exc}", exc_info=True)
        return jsonify({
            "positives": ["You're building healthy habits"],
            "concern": "Unable to analyze data right now",
            "suggestions": ["Keep logging your health data", "Check back tomorrow", "Stay consistent with tracking"],
        }), 200
