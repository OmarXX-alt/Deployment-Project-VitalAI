from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify, request

from main.business import ai_service, log_service
from main.business.utils.aggregation import (
    get_hydration_context,
    get_meal_context,
    get_mood_context,
    get_sleep_context,
    get_workout_context,
)
from main.persistence.db import get_db
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
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body is required.",
                }
            ),
            400,
        )

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
    
    # Use business layer instead of direct API calls
    reaction = None
    try:
        db = get_db()
        context = get_workout_context(g.user_id, db)
        new_entry = {
            "exercise_type": response_body.get("exercise_type"),
            "duration_minutes": response_body.get("duration_minutes"),
            "intensity": response_body.get("intensity"),
            "sets": response_body.get("sets"),
            "reps": response_body.get("reps"),
        }
        reaction = ai_service.get_reaction("workout", context, new_entry, timeout_seconds=3)
    except Exception as exc:
        current_app.logger.warning("workout AI reaction failed: %s", exc)

    response_body["reaction"] = reaction if reaction else {
        "type": "workout",
        "message": None,
        "tags": [],
    }
    return jsonify(response_body), status


@logs_bp.post("/api/logs/meal")
@require_auth
def log_meal():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("log_meal: missing or invalid JSON body")
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body is required.",
                }
            ),
            400,
        )

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
    
    # Use business layer instead of direct API calls
    reaction = None
    try:
        db = get_db()
        context = get_meal_context(g.user_id, db)
        new_entry = {
            "meal_name": response_body.get("meal_name"),
            "calories": response_body.get("calories"),
            "meal_type": response_body.get("meal_type"),
            "today_total_kcal": response_body.get("today_total_kcal"),
        }
        reaction = ai_service.get_reaction("meal", context, new_entry, timeout_seconds=3)
    except Exception as exc:
        current_app.logger.warning("meal AI reaction failed: %s", exc)

    response_body["reaction"] = reaction if reaction else {
        "type": "meal",
        "message": None,
        "tags": [],
    }
    return jsonify(response_body), status


@logs_bp.post("/api/logs/sleep")
@require_auth
def log_sleep():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("log_sleep: missing or invalid JSON body")
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body is required.",
                }
            ),
            400,
        )

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
    
    # Use business layer instead of direct API calls
    reaction = None
    try:
        db = get_db()
        context = get_sleep_context(g.user_id, db)
        new_entry = {
            "sleep_start": response_body.get("sleep_start"),
            "sleep_end": response_body.get("sleep_end"),
            "duration_minutes": response_body.get("duration_minutes"),
            "quality_score": response_body.get("quality_score"),
        }
        reaction = ai_service.get_reaction("sleep", context, new_entry, timeout_seconds=3)
    except Exception as exc:
        current_app.logger.warning("sleep AI reaction failed: %s", exc)

    response_body["reaction"] = reaction if reaction else {
        "type": "sleep",
        "message": None,
        "tags": [],
    }
    return jsonify(response_body), status


@logs_bp.post("/api/logs/hydration")
@require_auth
def log_hydration():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("log_hydration: missing or invalid JSON body")
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body is required.",
                }
            ),
            400,
        )

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
    
    # Use business layer instead of direct API calls
    reaction = None
    try:
        db = get_db()
        context = get_hydration_context(g.user_id, db)
        new_entry = {
            "amount_ml": response_body.get("amount_ml"),
            "daily_total_ml": response_body.get("daily_total_ml"),
            "pct_of_goal": response_body.get("pct_of_goal"),
        }
        reaction = ai_service.get_reaction("hydration", context, new_entry, timeout_seconds=3)
    except Exception as exc:
        current_app.logger.warning("hydration AI reaction failed: %s", exc)

    response_body["reaction"] = reaction if reaction else {
        "type": "hydration",
        "message": None,
        "tags": [],
    }
    return jsonify(response_body), status


@logs_bp.post("/api/logs/mood")
@require_auth
def log_mood():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("log_mood: missing or invalid JSON body")
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body is required.",
                }
            ),
            400,
        )

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
    
    # Use business layer instead of direct API calls
    reaction = None
    try:
        db = get_db()
        context = get_mood_context(g.user_id, db)
        new_entry = {
            "mood_score": response_body.get("mood_score"),
            "note": response_body.get("note"),
            "date": response_body.get("date"),
        }
        reaction = ai_service.get_reaction("mood", context, new_entry, timeout_seconds=3)
    except Exception as exc:
        current_app.logger.warning("mood AI reaction failed: %s", exc)

    response_body["wellness_resource"] = (
        WELLNESS_RESOURCE if validated["mood_score"] == 1 else None
    )
    response_body["reaction"] = reaction if reaction else {
        "type": "mood",
        "message": None,
        "tags": [],
    }
    return jsonify(response_body), status


@logs_bp.get("/api/logs/<string:log_type>")
@require_auth
def log_history(log_type: str):
    valid_types = {"workout", "meal", "sleep", "hydration", "mood"}
    if log_type not in valid_types:
        return (
            jsonify(
                {
                    "error": "invalid_log_type",
                    "message": "Unsupported log type.",
                }
            ),
            400,
        )

    days_param = request.args.get("days", "7")
    try:
        days = int(days_param)
    except ValueError:
        return (
            jsonify(
                {
                    "error": "invalid_days",
                    "message": "days must be an integer.",
                }
            ),
            400,
        )

    days = max(1, min(days, 90))

    # TODO: [Logic-Issue-010]
    response_body, status = log_service.get_log_history(
        g.user_id, log_type, days
    )
    return jsonify(response_body), status
