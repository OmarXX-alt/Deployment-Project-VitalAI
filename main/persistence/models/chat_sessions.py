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


def _ensure_datetime(value: datetime | None, field_name: str) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _validate_messages(
    messages: list[dict[str, object]],
) -> list[dict[str, object]]:
    if not isinstance(messages, list):
        raise ValueError("messages must be a list of dicts")
    validated: list[dict[str, object]] = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"messages[{index}] must be a dict")
        role = message.get("role")
        content = message.get("content")
        timestamp = message.get("timestamp")
        role_value = _require_str(role, f"messages[{index}].role")
        content_value = _require_str(content, f"messages[{index}].content")
        timestamp_value = _ensure_datetime(
            timestamp, f"messages[{index}].timestamp"
        )
        validated.append(
            {
                "role": role_value,
                "content": content_value,
                "timestamp": timestamp_value,
            }
        )
    return validated


def create_chat_session(
    user_id: ObjectId,
    messages: list[dict[str, object]],
    created_at: datetime | None = None,
) -> dict[str, object]:
    """
    Create a chat session document ready for MongoDB insertion.

    Parameters:
        user_id: MongoDB ObjectId of the user.
        messages: List of chat messages with role, content, and timestamp.
        created_at: Optional timestamp; defaults to now (UTC).
    """
    user_value = _require_object_id(user_id, "user_id")
    messages_value = _validate_messages(messages)
    created_value = _ensure_datetime(created_at, "created_at")

    return {
        "user_id": user_value,
        "messages": messages_value,
        "created_at": created_value,
    }
