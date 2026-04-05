from __future__ import annotations

from bson import ObjectId


def validate_object_id(value: str) -> ObjectId:
    if not isinstance(value, str) or not value:
        raise ValueError("id must be a non-empty string")
    if not ObjectId.is_valid(value):
        raise ValueError("id must be a valid ObjectId")
    return ObjectId(value)
