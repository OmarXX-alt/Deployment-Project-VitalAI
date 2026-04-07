from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bson import ObjectId

from main.persistence.extensions import mongo


def _utc_today_bounds() -> tuple[datetime, datetime]:
    """Return (start_of_today_utc, now_utc) for daily aggregations."""
    now = datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_of_today, now


def _date_str(dt: datetime | str) -> str:
    """Return YYYY-MM-DD string for a UTC datetime."""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d")
    if isinstance(dt, str):
        try:
            parsed = datetime.fromisoformat(dt)
        except ValueError:
            return dt[:10] if len(dt) >= 10 else dt
        if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.strftime("%Y-%m-%d")
    return ""


def _fill_7_day_series(
    data: dict[str, object], key: str, default: object
) -> list[dict]:
    today = datetime.now(timezone.utc).date()
    series = []
    for offset in range(6, -1, -1):
        d = today - timedelta(days=offset)
        date_s = d.isoformat()
        series.append({"date": date_s, key: data.get(date_s, default)})
    return series


def _serialize_value(value: object) -> object:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    return value


def _serialize_doc(doc: dict) -> dict:
    return {key: _serialize_value(value) for key, value in doc.items()}


def _secure_match(user_id: str) -> dict:
    """Return a scoped query filter for an authenticated user."""
    return {"user_id": str(user_id)}


def _window_dates(now: datetime, days: int) -> list[str]:
    today = now.date()
    return [
        (today - timedelta(days=offset)).isoformat()
        for offset in range(days - 1, -1, -1)
    ]


def _series_from_dict(
    dates: list[str], data: dict[str, float], key: str, default: float
) -> list[dict]:
    return [{"date": date, key: data.get(date, default)} for date in dates]


def _coerce_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    return None


def _normalize_log_types(log_type, log_types) -> set[str]:
    all_types = {"workouts", "meals", "sleep", "hydration", "mood"}
    if log_types is None and log_type:
        log_types = [log_type]
    if log_types is None:
        return set(all_types)
    normalized: set[str] = set()
    mapping = {
        "workout": "workouts",
        "meal": "meals",
        "sleep": "sleep",
        "hydration": "hydration",
        "mood": "mood",
        "workouts": "workouts",
        "meals": "meals",
    }
    for entry in log_types:
        if not isinstance(entry, str):
            continue
        key = mapping.get(entry.strip().lower())
        if key:
            normalized.add(key)
    return normalized or set(all_types)


def _fill_days(
    data: dict[str, object], default: object, days: int
) -> dict[str, object]:
    today = datetime.now(timezone.utc).date()
    filled: dict[str, object] = {}
    for offset in range(days - 1, -1, -1):
        d = today - timedelta(days=offset)
        date_s = d.isoformat()
        filled[date_s] = data.get(date_s, default)
    return filled


def _fill_workout_days(by_day: dict[str, dict], days: int) -> dict[str, dict]:
    today = datetime.now(timezone.utc).date()
    filled: dict[str, dict] = {}
    for offset in range(days - 1, -1, -1):
        d = today - timedelta(days=offset)
        date_s = d.isoformat()
        if date_s in by_day:
            filled[date_s] = by_day[date_s]
        else:
            filled[date_s] = {
                "count": 0,
                "total_minutes": 0,
                "intensities": [],
            }
    return filled


def build_context(
    user_id: str,
    log_type=None,
    log_types=None,
    days: int = 7,
) -> dict:
    """Build a 7-day reactive context summary for AI prompts.

    Purpose:
        Aggregate recent logs and profile data into a compact, flat summary.
    Expected Input types:
        user_id (str), log_type (Optional[str]),
        log_types (Optional[list[str]]), days (int).
    Expected Output:
        dict containing the reactive context summary.
    """
    requested = _normalize_log_types(log_type, log_types)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=days * 24)
    date_keys = _window_dates(now, days)

    context: dict = {
        "window_days": days,
        "window_start_utc": cutoff.isoformat(),
        "window_end_utc": now.isoformat(),
        "daily_calorie_target": None,
        "hydration_goal_ml": None,
        "wellness_goal": None,
        "meal_daily_kcal": _series_from_dict(
            date_keys, {}, "kcal", 0
        ),
        "meal_avg_kcal": 0.0,
        "meal_days_logged": 0,
        "sleep_daily_hours": _series_from_dict(
            date_keys, {}, "hours", 0.0
        ),
        "sleep_avg_duration_hours": 0.0,
        "sleep_avg_quality_score": 0.0,
        "hydration_daily_ml": _series_from_dict(
            date_keys, {}, "ml", 0.0
        ),
        "hydration_today_ml": 0.0,
        "hydration_pct_of_goal": None,
        "workout_daily_count": _series_from_dict(
            date_keys, {}, "count", 0
        ),
        "workout_sessions": 0,
        "workout_avg_intensity": None,
        "workout_avg_intensity_label": None,
        "mood_daily_score": _series_from_dict(
            date_keys, {}, "score", None
        ),
        "mood_avg_score": None,
    }

    try:
        user = mongo.users.find_one(
            {"_id": ObjectId(user_id)},
            {
                "daily_calorie_target": 1,
                "hydration_goal": 1,
                "hydration_goal_ml": 1,
                "wellness_goal": 1,
            },
        )
    except Exception:
        user = None

    if user:
        context["daily_calorie_target"] = user.get("daily_calorie_target")
        context["hydration_goal_ml"] = user.get("hydration_goal")
        if context["hydration_goal_ml"] is None:
            context["hydration_goal_ml"] = user.get("hydration_goal_ml")
        context["wellness_goal"] = user.get("wellness_goal")

    if "meals" in requested:
        pipeline = [
            {
                "$match": {
                    **_secure_match(user_id),
                    "logged_at": {"$gte": cutoff},
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$logged_at",
                            "timezone": "UTC",
                        }
                    },
                    "total_kcal": {"$sum": "$calories"},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        results = list(mongo.meal_logs.aggregate(pipeline))
        daily_totals: dict[str, float] = {
            result.get("_id"): float(result.get("total_kcal", 0))
            for result in results
            if result.get("_id")
        }
        context["meal_daily_kcal"] = _series_from_dict(
            date_keys, daily_totals, "kcal", 0.0
        )
        kcal_values = [point["kcal"] for point in context["meal_daily_kcal"]]
        context["meal_avg_kcal"] = (
            sum(kcal_values) / len(kcal_values) if kcal_values else 0.0
        )
        context["meal_days_logged"] = sum(
            1 for point in context["meal_daily_kcal"] if point["kcal"] > 0
        )

    if "sleep" in requested:
        cursor = mongo.sleep_logs.find(
            {**_secure_match(user_id), "logged_at": {"$gte": cutoff}},
            sort=[("logged_at", 1)],
        )
        durations: list[float] = []
        qualities: list[float] = []
        by_day: dict[str, float] = {}
        for doc in cursor:
            sleep_start = _coerce_datetime(doc.get("sleep_start"))
            sleep_end = _coerce_datetime(doc.get("sleep_end"))
            duration_minutes = doc.get("duration_minutes")
            duration_hours = None
            if sleep_start and sleep_end:
                duration_hours = (
                    sleep_end - sleep_start
                ).total_seconds() / 3600
            elif isinstance(duration_minutes, (int, float)):
                duration_hours = float(duration_minutes) / 60.0
            if isinstance(duration_hours, (int, float)):
                durations.append(float(duration_hours))
                day_key = _date_str(
                    doc.get("logged_at") or sleep_start or sleep_end
                )
                if day_key:
                    by_day[day_key] = by_day.get(day_key, 0.0) + float(
                        duration_hours
                    )
            quality = doc.get("quality_score", doc.get("quality"))
            if isinstance(quality, (int, float)):
                qualities.append(float(quality))
        context["sleep_daily_hours"] = _series_from_dict(
            date_keys, by_day, "hours", 0.0
        )
        context["sleep_avg_duration_hours"] = (
            sum(durations) / len(durations) if durations else 0.0
        )
        context["sleep_avg_quality_score"] = (
            sum(qualities) / len(qualities) if qualities else 0.0
        )

    if "hydration" in requested:
        pipeline = [
            {
                "$match": {
                    **_secure_match(user_id),
                    "logged_at": {"$gte": cutoff},
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$logged_at",
                            "timezone": "UTC",
                        }
                    },
                    "total_ml": {"$sum": "$amount_ml"},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        results = list(mongo.hydration_logs.aggregate(pipeline))
        daily_totals = {
            result.get("_id"): float(result.get("total_ml", 0))
            for result in results
            if result.get("_id")
        }
        context["hydration_daily_ml"] = _series_from_dict(
            date_keys, daily_totals, "ml", 0.0
        )
        today_key = date_keys[-1] if date_keys else _date_str(now)
        context["hydration_today_ml"] = float(daily_totals.get(today_key, 0))
        goal = context.get("hydration_goal_ml")
        if isinstance(goal, (int, float)) and goal > 0:
            context["hydration_pct_of_goal"] = round(
                (context["hydration_today_ml"] / goal) * 100, 1
            )

    if "workouts" in requested:
        cursor = mongo.workout_logs.find(
            {**_secure_match(user_id), "logged_at": {"$gte": cutoff}},
            sort=[("logged_at", 1)],
        )
        by_day: dict[str, float] = {}
        intensity_values: list[float] = []
        intensity_map = {"low": 1.0, "moderate": 2.0, "high": 3.0}
        for doc in cursor:
            context["workout_sessions"] += 1
            logged_at = doc.get("logged_at")
            day_key = _date_str(logged_at) if logged_at else None
            if day_key:
                by_day[day_key] = by_day.get(day_key, 0) + 1
            intensity = doc.get("intensity")
            if isinstance(intensity, str):
                intensity_value = intensity_map.get(intensity.strip().lower())
                if intensity_value:
                    intensity_values.append(intensity_value)
        context["workout_daily_count"] = _series_from_dict(
            date_keys, by_day, "count", 0
        )
        if intensity_values:
            avg_intensity = sum(intensity_values) / len(intensity_values)
            context["workout_avg_intensity"] = round(avg_intensity, 2)
            if avg_intensity < 1.5:
                context["workout_avg_intensity_label"] = "low"
            elif avg_intensity < 2.5:
                context["workout_avg_intensity_label"] = "moderate"
            else:
                context["workout_avg_intensity_label"] = "high"

    if "mood" in requested:
        cursor = mongo.mood_logs.find(
            {**_secure_match(user_id), "logged_at": {"$gte": cutoff}},
            sort=[("logged_at", 1)],
        )
        scores: list[float] = []
        by_day: dict[str, list[float]] = {}
        for doc in cursor:
            score = doc.get("mood_score", doc.get("mood_rating"))
            if isinstance(score, (int, float)):
                scores.append(float(score))
            date_value = doc.get("date")
            day_key = None
            if isinstance(date_value, str):
                day_key = date_value[:10]
            if not day_key:
                logged_at = doc.get("logged_at")
                day_key = _date_str(logged_at) if logged_at else None
            if day_key and isinstance(score, (int, float)):
                by_day.setdefault(day_key, []).append(float(score))
        mood_daily: dict[str, float] = {}
        for day, values in by_day.items():
            mood_daily[day] = sum(values) / len(values) if values else 0.0
        context["mood_daily_score"] = _series_from_dict(
            date_keys, mood_daily, "score", None
        )
        context["mood_avg_score"] = (
            sum(scores) / len(scores) if scores else None
        )

    return context


def get_dashboard_data(user_id: str) -> dict:
    """Return dashboard data for the authenticated user.

    Purpose:
        Provide the aggregated dashboard payload for the UI.
    Expected Input types:
        user_id (str).
    Expected Output:
        dict with dashboard metrics and recent entries.

    # TODO: [Logic-Issue-012]
    """
    context = build_context(user_id, log_types=None, days=7)

    sleep_duration_7d = context["sleep_daily_hours"]
    for point in sleep_duration_7d:
        if isinstance(point.get("hours"), (int, float)):
            point["hours"] = round(point["hours"], 1)

    calorie_target = context["daily_calorie_target"]
    calories_7d = context["meal_daily_kcal"]
    for point in calories_7d:
        point["target"] = calorie_target

    workout_count_7d = context["workout_daily_count"]

    hydration_goal = context["hydration_goal_ml"]
    hydration_7d = context["hydration_daily_ml"]
    for point in hydration_7d:
        point["goal"] = hydration_goal
        if hydration_goal and hydration_goal > 0:
            point["pct_of_goal"] = round(
                (point["ml"] / hydration_goal) * 100, 1
            )
        else:
            point["pct_of_goal"] = None

    mood_7d = context["mood_daily_score"]

    today_hydration_pct = context.get("hydration_pct_of_goal")

    return {
        "sleep_duration_7d": sleep_duration_7d,
        "calories_7d": calories_7d,
        "workout_count_7d": workout_count_7d,
        "hydration_7d": hydration_7d,
        "mood_7d": mood_7d,
        "today_hydration_pct": today_hydration_pct,
    }
