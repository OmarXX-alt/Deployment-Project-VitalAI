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


def _require_datetime(value: Any, field_name: str) -> datetime:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _require_int(value: Any, field_name: str) -> int:
    if value is None:
        raise ValueError(f"{field_name} is required")
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


def create_sleep_log(
    user_id: ObjectId,
    sleep_start: datetime,
    sleep_end: datetime,
    quality: int,
    logged_at: datetime | None = None,
    ai_reaction: dict[str, object] | None = None,
) -> dict[str, object]:
    """
    Create a sleep log document ready for MongoDB insertion.

    Parameters:
        user_id: MongoDB ObjectId of the user.
        sleep_start: Sleep start timestamp.
        sleep_end: Sleep end timestamp.
        quality: Sleep quality rating.
        logged_at: Optional timestamp; defaults to now (UTC).
        ai_reaction: Optional AI reaction document.
    """
    user_value = _require_object_id(user_id, "user_id")
    start_value = _require_datetime(sleep_start, "sleep_start")
    end_value = _require_datetime(sleep_end, "sleep_end")
    if end_value <= start_value:
        raise ValueError("sleep_end must be after sleep_start")
    quality_value = _require_int(quality, "quality")
    duration_hrs = round((end_value - start_value).total_seconds() / 3600, 2)
    logged_value = _ensure_datetime(logged_at, "logged_at")
    reaction_value = _validate_ai_reaction(ai_reaction)

    return {
        "user_id": user_value,
        "sleep_start": start_value,
        "sleep_end": end_value,
        "duration_hrs": duration_hrs,
        "quality": quality_value,
        "logged_at": logged_value,
        "ai_reaction": reaction_value,
    }
