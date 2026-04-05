from __future__ import annotations

from datetime import datetime
from typing import Any

from bson import ObjectId


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


def to_json_serializable(doc: dict[str, Any]) -> dict[str, Any]:
    return _serialize_value(doc)
