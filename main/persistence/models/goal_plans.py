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


def _require_list(value: Any, field_name: str) -> list[dict[str, object]]:
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{field_name} must be a list of dicts")
    return list(value)


def _ensure_datetime(value: datetime | None, field_name: str) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def create_goal_plan(
    user_id: ObjectId,
    goal: str,
    weekly_tasks: list[dict[str, object]],
    created_at: datetime | None = None,
) -> dict[str, object]:
    """
    Create a goal plan document ready for MongoDB insertion.

    Parameters:
        user_id: MongoDB ObjectId of the user.
        goal: Goal description.
        weekly_tasks: List of week plans and tasks.
        created_at: Optional timestamp; defaults to now (UTC).
    """
    user_value = _require_object_id(user_id, "user_id")
    goal_value = _require_str(goal, "goal")
    tasks_value = _require_list(weekly_tasks, "weekly_tasks")
    created_value = _ensure_datetime(created_at, "created_at")

    return {
        "user_id": user_value,
        "goal": goal_value,
        "weekly_tasks": tasks_value,
        "created_at": created_value,
    }
