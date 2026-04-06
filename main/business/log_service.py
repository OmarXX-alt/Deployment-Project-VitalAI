from __future__ import annotations

from datetime import datetime, timezone

from persistence.extensions import mongo
from persistence.models import (
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
    _ = (mongo, WorkoutLogDocument)
    return (
        {
            "log_id": "stub_workout_001",
            "exercise_type": exercise_type,
            "duration_minutes": duration_minutes,
            "sets": sets,
            "reps": reps,
            "intensity": intensity,
            "logged_at": _to_iso(logged_at),
            "reaction": None,
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
    _ = (mongo, MealLogDocument)
    return (
        {
            "log_id": "stub_meal_001",
            "meal_name": meal_name,
            "calories": calories,
            "meal_type": meal_type,
            "logged_at": _to_iso(logged_at),
            "today_total_kcal": calories,
            "reaction": None,
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
    _ = (mongo, SleepLogDocument)
    duration_minutes = 0
    if isinstance(sleep_start, datetime) and isinstance(sleep_end, datetime):
        duration_minutes = int((sleep_end - sleep_start).total_seconds() / 60)
    return (
        {
            "log_id": "stub_sleep_001",
            "sleep_start": _to_iso(sleep_start),
            "sleep_end": _to_iso(sleep_end),
            "duration_minutes": duration_minutes,
            "quality_score": quality_score,
            "reaction": None,
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
    _ = (mongo, HydrationLogDocument)
    return (
        {
            "log_id": "stub_hydration_001",
            "amount_ml": amount_ml,
            "logged_at": _to_iso(logged_at),
            "daily_total_ml": amount_ml,
            "pct_of_goal": None,
            "reaction": None,
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
    _ = (mongo, MoodLogDocument)
    today = datetime.now(timezone.utc).date().isoformat()
    return (
        {
            "log_id": "stub_mood_001",
            "date": today,
            "mood_score": mood_score,
            "note": note,
            "reaction": None,
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
    _ = mongo
    return ({"log_type": log_type, "entries": [], "count": 0}, 200)
