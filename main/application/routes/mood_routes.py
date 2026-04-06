import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from main.application.routes._auth_utils import login_required
from main.persistence.repositories import mood_repository

logger = logging.getLogger(__name__)

mood_bp = Blueprint("moods", __name__)


@mood_bp.post("/api/moods")
@login_required
def log_mood(current_user_id: str):
    """
    Log a mood check-in for the authenticated user.

    Request body (JSON):
        rating (int) – mood score from 1 to 10
        notes  (str) – optional free-text note

    Returns 201 with the created mood document on success.
    Returns 400 if the rating is missing or out of range.
    Returns 500 on server error.
    """
    body = request.get_json(silent=True) or {}
    rating = body.get("rating")
    notes = body.get("notes", "").strip()

    if rating is None or not isinstance(rating, (int, float)) or not (1 <= int(rating) <= 10):
        return jsonify({"message": "Rating must be a number between 1 and 10."}), 400

    mood_doc = {
        "user_id": current_user_id,
        "mood_rating": int(rating),
        "notes": notes,
        "logged_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    try:
        inserted_id = mood_repository.insert(mood_doc)
    except RuntimeError:
        logger.exception("log_mood: insert failed for user=%s", current_user_id)
        return jsonify({"message": "Could not save mood log. Please try again."}), 500

    return jsonify({"id": inserted_id, "reaction": "😊 Mood logged!"}), 201


@mood_bp.get("/api/moods")
@login_required
def get_moods(current_user_id: str):
    """
    Retrieve recent mood logs for the authenticated user.

    Returns 200 with a list of mood documents.
    Returns 500 on server error.
    """
    try:
        logs = mood_repository.find_recent(current_user_id)
    except RuntimeError:
        logger.exception("get_moods: query failed for user=%s", current_user_id)
        return jsonify({"message": "Could not retrieve mood logs."}), 500

    return jsonify({"mood_logs": logs}), 200
