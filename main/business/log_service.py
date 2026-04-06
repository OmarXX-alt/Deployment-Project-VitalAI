from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bson import ObjectId
from bson.errors import InvalidId

from main.business import aggregation_service, ai_service
from main.persistence.extensions import mongo
from main.persistence.models import (
    HydrationLogDocument,
    MealLogDocument,
    MoodLogDocument,
    SleepLogDocument,
    WorkoutLogDocument,
)

_ = (
    HydrationLogDocument,
    MealLogDocument,
    MoodLogDocument,
    SleepLogDocument,
    WorkoutLogDocument,
)


def _to_iso(value) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def save_workout_log(
    user_id: str,
    exercise_type: str,
    duration_minutes: int,
    sets: int | None,
    reps: int | None,
    intensity: str,
    logged_at=None,
) -> tuple[dict, int]:
    """Persist a workout log and return the response contract.

    Purpose:
        Record a workout log entry and return the saved entry plus AI reaction.
    Expected Input types:
        user_id (str), exercise_type (str), duration_minutes (int),
        sets (Optional[int]), reps (Optional[int]), intensity (str),
        logged_at (Optional[datetime or str]).
    Expected Output:
        tuple[dict, int] with workout log response shape and status 201.

    # TODO: [Logic-Issue-005]
    Implementation checklist:
        1. resolve logged_at
        2. insert
        3. build_context(workouts, 7d)
        4. ai_service.get_reaction("workout", ctx, entry)
        5. return with reaction
    """
    now = datetime.now(timezone.utc)
    resolved_at = logged_at if logged_at is not None else now
    if resolved_at.tzinfo is None:
        resolved_at = resolved_at.replace(tzinfo=timezone.utc)

    clean_exercise_type = exercise_type.strip()[:100]
    intensity = intensity.strip()
    doc = {
        "user_id": user_id,
        "exercise_type": clean_exercise_type,
        "duration_minutes": duration_minutes,
        "sets": sets,
        "reps": reps,
        "intensity": intensity,
        "logged_at": resolved_at,
        "created_at": now,
    }
    result = mongo.workout_logs.insert_one(doc)
    log_id = str(result.inserted_id)

    context = aggregation_service.build_context(
        user_id, log_types=["workouts"], days=7
    )

    new_entry = {
        "exercise_type": clean_exercise_type,
        "duration_minutes": duration_minutes,
        "intensity": intensity,
        "sets": sets,
        "reps": reps,
    }
    reaction = None
    try:
        from flask import current_app

        reaction = ai_service.get_reaction(
            "workout",
            context,
            new_entry,
            gemini_api_key=current_app.config.get("GEMINI_API_KEY", ""),
            timeout_seconds=current_app.config.get("GEMINI_TIMEOUT_SECONDS", 3),
        )
    except Exception:
        reaction = None

    return (
        {
            "log_id": log_id,
            "exercise_type": clean_exercise_type,
            "duration_minutes": duration_minutes,
            "sets": sets,
            "reps": reps,
            "intensity": intensity,
            "logged_at": resolved_at.isoformat(),
            "reaction": reaction,
        },
        201,
    )


def save_meal_log(
    user_id: str,
    meal_name: str,
    calories: int,
    meal_type: str,
    logged_at=None,
) -> tuple[dict, int]:
    """Persist a meal log and return the response contract.

    Purpose:
        Record a meal entry, compute daily totals, and return AI reaction.
    Expected Input types:
        user_id (str), meal_name (str), calories (int), meal_type (str),
        logged_at (Optional[datetime or str]).
    Expected Output:
        tuple[dict, int] with meal log response shape and status 201.

    # TODO: [Logic-Issue-006]
    Implementation checklist:
        1. insert
        2. SUM today's kcal
        3. fetch profile.calorie_target
        4. build_context(meals+workouts)
        5. ai_service.get_reaction("meal")
        6. return
    NOTE: This hook queries BOTH meal_logs AND workout_logs for context.
    """
    now = datetime.now(timezone.utc)
    resolved_at = logged_at if logged_at is not None else now
    if resolved_at.tzinfo is None:
        resolved_at = resolved_at.replace(tzinfo=timezone.utc)

    clean_meal_name = meal_name.strip()[:100]
    meal_type = meal_type.strip()
    doc = {
        "user_id": user_id,
        "meal_name": clean_meal_name,
        "calories": calories,
        "meal_type": meal_type,
        "logged_at": resolved_at,
        "created_at": now,
    }
    result = mongo.meal_logs.insert_one(doc)
    log_id = str(result.inserted_id)

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    pipeline = [
        {"$match": {"user_id": user_id, "logged_at": {"$gte": today_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$calories"}}},
    ]
    agg_result = list(mongo.meal_logs.aggregate(pipeline))
    today_total_kcal = agg_result[0]["total"] if agg_result else calories

    context = aggregation_service.build_context(
        user_id, log_types=["meals", "workouts"], days=7
    )

    new_entry = {
        "meal_name": clean_meal_name,
        "calories": calories,
        "meal_type": meal_type,
        "today_total_kcal": today_total_kcal,
    }
    reaction = None
    try:
        from flask import current_app

        reaction = ai_service.get_reaction(
            "meal",
            context,
            new_entry,
            gemini_api_key=current_app.config.get("GEMINI_API_KEY", ""),
            timeout_seconds=current_app.config.get("GEMINI_TIMEOUT_SECONDS", 3),
        )
    except Exception:
        reaction = None

    return (
        {
            "log_id": log_id,
            "meal_name": clean_meal_name,
            "calories": calories,
            "meal_type": meal_type,
            "logged_at": resolved_at.isoformat(),
            "today_total_kcal": today_total_kcal,
            "reaction": reaction,
        },
        201,
    )


def save_sleep_log(
    user_id: str,
    sleep_start,
    sleep_end,
    quality_score: int,
) -> tuple[dict, int]:
    """Persist a sleep log and return the response contract.

    Purpose:
        Record sleep data and return the computed duration plus AI reaction.
    Expected Input types:
        user_id (str), sleep_start (datetime or str), sleep_end (datetime or str),
        quality_score (int).
    Expected Output:
        tuple[dict, int] with sleep log response shape and status 201.

    # TODO: [Logic-Issue-007]
    Implementation checklist:
        1. compute duration_minutes
        2. set logged_at=sleep_start
        3. insert
        4. aggregate 7d trend
        5. get_reaction("sleep")
        6. return
    """
    if sleep_start.tzinfo is None:
        sleep_start = sleep_start.replace(tzinfo=timezone.utc)
    if sleep_end.tzinfo is None:
        sleep_end = sleep_end.replace(tzinfo=timezone.utc)

    duration_minutes = int((sleep_end - sleep_start).total_seconds() / 60)
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "sleep_start": sleep_start,
        "sleep_end": sleep_end,
        "duration_minutes": duration_minutes,
        "quality_score": quality_score,
        "logged_at": sleep_start,
        "created_at": now,
    }
    result = mongo.sleep_logs.insert_one(doc)
    log_id = str(result.inserted_id)

    context = aggregation_service.build_context(user_id, log_types=["sleep"], days=7)

    new_entry = {
        "sleep_start": sleep_start.isoformat(),
        "sleep_end": sleep_end.isoformat(),
        "duration_minutes": duration_minutes,
        "quality_score": quality_score,
    }
    reaction = None
    try:
        from flask import current_app

        reaction = ai_service.get_reaction(
            "sleep",
            context,
            new_entry,
            gemini_api_key=current_app.config.get("GEMINI_API_KEY", ""),
            timeout_seconds=current_app.config.get("GEMINI_TIMEOUT_SECONDS", 3),
        )
    except Exception:
        reaction = None

    return (
        {
            "log_id": log_id,
            "sleep_start": sleep_start.isoformat(),
            "sleep_end": sleep_end.isoformat(),
            "duration_minutes": duration_minutes,
            "quality_score": quality_score,
            "reaction": reaction,
        },
        201,
    )


def save_hydration_log(
    user_id: str,
    amount_ml: int,
    logged_at=None,
) -> tuple[dict, int]:
    """Persist a hydration log and return the response contract.

    Purpose:
        Record hydration data, compute daily totals, and return AI reaction.
    Expected Input types:
        user_id (str), amount_ml (int), logged_at (Optional[datetime or str]).
    Expected Output:
        tuple[dict, int] with hydration log response shape and status 201.

    # TODO: [Logic-Issue-008]
    Implementation checklist:
        1. insert
        2. $group SUM today
        3. fetch hydration_goal
        4. build_context(hydration+workouts)
        5. get_reaction("hydration")
        6. return
    """
    now = datetime.now(timezone.utc)
    resolved_at = logged_at if logged_at is not None else now
    if resolved_at.tzinfo is None:
        resolved_at = resolved_at.replace(tzinfo=timezone.utc)

    doc = {
        "user_id": user_id,
        "amount_ml": amount_ml,
        "logged_at": resolved_at,
        "created_at": now,
    }
    result = mongo.hydration_logs.insert_one(doc)
    log_id = str(result.inserted_id)

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    pipeline = [
        {"$match": {"user_id": user_id, "logged_at": {"$gte": today_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount_ml"}}},
    ]
    agg = list(mongo.hydration_logs.aggregate(pipeline))
    daily_total_ml = agg[0]["total"] if agg else amount_ml

    hydration_goal = None
    try:
        user = mongo.users.find_one({"_id": ObjectId(user_id)}, {"hydration_goal": 1})
        hydration_goal = user.get("hydration_goal") if user else None
    except InvalidId:
        hydration_goal = None

    if hydration_goal and hydration_goal > 0:
        pct_of_goal = round((daily_total_ml / hydration_goal) * 100, 1)
    else:
        pct_of_goal = None

    context = aggregation_service.build_context(
        user_id, log_types=["hydration", "workouts"], days=7
    )

    new_entry = {
        "amount_ml": amount_ml,
        "daily_total_ml": daily_total_ml,
        "pct_of_goal": pct_of_goal,
    }
    reaction = None
    try:
        from flask import current_app

        reaction = ai_service.get_reaction(
            "hydration",
            context,
            new_entry,
            gemini_api_key=current_app.config.get("GEMINI_API_KEY", ""),
            timeout_seconds=current_app.config.get("GEMINI_TIMEOUT_SECONDS", 3),
        )
    except Exception:
        reaction = None

    return (
        {
            "log_id": log_id,
            "amount_ml": amount_ml,
            "logged_at": resolved_at.isoformat(),
            "daily_total_ml": daily_total_ml,
            "pct_of_goal": pct_of_goal,
            "reaction": reaction,
        },
        201,
    )


def save_mood_log(
    user_id: str,
    mood_score: int,
    note: str | None,
) -> tuple[dict, int]:
    """Upsert a mood log and return the response contract.

    Purpose:
        Record or update the mood log for today and return AI reaction.
    Expected Input types:
        user_id (str), mood_score (int), note (Optional[str]).
    Expected Output:
        tuple[dict, int] with mood log response shape and status 201.

    # TODO: [Logic-Issue-009]
    Implementation checklist:
        1. today_date
        2. sanitise note (max 500 chars)
        3. upsert (user_id+date compound key)
        4. build_context(mood+sleep+workouts)
        5. get_reaction("mood")
        6. return
    NOTE: Wellness resource overlay is applied at ROUTE level, not here.
    """
    now = datetime.now(timezone.utc)
    today_date = now.strftime("%Y-%m-%d")
    clean_note = note.strip()[:500] if note else None

    filter_doc = {"user_id": user_id, "date": today_date}
    update_doc = {
        "$set": {
            "mood_score": mood_score,
            "note": clean_note,
            "logged_at": now,
        },
        "$setOnInsert": {
            "user_id": user_id,
            "date": today_date,
            "created_at": now,
        },
    }
    result = mongo.mood_logs.update_one(filter_doc, update_doc, upsert=True)

    if result.upserted_id:
        log_id = str(result.upserted_id)
    else:
        doc = mongo.mood_logs.find_one(filter_doc, {"_id": 1})
        log_id = str(doc["_id"]) if doc else "unknown"

    context = aggregation_service.build_context(
        user_id, log_types=["mood", "sleep", "workouts"], days=7
    )

    new_entry = {"mood_score": mood_score, "note": clean_note, "date": today_date}
    reaction = None
    try:
        from flask import current_app

        reaction = ai_service.get_reaction(
            "mood",
            context,
            new_entry,
            gemini_api_key=current_app.config.get("GEMINI_API_KEY", ""),
            timeout_seconds=current_app.config.get("GEMINI_TIMEOUT_SECONDS", 3),
        )
    except Exception:
        reaction = None

    return (
        {
            "log_id": log_id,
            "date": today_date,
            "mood_score": mood_score,
            "note": clean_note,
            "reaction": reaction,
        },
        201,
    )


def get_log_history(user_id: str, log_type: str, days: int = 7) -> tuple[dict, int]:
    """Return log history data for a given type.

    Purpose:
        Fetch historical log entries with a standard response envelope.
    Expected Input types:
        user_id (str), log_type (str), days (int).
    Expected Output:
        tuple[dict, int] with log history response and status 200.

    # TODO: [Logic-Issue-010]
    """
    collection_map = {
        "workout": mongo.workout_logs,
        "meal": mongo.meal_logs,
        "sleep": mongo.sleep_logs,
        "hydration": mongo.hydration_logs,
        "mood": mongo.mood_logs,
    }

    if log_type not in collection_map:
        return (
            {
                "error": "bad_request",
                "message": f"Unknown log_type '{log_type}'.",
            },
            400,
        )

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    collection = collection_map[log_type]

    cursor = collection.find(
        {"user_id": user_id, "logged_at": {"$gte": cutoff}},
        sort=[("logged_at", -1)],
    )

    entries = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        for key, val in doc.items():
            if isinstance(val, datetime):
                doc[key] = val.isoformat()
        entries.append(doc)

    return ({"log_type": log_type, "entries": entries, "count": len(entries)}, 200)
