from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


def _require_object_id(value: Any, field_name: str) -> ObjectId:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, ObjectId):
        raise ValueError(f"{field_name} must be an ObjectId")
    return value


def _require_str(value: Any, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_number(value: Any, field_name: str) -> float:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number")
    return float(value)


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


def _validate_ai_reaction(ai_reaction: dict[str, object] | None) -> dict[str, object] | None:
    if ai_reaction is None:
        return None
    if not isinstance(ai_reaction, dict):
        raise ValueError("ai_reaction must be a dict with keys: type, message, tags")
    reaction_type = ai_reaction.get("type")
    message = ai_reaction.get("message")
    tags = ai_reaction.get("tags")
    if not isinstance(reaction_type, str):
        raise ValueError("ai_reaction.type must be a string")
    if not isinstance(message, str):
        raise ValueError("ai_reaction.message must be a string")
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise ValueError("ai_reaction.tags must be a list of strings")
    return {"type": reaction_type, "message": message, "tags": list(tags)}


def create_workout_log(
    user_id: ObjectId,
    exercise_type: str,
    duration_min: int | float,
    intensity: str,
    sets: int | None = None,
    reps: int | None = None,
    logged_at: datetime | None = None,
    ai_reaction: dict[str, object] | None = None,
) -> dict[str, object]:
    """
    Create a workout log document ready for MongoDB insertion.

    Parameters:
        user_id: MongoDB ObjectId of the user.
        exercise_type: Workout activity type (for example, Running).
        duration_min: Workout duration in minutes.
        intensity: Intensity label (low, medium, high).
        sets: Optional number of sets.
        reps: Optional number of reps.
        logged_at: Optional timestamp; defaults to now (UTC).
        ai_reaction: Optional AI reaction document.
    """
    user_value = _require_object_id(user_id, "user_id")
    exercise_value = _require_str(exercise_type, "exercise_type")
    duration_value = _require_number(duration_min, "duration_min")
    intensity_value = _require_str(intensity, "intensity")
    sets_value = _optional_int(sets, "sets")
    reps_value = _optional_int(reps, "reps")
    logged_value = _ensure_datetime(logged_at, "logged_at")
    reaction_value = _validate_ai_reaction(ai_reaction)

    return {
        "user_id": user_value,
        "exercise_type": exercise_value,
        "duration_min": duration_value,
        "sets": sets_value,
        "reps": reps_value,
        "intensity": intensity_value,
        "logged_at": logged_value,
        "ai_reaction": reaction_value,
    }
