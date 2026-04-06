import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from main.application.routes._auth_utils import login_required
from main.persistence.repositories import meal_repository

logger = logging.getLogger(__name__)

meal_bp = Blueprint("meals", __name__)


@meal_bp.post("/api/meals")
@login_required
def log_meal(current_user_id: str):
    """
    Log a meal entry for the authenticated user.

    Request body (JSON):
        food     (str) – food item name
        calories (int) – calorie count
        protein  (int) – protein in grams

    Returns 201 with the created meal document on success.
    Returns 400 if required fields are missing or invalid.
    Returns 500 on server error.
    """
    body = request.get_json(silent=True) or {}
    food = body.get("food", "").strip()
    calories = body.get("calories")
    protein = body.get("protein")

    if not food:
        return jsonify({"message": "Food item is required."}), 400
    if calories is None or not isinstance(calories, (int, float)) or calories < 0:
        return jsonify({"message": "A valid calorie count is required."}), 400

    meal_doc = {
        "user_id": current_user_id,
        "food": food,
        "calories": int(calories),
        "protein": int(protein) if isinstance(protein, (int, float)) else 0,
        "logged_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    try:
        inserted_id = meal_repository.insert(meal_doc)
    except RuntimeError:
        logger.exception("log_meal: insert failed for user=%s", current_user_id)
        return jsonify({"message": "Could not save meal. Please try again."}), 500

    return jsonify({"id": inserted_id, "reaction": "✅ Meal logged!"}), 201


@meal_bp.get("/api/meals")
@login_required
def get_meals(current_user_id: str):
    """
    Retrieve recent meal logs for the authenticated user.

    Returns 200 with a list of meal documents.
    Returns 500 on server error.
    """
    try:
        meals = meal_repository.find_recent(current_user_id)
    except RuntimeError:
        logger.exception("get_meals: query failed for user=%s", current_user_id)
        return jsonify({"message": "Could not retrieve meals."}), 500

    return jsonify({"meals": meals}), 200
