from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from main.persistence.repositories import (
    hydration_repository,
    meal_repository,
    mood_repository,
    sleep_repository,
    user_repository,
    workout_repository,
)

# Note: No changes detected in main/business/utils/validators.py or
# main/business/utils/serialization.py; this file is new in persistence/utils.


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _group_by_day(logs: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for log in logs:
        value = log.get(key)
        dt_value = _parse_iso_datetime(value) if isinstance(value, str) else None
        if dt_value is None:
            continue
        day_key = dt_value.date().isoformat()
        grouped.setdefault(day_key, []).append(log)
    return grouped


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _sleep_summary(logs: list[dict]) -> str:
    durations = [log.get("duration_hrs") for log in logs if isinstance(log.get("duration_hrs"), (int, float))]
    qualities = [log.get("quality") for log in logs if isinstance(log.get("quality"), (int, float))]
    avg_duration = _average([float(value) for value in durations])
    avg_quality = _average([float(value) for value in qualities])
    if avg_duration is None or avg_quality is None:
        return "No sleep logs in the last 7 days"
    return f"Avg {avg_duration:.1f} hrs/night, avg quality {avg_quality:.1f}/5 over 7 days"


def _workout_summary(logs: list[dict]) -> str:
    if not logs:
        return "No workouts logged in the last 7 days"
    intensity_counts = {"high": 0, "medium": 0, "low": 0}
    for log in logs:
        intensity = log.get("intensity")
        if isinstance(intensity, str):
            key = intensity.strip().lower()
            if key in intensity_counts:
                intensity_counts[key] += 1
    total_sessions = len(logs)
    return (
        f"{total_sessions} sessions: {intensity_counts['high']} high, "
        f"{intensity_counts['medium']} medium, {intensity_counts['low']} low intensity"
    )


def _calorie_summary(logs: list[dict]) -> str:
    if not logs:
        return "No meals logged in the last 7 days"
    grouped = _group_by_day(logs, "logged_at")
    daily_totals: list[float] = []
    for day_logs in grouped.values():
        total = 0.0
        for log in day_logs:
            calories = log.get("calories")
            if isinstance(calories, (int, float)):
                total += float(calories)
        daily_totals.append(total)
    avg_daily = _average(daily_totals)
    days_logged = len(grouped)
    if avg_daily is None:
        return "No meals logged in the last 7 days"
    return f"Avg {avg_daily:.0f} kcal/day, logged {days_logged} of 7 days"


def _hydration_summary(logs: list[dict], goal_ml: int | None) -> str:
    if not logs:
        return "No hydration logs in the last 7 days"
    grouped = _group_by_day(logs, "logged_at")
    daily_totals: list[float] = []
    goal_hits = 0
    for day_logs in grouped.values():
        day_total = 0.0
        for log in day_logs:
            daily_total_ml = log.get("daily_total_ml")
            if isinstance(daily_total_ml, (int, float)):
                day_total = max(day_total, float(daily_total_ml))
        daily_totals.append(day_total)
        if goal_ml is not None and day_total >= goal_ml:
            goal_hits += 1
    avg_daily = _average(daily_totals)
    days_logged = len(grouped)
    if avg_daily is None:
        return "No hydration logs in the last 7 days"
    if goal_ml is None:
        return f"Avg {avg_daily:.0f} ml/day, logged {days_logged} of 7 days"
    return f"Avg {avg_daily:.0f} ml/day, goal hit {goal_hits} of 7 days"


def _mood_summary(mood_logs: list[dict], sleep_logs: list[dict]) -> str:
    if not mood_logs:
        return "No mood logs in the last 7 days"
    ratings = [log.get("mood_rating") for log in mood_logs if isinstance(log.get("mood_rating"), (int, float))]
    avg_mood = _average([float(value) for value in ratings])
    if avg_mood is None:
        return "No mood logs in the last 7 days"
    sleep_by_day: dict[str, float] = {}
    for log in sleep_logs:
        end_value = log.get("sleep_end")
        duration = log.get("duration_hrs")
        if isinstance(duration, (int, float)) and isinstance(end_value, str):
            end_dt = _parse_iso_datetime(end_value)
            if end_dt is not None:
                sleep_by_day[end_dt.date().isoformat()] = float(duration)
    high_sleep_days = {day for day, duration in sleep_by_day.items() if duration >= 7.5}
    mood_after_sleep = []
    for log in mood_logs:
        logged_at = log.get("logged_at")
        rating = log.get("mood_rating")
        if not isinstance(rating, (int, float)):
            continue
        dt_value = _parse_iso_datetime(logged_at) if isinstance(logged_at, str) else None
        if dt_value is None:
            continue
        if dt_value.date().isoformat() in high_sleep_days:
            mood_after_sleep.append(float(rating))
    if mood_after_sleep and _average(mood_after_sleep) >= avg_mood:
        return f"Avg mood {avg_mood:.1f}/5, best days follow 7.5+ hr sleep"
    return f"Avg mood {avg_mood:.1f}/5 over 7 days"


def get_user_context(user_id: str, log_type: str = "all") -> dict[str, str]:
    """
    Build a 7-day user context summary for Gemini prompts.

    Parameters:
        user_id: User identifier as a string.
        log_type: One of 'all', 'workout', 'meal', 'sleep', 'hydration', 'mood'.

    Returns:
        A dict of human-readable summary strings keyed by summary type.
    """
    allowed_types = {"all", "workout", "meal", "sleep", "hydration", "mood"}
    if log_type not in allowed_types:
        raise ValueError("log_type must be one of: all, workout, meal, sleep, hydration, mood")

    context: dict[str, str] = {}
    if log_type in {"all", "sleep"}:
        sleep_logs = sleep_repository.find_recent(user_id)
        context["sleep_summary"] = _sleep_summary(sleep_logs)
    else:
        sleep_logs = []

    if log_type in {"all", "workout"}:
        workout_logs = workout_repository.find_recent(user_id)
        context["workout_summary"] = _workout_summary(workout_logs)

    if log_type in {"all", "meal"}:
        meal_logs = meal_repository.find_recent(user_id)
        context["calorie_summary"] = _calorie_summary(meal_logs)

    if log_type in {"all", "hydration"}:
        hydration_logs = hydration_repository.find_recent(user_id)
        user_doc = user_repository.find_by_id(user_id)
        goal_ml = None
        if isinstance(user_doc, dict):
            goal_value = user_doc.get("hydration_goal_ml")
            if isinstance(goal_value, (int, float)):
                goal_ml = int(goal_value)
        context["hydration_summary"] = _hydration_summary(hydration_logs, goal_ml)

    if log_type in {"all", "mood"}:
        mood_logs = mood_repository.find_recent(user_id)
        if not sleep_logs:
            sleep_logs = sleep_repository.find_recent(user_id)
        context["mood_summary"] = _mood_summary(mood_logs, sleep_logs)

    return context


def format_context_for_prompt(context: dict[str, str]) -> str:
    """
    Convert a context dict into a compact multi-line prompt preface.

    Parameters:
        context: A dict produced by get_user_context.

    Returns:
        A multi-line string under 200 tokens for prompt injection.
    """
    ordered_keys = [
        "sleep_summary",
        "workout_summary",
        "calorie_summary",
        "hydration_summary",
        "mood_summary",
    ]
    lines = []
    for key in ordered_keys:
        if key in context:
            lines.append(f"- {context[key]}")
    for key, value in context.items():
        if key not in ordered_keys:
            lines.append(f"- {value}")
    return "\n".join(lines[:5])