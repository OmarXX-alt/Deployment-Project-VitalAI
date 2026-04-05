from __future__ import annotations

from datetime import datetime
from typing import Any

from bson import ObjectId

from database import get_db


_USER_PROJECTION = {
    "email": 1,
    "password_hash": 1,
    "display_name": 1,
    "daily_calorie_target": 1,
    "hydration_goal_ml": 1,
    "wellness_goal": 1,
    "created_at": 1,
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


def _serialize_doc(doc: dict[str, Any] | None) -> dict[str, Any] | None:
    if doc is None:
        return None
    return _serialize_value(doc)


def insert(doc: dict) -> str:
    try:
        result = get_db().users.insert_one(doc)
        return str(result.inserted_id)
    except Exception as exc:
        raise RuntimeError("Failed to insert user") from exc


def find_by_id(doc_id: str) -> dict | None:
    try:
        doc = get_db().users.find_one({"_id": _to_object_id(doc_id)}, _USER_PROJECTION)
        return _serialize_doc(doc)
    except Exception as exc:
        raise RuntimeError("Failed to find user by id") from exc


def find_by_email(email: str) -> dict | None:
    try:
        doc = get_db().users.find_one({"email": email}, _USER_PROJECTION)
        return _serialize_doc(doc)
    except Exception as exc:
        raise RuntimeError("Failed to find user by email") from exc


def find_by_user(user_id: str) -> list[dict]:
    try:
        doc = get_db().users.find_one({"_id": _to_object_id(user_id)}, _USER_PROJECTION)
        serialized = _serialize_doc(doc)
        return [serialized] if serialized else []
    except Exception as exc:
        raise RuntimeError("Failed to find user by user_id") from exc


def delete_by_id(doc_id: str) -> bool:
    try:
        result = get_db().users.delete_one({"_id": _to_object_id(doc_id)})
        return result.deleted_count == 1
    except Exception as exc:
        raise RuntimeError("Failed to delete user by id") from exc
