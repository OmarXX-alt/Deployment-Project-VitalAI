from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId

from database import get_db


_MEAL_PROJECTION = {
    "user_id": 1,
    "meal_name": 1,
    "calories": 1,
    "meal_type": 1,
    "logged_at": 1,
    "ai_reaction": 1,
}


def _to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise RuntimeError("Invalid ObjectId") from exc


def _serialize_value(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    return value


def _serialize_docs(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_serialize_value(doc) for doc in docs]


def insert(doc: dict) -> str:
    try:
        result = get_db().meal_logs.insert_one(doc)
        return str(result.inserted_id)
    except Exception as exc:
        raise RuntimeError("Failed to insert meal log") from exc


def find_by_id(doc_id: str) -> dict | None:
    try:
        doc = get_db().meal_logs.find_one({"_id": _to_object_id(doc_id)}, _MEAL_PROJECTION)
        return _serialize_value(doc) if doc else None
    except Exception as exc:
        raise RuntimeError("Failed to find meal log by id") from exc


def find_by_user(user_id: str) -> list[dict]:
    try:
        cursor = get_db().meal_logs.find({"user_id": _to_object_id(user_id)}, _MEAL_PROJECTION)
        return _serialize_docs(list(cursor))
    except Exception as exc:
        raise RuntimeError("Failed to find meal logs by user") from exc


def find_recent(user_id: str, days: int = 7) -> list[dict]:
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cursor = (
            get_db()
            .meal_logs
            .find(
                {"user_id": _to_object_id(user_id), "logged_at": {"$gte": cutoff}},
                _MEAL_PROJECTION,
            )
            .sort("logged_at", -1)
        )
        return _serialize_docs(list(cursor))
    except Exception as exc:
        raise RuntimeError("Failed to find recent meal logs") from exc


def update_ai_reaction(log_id: str, reaction: dict) -> bool:
    try:
        result = get_db().meal_logs.update_one(
            {"_id": _to_object_id(log_id)},
            {"$set": {"ai_reaction": reaction}},
        )
        return result.modified_count == 1
    except Exception as exc:
        raise RuntimeError("Failed to update meal ai_reaction") from exc


def delete_by_id(doc_id: str) -> bool:
    try:
        result = get_db().meal_logs.delete_one({"_id": _to_object_id(doc_id)})
        return result.deleted_count == 1
    except Exception as exc:
        raise RuntimeError("Failed to delete meal log by id") from exc
