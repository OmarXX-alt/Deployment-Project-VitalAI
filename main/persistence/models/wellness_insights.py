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


def _require_str_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    return list(value)


def _ensure_datetime(value: datetime | None, field_name: str) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def create_wellness_insight(
    user_id: ObjectId,
    positives: list[str],
    concern: str,
    suggestions: list[str],
    generated_at: datetime | None = None,
) -> dict[str, object]:
    """
    Create a wellness insight document ready for MongoDB insertion.

    Parameters:
        user_id: MongoDB ObjectId of the user.
        positives: Positive trends or wins.
        concern: Primary concern to highlight.
        suggestions: Suggested actions or improvements.
        generated_at: Optional timestamp; defaults to now (UTC).
    """
    user_value = _require_object_id(user_id, "user_id")
    positives_value = _require_str_list(positives, "positives")
    concern_value = _require_str(concern, "concern")
    suggestions_value = _require_str_list(suggestions, "suggestions")
    generated_value = _ensure_datetime(generated_at, "generated_at")

    return {
        "user_id": user_value,
        "positives": positives_value,
        "concern": concern_value,
        "suggestions": suggestions_value,
        "generated_at": generated_value,
    }
