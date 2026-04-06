import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from main.application.routes._auth_utils import login_required
from main.persistence.repositories import hydration_repository

logger = logging.getLogger(__name__)

hydration_bp = Blueprint("hydration", __name__)


@hydration_bp.post("/api/hydration")
@login_required
def log_hydration(current_user_id: str):
    """
    Log a water intake entry for the authenticated user.

    Request body (JSON):
        ml (int) – millilitres consumed

    Returns 201 with the created hydration document on success.
    Returns 400 if the value is missing or invalid.
    Returns 500 on server error.
    """
    body = request.get_json(silent=True) or {}
    ml = body.get("ml")

    if ml is None or not isinstance(ml, (int, float)) or ml <= 0:
        return jsonify({"message": "A positive ml value is required."}), 400

    hydration_doc = {
        "user_id": current_user_id,
        "daily_total_ml": int(ml),
        "logged_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    try:
        inserted_id = hydration_repository.insert(hydration_doc)
    except RuntimeError:
        logger.exception("log_hydration: insert failed for user=%s", current_user_id)
        return jsonify({"message": "Could not save hydration log. Please try again."}), 500

    return jsonify({"id": inserted_id, "reaction": "💧 Water logged!"}), 201


@hydration_bp.get("/api/hydration")
@login_required
def get_hydration(current_user_id: str):
    """
    Retrieve recent hydration logs for the authenticated user.

    Returns 200 with a list of hydration documents.
    Returns 500 on server error.
    """
    try:
        logs = hydration_repository.find_recent(current_user_id)
    except RuntimeError:
        logger.exception("get_hydration: query failed for user=%s", current_user_id)
        return jsonify({"message": "Could not retrieve hydration logs."}), 500

    return jsonify({"hydration_logs": logs}), 200
