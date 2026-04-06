import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from main.application.routes._auth_utils import login_required
from main.persistence.repositories import workout_repository

logger = logging.getLogger(__name__)

workout_bp = Blueprint("workouts", __name__)

_VALID_INTENSITIES = {"low", "medium", "high"}


@workout_bp.post("/api/workouts")
@login_required
def log_workout(current_user_id: str):
    """
    Log a workout entry for the authenticated user.

    Request body (JSON):
        type      (str) – exercise name / description
        duration  (int) – duration in minutes
        intensity (str) – one of 'low', 'medium', 'high'

    Returns 201 with the created workout document on success.
    Returns 400 if required fields are missing or invalid.
    Returns 500 on server error.
    """
    body = request.get_json(silent=True) or {}
    workout_type = body.get("type", "").strip()
    duration = body.get("duration")
    intensity = body.get("intensity", "medium").strip().lower()

    if not workout_type:
        return jsonify({"message": "Exercise type is required."}), 400
    if duration is None or not isinstance(duration, (int, float)) or duration <= 0:
        return jsonify({"message": "A valid duration (minutes) is required."}), 400
    if intensity not in _VALID_INTENSITIES:
        return jsonify({"message": "Intensity must be 'low', 'medium', or 'high'."}), 400

    workout_doc = {
        "user_id": current_user_id,
        "type": workout_type,
        "duration_minutes": int(duration),
        "intensity": intensity,
        "logged_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    try:
        inserted_id = workout_repository.insert(workout_doc)
    except RuntimeError:
        logger.exception("log_workout: insert failed for user=%s", current_user_id)
        return jsonify({"message": "Could not save workout. Please try again."}), 500

    return jsonify({"id": inserted_id, "reaction": "💪 Workout logged!"}), 201


@workout_bp.get("/api/workouts")
@login_required
def get_workouts(current_user_id: str):
    """
    Retrieve recent workout logs for the authenticated user.

    Returns 200 with a list of workout documents.
    Returns 500 on server error.
    """
    try:
        workouts = workout_repository.find_recent(current_user_id)
    except RuntimeError:
        logger.exception("get_workouts: query failed for user=%s", current_user_id)
        return jsonify({"message": "Could not retrieve workouts."}), 500

    return jsonify({"workouts": workouts}), 200
