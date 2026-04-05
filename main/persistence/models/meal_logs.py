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


def create_meal_log(
    user_id: ObjectId,
    meal_name: str,
    calories: int | float,
    meal_type: str,
    logged_at: datetime | None = None,
    ai_reaction: dict[str, object] | None = None,
) -> dict[str, object]:
    """
    Create a meal log document ready for MongoDB insertion.

    Parameters:
        user_id: MongoDB ObjectId of the user.
        meal_name: Name or description of the meal.
        calories: Total calories for the meal.
        meal_type: Meal type label (breakfast, lunch, dinner, snack).
        logged_at: Optional timestamp; defaults to now (UTC).
        ai_reaction: Optional AI reaction document.
    """
    user_value = _require_object_id(user_id, "user_id")
    name_value = _require_str(meal_name, "meal_name")
    calories_value = _require_number(calories, "calories")
    type_value = _require_str(meal_type, "meal_type")
    logged_value = _ensure_datetime(logged_at, "logged_at")
    reaction_value = _validate_ai_reaction(ai_reaction)

    return {
        "user_id": user_value,
        "meal_name": name_value,
        "calories": calories_value,
        "meal_type": type_value,
        "logged_at": logged_value,
        "ai_reaction": reaction_value,
    }
