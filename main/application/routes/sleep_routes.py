import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from main.application.routes._auth_utils import login_required
from main.persistence.repositories import sleep_repository

logger = logging.getLogger(__name__)

sleep_bp = Blueprint("sleep", __name__)

_VALID_QUALITIES = {"poor", "fair", "good", "excellent"}


@sleep_bp.post("/api/sleep")
@login_required
def log_sleep(current_user_id: str):
    """
    Log a sleep entry for the authenticated user.

    Request body (JSON):
        hours   (float) – hours slept
        quality (str)   – one of 'poor', 'fair', 'good', 'excellent'

    Returns 201 with the created sleep document on success.
    Returns 400 if required fields are missing or invalid.
    Returns 500 on server error.
    """
    body = request.get_json(silent=True) or {}
    hours = body.get("hours")
    quality = body.get("quality", "fair").strip().lower()

    if hours is None or not isinstance(hours, (int, float)) or not (0 < hours <= 24):
        return jsonify({"message": "Hours must be a number between 0 and 24."}), 400
    if quality not in _VALID_QUALITIES:
        return jsonify({"message": "Quality must be 'poor', 'fair', 'good', or 'excellent'."}), 400

    sleep_doc = {
        "user_id": current_user_id,
        "duration_hrs": float(hours),
        "quality": quality,
        "logged_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    try:
        inserted_id = sleep_repository.insert(sleep_doc)
    except RuntimeError:
        logger.exception("log_sleep: insert failed for user=%s", current_user_id)
        return jsonify({"message": "Could not save sleep log. Please try again."}), 500

    return jsonify({"id": inserted_id, "reaction": "😴 Sleep logged!"}), 201


@sleep_bp.get("/api/sleep")
@login_required
def get_sleep(current_user_id: str):
    """
    Retrieve recent sleep logs for the authenticated user.

    Returns 200 with a list of sleep documents.
    Returns 500 on server error.
    """
    try:
        logs = sleep_repository.find_recent(current_user_id)
    except RuntimeError:
        logger.exception("get_sleep: query failed for user=%s", current_user_id)
        return jsonify({"message": "Could not retrieve sleep logs."}), 500

    return jsonify({"sleep_logs": logs}), 200
