from __future__ import annotations

import logging

from pymongo.errors import DuplicateKeyError, OperationFailure, WriteError

from database import get_db
from main.business.utils.serialization import to_json_serializable
from main.business.utils.validators import validate_object_id

logger = logging.getLogger(__name__)


_USER_PROJECTION = {
    "email": 1,
    "password_hash": 1,
    "display_name": 1,
    "daily_calorie_target": 1,
    "hydration_goal_ml": 1,
    "wellness_goal": 1,
    "created_at": 1,
}


def insert(doc: dict) -> str:
    try:
        result = get_db().users.insert_one(doc)
        inserted_id = str(result.inserted_id)
        logger.debug("insert_user ok id=%s", inserted_id)
        return inserted_id
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        email = doc.get("email") if isinstance(doc, dict) else None
        logger.error("insert_user failed for email=%s", email, exc_info=True)
        raise RuntimeError(
            f"insert_user failed for email {email}: {exc}"
        ) from exc


def find_by_id(doc_id: str) -> dict | None:
    object_id = validate_object_id(doc_id)
    try:
        doc = get_db().users.find_one({"_id": object_id}, _USER_PROJECTION)
        logger.debug("find_user_by_id ok id=%s", doc_id)
        return to_json_serializable(doc) if doc else None
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        logger.error("find_user_by_id failed id=%s", doc_id, exc_info=True)
        raise RuntimeError(
            f"find_user_by_id failed for id {doc_id}: {exc}"
        ) from exc


def find_by_email(email: str) -> dict | None:
    try:
        doc = get_db().users.find_one({"email": email}, _USER_PROJECTION)
        logger.debug("find_user_by_email ok email=%s", email)
        return to_json_serializable(doc) if doc else None
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        logger.error(
            "find_user_by_email failed email=%s", email, exc_info=True
        )
        raise RuntimeError(
            f"find_user_by_email failed for email {email}: {exc}"
        ) from exc


def find_by_user(user_id: str) -> list[dict]:
    user_object_id = validate_object_id(user_id)
    try:
        doc = get_db().users.find_one(
            {"_id": user_object_id}, _USER_PROJECTION
        )
        logger.debug("find_user_by_user_id ok user_id=%s", user_id)
        return [to_json_serializable(doc)] if doc else []
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        logger.error(
            "find_user_by_user_id failed user_id=%s", user_id, exc_info=True
        )
        raise RuntimeError(
            f"find_user_by_user_id failed for user {user_id}: {exc}"
        ) from exc


def delete_by_id(doc_id: str) -> bool:
    object_id = validate_object_id(doc_id)
    try:
        result = get_db().users.delete_one({"_id": object_id})
        deleted = result.deleted_count == 1
        logger.debug("delete_user_by_id ok id=%s deleted=%s", doc_id, deleted)
        return deleted
    except (DuplicateKeyError, WriteError, OperationFailure) as exc:
        logger.error("delete_user_by_id failed id=%s", doc_id, exc_info=True)
        raise RuntimeError(
            f"delete_user_by_id failed for id {doc_id}: {exc}"
        ) from exc
