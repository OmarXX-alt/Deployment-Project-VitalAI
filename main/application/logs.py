from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from main.business import log_service
from main.persistence.schemas import (
    HydrationLogSchema,
    MealLogSchema,
    MoodLogSchema,
    SleepLogSchema,
    WorkoutLogSchema,
    validate_schema,
)
from main.server.middleware.auth import require_auth


logs_bp = Blueprint("logs", __name__)

workout_schema = WorkoutLogSchema()
meal_schema = MealLogSchema()
sleep_schema = SleepLogSchema()
hydration_schema = HydrationLogSchema()
mood_schema = MoodLogSchema()

WELLNESS_RESOURCE = {
    "url": "https://www.mind.org.uk/information-support/",
    "label": "Mind — Mental Health Support",
    "note": "We noticed a low mood today. You're not alone.",
}


@logs_bp.post("/api/logs/workout")
@require_auth
def log_workout():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("log_workout: missing or invalid JSON body")
        return jsonify({"error": "invalid_json", "message": "Request body is required."}), 400

    validated, errors = validate_schema(workout_schema, body)
    if errors:
        current_app.logger.info("log_workout: validation_error %s", errors)
        return jsonify({"error": "validation_error", "fields": errors}), 422

    # TODO: [Logic-Issue-005]
    response_body, status = log_service.save_workout_log(
        g.user_id,
        validated["exercise_type"],
        validated["duration_minutes"],
        validated.get("sets"),
        validated.get("reps"),
        validated["intensity"],
        validated.get("logged_at"),
    )
    return jsonify(response_body), status


@logs_bp.post("/api/logs/meal")
@require_auth
def log_meal():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("log_meal: missing or invalid JSON body")
        return jsonify({"error": "invalid_json", "message": "Request body is required."}), 400

    validated, errors = validate_schema(meal_schema, body)
    if errors:
        current_app.logger.info("log_meal: validation_error %s", errors)
        return jsonify({"error": "validation_error", "fields": errors}), 422

    # TODO: [Logic-Issue-006]
    response_body, status = log_service.save_meal_log(
        g.user_id,
        validated["meal_name"],
        validated["calories"],
        validated["meal_type"],
        validated.get("logged_at"),
    )
    return jsonify(response_body), status


@logs_bp.post("/api/logs/sleep")
@require_auth
def log_sleep():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("log_sleep: missing or invalid JSON body")
        return jsonify({"error": "invalid_json", "message": "Request body is required."}), 400

    validated, errors = validate_schema(sleep_schema, body)
    if errors:
        current_app.logger.info("log_sleep: validation_error %s", errors)
        return jsonify({"error": "validation_error", "fields": errors}), 422

    # TODO: [Logic-Issue-007]
    response_body, status = log_service.save_sleep_log(
        g.user_id,
        validated["sleep_start"],
        validated["sleep_end"],
        validated["quality_score"],
    )
    return jsonify(response_body), status


@logs_bp.post("/api/logs/hydration")
@require_auth
def log_hydration():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("log_hydration: missing or invalid JSON body")
        return jsonify({"error": "invalid_json", "message": "Request body is required."}), 400

    validated, errors = validate_schema(hydration_schema, body)
    if errors:
        current_app.logger.info("log_hydration: validation_error %s", errors)
        return jsonify({"error": "validation_error", "fields": errors}), 422

    # TODO: [Logic-Issue-008]
    response_body, status = log_service.save_hydration_log(
        g.user_id,
        validated["amount_ml"],
        validated.get("logged_at"),
    )
    return jsonify(response_body), status


@logs_bp.post("/api/logs/mood")
@require_auth
def log_mood():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("log_mood: missing or invalid JSON body")
        return jsonify({"error": "invalid_json", "message": "Request body is required."}), 400

    validated, errors = validate_schema(mood_schema, body)
    if errors:
        current_app.logger.info("log_mood: validation_error %s", errors)
        return jsonify({"error": "validation_error", "fields": errors}), 422

    # TODO: [Logic-Issue-009]
    response_body, status = log_service.save_mood_log(
        g.user_id,
        validated["mood_score"],
        validated.get("note"),
    )

    response_body["wellness_resource"] = (
        WELLNESS_RESOURCE if validated["mood_score"] == 1 else None
    )
    return jsonify(response_body), status


@logs_bp.get("/api/logs/<string:log_type>")
@require_auth
def log_history(log_type: str):
    valid_types = {"workout", "meal", "sleep", "hydration", "mood"}
    if log_type not in valid_types:
        return jsonify({"error": "invalid_log_type", "message": "Unsupported log type."}), 400

    days_param = request.args.get("days", "7")
    try:
        days = int(days_param)
    except ValueError:
        return jsonify({"error": "invalid_days", "message": "days must be an integer."}), 400

    days = max(1, min(days, 90))

    # TODO: [Logic-Issue-010]
    response_body, status = log_service.get_log_history(g.user_id, log_type, days)
    return jsonify(response_body), status
