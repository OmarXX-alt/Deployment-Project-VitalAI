from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from pymongo.errors import DuplicateKeyError, OperationFailure, WriteError

from database import get_db
from utils.serialization import to_json_serializable
from utils.validators import validate_object_id

logger = logging.getLogger(__name__)


_SLEEP_PROJECTION = {
    "user_id": 1,
    "sleep_start": 1,
    "sleep_end": 1,
    "duration_hrs": 1,
    "quality": 1,
    "logged_at": 1,
    "ai_reaction": 1,
}


def insert(doc: dict) -> str:
    try:
        result = get_db().sleep_logs.insert_one(doc)
        inserted_id = str(result.inserted_id)
        logger.debug("insert_sleep ok id=%s", inserted_id)
        return inserted_id
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        user_id = doc.get("user_id") if isinstance(doc, dict) else None
        logger.error("insert_sleep failed user_id=%s", user_id, exc_info=True)
        raise RuntimeError(f"insert_sleep failed for user {user_id}: {exc}") from exc


def find_by_id(doc_id: str) -> dict | None:
    object_id = validate_object_id(doc_id)
    try:
        doc = get_db().sleep_logs.find_one({"_id": object_id}, _SLEEP_PROJECTION)
        logger.debug("find_sleep_by_id ok id=%s", doc_id)
        return to_json_serializable(doc) if doc else None
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        logger.error("find_sleep_by_id failed id=%s", doc_id, exc_info=True)
        raise RuntimeError(f"find_sleep_by_id failed for id {doc_id}: {exc}") from exc


def find_by_user(user_id: str) -> list[dict]:
    user_object_id = validate_object_id(user_id)
    try:
        cursor = get_db().sleep_logs.find({"user_id": user_object_id}, _SLEEP_PROJECTION)
        docs = [to_json_serializable(doc) for doc in cursor]
        logger.debug("find_sleep_by_user ok user_id=%s count=%s", user_id, len(docs))
        return docs
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        logger.error("find_sleep_by_user failed user_id=%s", user_id, exc_info=True)
        raise RuntimeError(f"find_sleep_by_user failed for user {user_id}: {exc}") from exc


def find_recent(user_id: str, days: int = 7) -> list[dict]:
    user_object_id = validate_object_id(user_id)
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cursor = (
            get_db()
            .sleep_logs
            .find(
                {"user_id": user_object_id, "logged_at": {"$gte": cutoff}},
                _SLEEP_PROJECTION,
            )
            .sort("logged_at", -1)
        )
        docs = [to_json_serializable(doc) for doc in cursor]
        logger.debug("find_recent_sleep ok user_id=%s days=%s count=%s", user_id, days, len(docs))
        return docs
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        logger.error("find_recent_sleep failed user_id=%s", user_id, exc_info=True)
        raise RuntimeError(f"find_recent_sleep failed for user {user_id}: {exc}") from exc


def update_ai_reaction(log_id: str, reaction: dict) -> bool:
    log_object_id = validate_object_id(log_id)
    try:
        result = get_db().sleep_logs.update_one(
            {"_id": log_object_id},
            {"$set": {"ai_reaction": reaction}},
        )
        updated = result.modified_count == 1
        logger.debug("update_sleep_ai ok id=%s updated=%s", log_id, updated)
        return updated
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        logger.error("update_sleep_ai failed id=%s", log_id, exc_info=True)
        raise RuntimeError(f"update_sleep_ai failed for id {log_id}: {exc}") from exc


def delete_by_id(doc_id: str) -> bool:
    object_id = validate_object_id(doc_id)
    try:
        result = get_db().sleep_logs.delete_one({"_id": object_id})
        deleted = result.deleted_count == 1
        logger.debug("delete_sleep_by_id ok id=%s deleted=%s", doc_id, deleted)
        return deleted
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        logger.error("delete_sleep_by_id failed id=%s", doc_id, exc_info=True)
        raise RuntimeError(f"delete_sleep_by_id failed for id {doc_id}: {exc}") from exc
