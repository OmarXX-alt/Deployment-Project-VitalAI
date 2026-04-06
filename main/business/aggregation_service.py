from __future__ import annotations

from main.persistence.extensions import mongo
from main.persistence.models import UserPublic


def build_context(user_id: str, log_types=None, days: int = 7) -> dict:
    """Build the canonical context schema for AI prompts and analytics.

    Purpose:
        Aggregate recent logs and profile data into a standardized context.
    Expected Input types:
        user_id (str), log_types (Optional[list[str]]), days (int).
    Expected Output:
        dict containing the canonical context schema.

    # TODO: [Logic-Issue-010]
    Implementation checklist:
        1. load logs by type
        2. compute daily totals and trends
        3. load profile targets
        4. return canonical context schema

    This is the agreed output schema. Member 2 builds prompts against this shape.
    Any change must be communicated via a GitHub issue comment before implementation.
    """
    _ = (mongo, UserPublic)
    return {
        "workouts": {"entries": [], "by_day": {}},
        "meals": {"entries": [], "daily_totals": {}, "today_total_kcal": 0},
        "sleep": {
            "entries": [],
            "avg_duration": 0.0,
            "avg_quality": 0.0,
            "trend": "insufficient_data",
        },
        "hydration": {"entries": [], "daily_totals": {}, "today_total_ml": 0},
        "mood": {"entries": [], "avg_score": 0.0, "trend": "insufficient_data"},
        "profile": {
            "daily_calorie_target": None,
            "hydration_goal": None,
            "wellness_goal": None,
        },
    }


def get_dashboard_data(user_id: str) -> dict:
    """Return dashboard data for the authenticated user.

    Purpose:
        Provide the aggregated dashboard payload for the UI.
    Expected Input types:
        user_id (str).
    Expected Output:
        dict with dashboard metrics and recent entries.

    # TODO: [Logic-Issue-012]
    """
    _ = mongo
    return {
        "workouts": [],
        "meals": [],
        "sleep": [],
        "hydration": [],
        "mood": [],
        "today_total_kcal": 0,
        "hydration_goal": None,
        "hydration_pct": None,
        "wellness_insights": None,
    }
