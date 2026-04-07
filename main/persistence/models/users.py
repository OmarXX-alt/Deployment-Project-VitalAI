from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _require_str(value: Any, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def _optional_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    return value


def _ensure_datetime(value: datetime | None, field_name: str) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def create_user(
    email: str,
    password_hash: str,
    display_name: str,
    daily_calorie_target: int | None = None,
    hydration_goal_ml: int | None = None,
    wellness_goal: str | None = None,
    created_at: datetime | None = None,
) -> dict[str, object]:
    """
    Create a user document ready for MongoDB insertion.

    Parameters:
        email: Unique user email address.
        password_hash: Password hash for authentication.
        display_name: Friendly name shown in the UI.
        daily_calorie_target: Optional daily calorie target in kcal.
        hydration_goal_ml: Optional daily hydration goal in milliliters.
        wellness_goal: Optional wellness goal text.
        created_at: Optional creation timestamp; defaults to now (UTC).
    """
    email_value = _require_str(email, "email")
    password_value = _require_str(password_hash, "password_hash")
    display_value = _require_str(display_name, "display_name")
    calorie_target = _optional_int(
        daily_calorie_target, "daily_calorie_target"
    )
    hydration_goal = _optional_int(hydration_goal_ml, "hydration_goal_ml")
    if wellness_goal is not None and not isinstance(wellness_goal, str):
        raise ValueError("wellness_goal must be a string")
    created_value = _ensure_datetime(created_at, "created_at")

    return {
        "email": email_value,
        "password_hash": password_value,
        "display_name": display_value,
        "daily_calorie_target": calorie_target,
        "hydration_goal_ml": hydration_goal,
        "wellness_goal": wellness_goal,
        "created_at": created_value,
    }
