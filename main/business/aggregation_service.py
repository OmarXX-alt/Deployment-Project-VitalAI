from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bson import ObjectId

from main.persistence.extensions import mongo


def _utc_today_bounds() -> tuple[datetime, datetime]:
    """Return (start_of_today_utc, now_utc) for daily aggregations."""
    now = datetime.now(timezone.utc)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_of_today, now


def _date_str(dt: datetime) -> str:
    """Return YYYY-MM-DD string for a UTC datetime."""
    return dt.strftime("%Y-%m-%d")


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


def build_context(user_id: str, log_types=None, days: int = 7) -> dict:
    """Build the canonical context schema for AI prompts and analytics.

    Purpose:
        Aggregate recent logs and profile data into a standardized context.
    Expected Input types:
        user_id (str), log_types (Optional[list[str]]), days (int).
    Expected Output:
        dict containing the canonical context schema.

    # TODO: [Logic-Issue-010]
    Implementation checklist:
        1. load logs by type
        2. compute daily totals and trends
        3. load profile targets
        4. return canonical context schema

    This is the agreed output schema. Member 2 builds prompts against this shape.
    Any change must be communicated via a GitHub issue comment before implementation.
    """
    all_types = ["workouts", "meals", "sleep", "hydration", "mood"]
    requested = set(log_types or all_types)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    context: dict = {}

    try:
        user = mongo.users.find_one(
            {"_id": ObjectId(user_id)},
            {
                "daily_calorie_target": 1,
                "hydration_goal": 1,
                "wellness_goal": 1,
            },
        )
    except Exception:
        user = None

    context["profile"] = {
        "daily_calorie_target": user.get("daily_calorie_target") if user else None,
        "hydration_goal": user.get("hydration_goal") if user else None,
        "wellness_goal": user.get("wellness_goal") if user else None,
    }

    if "workouts" in requested:
        cursor = mongo.workout_logs.find(
            {"user_id": user_id, "logged_at": {"$gte": cutoff}},
            sort=[("logged_at", 1)],
        )
        entries = []
        by_day: dict[str, dict] = {}

        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            entries.append(doc)
            d = _date_str(doc["logged_at"])
            if d not in by_day:
                by_day[d] = {"count": 0, "total_minutes": 0, "intensities": []}
            by_day[d]["count"] += 1
            by_day[d]["total_minutes"] += doc.get("duration_minutes", 0)
            by_day[d]["intensities"].append(doc.get("intensity", ""))

        context["workouts"] = {"entries": entries, "by_day": by_day}

    if "meals" in requested:
        pipeline = [
            {"$match": {"user_id": user_id, "logged_at": {"$gte": cutoff}}},
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
                    "entries": {"$push": "$$ROOT"},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        results = list(mongo.meal_logs.aggregate(pipeline))

        daily_totals: dict[str, int] = {}
        all_entries = []
        for result in results:
            date_key = result.get("_id")
            daily_totals[date_key] = int(result.get("total_kcal", 0))
            for entry in result.get("entries", []):
                entry["_id"] = str(entry["_id"])
                all_entries.append(entry)

        today_str = _date_str(now)
        today_total_kcal = daily_totals.get(today_str, 0)

        context["meals"] = {
            "entries": all_entries,
            "daily_totals": daily_totals,
            "today_total_kcal": today_total_kcal,
        }

    if "sleep" in requested:
        cursor = mongo.sleep_logs.find(
            {"user_id": user_id, "logged_at": {"$gte": cutoff}},
            sort=[("logged_at", 1)],
        )
        entries = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            entries.append(doc)

        durations = [e.get("duration_minutes", 0) for e in entries]
        qualities = [e.get("quality_score", 0) for e in entries]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        avg_quality = sum(qualities) / len(qualities) if qualities else 0.0

        if len(entries) < 4:
            trend = "insufficient_data"
        else:
            mid = len(entries) // 2
            older = entries[:mid]
            newer = entries[mid:]
            older_avg = (
                sum(e.get("quality_score", 0) for e in older) / len(older)
                if older
                else 0.0
            )
            newer_avg = (
                sum(e.get("quality_score", 0) for e in newer) / len(newer)
                if newer
                else 0.0
            )
            if newer_avg > older_avg + 0.3:
                trend = "improving"
            elif newer_avg < older_avg - 0.3:
                trend = "declining"
            else:
                trend = "stable"

        context["sleep"] = {
            "entries": entries,
            "avg_duration": round(avg_duration, 1),
            "avg_quality": round(avg_quality, 2),
            "trend": trend,
        }

    if "hydration" in requested:
        pipeline = [
            {"$match": {"user_id": user_id, "logged_at": {"$gte": cutoff}}},
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
                    "entries": {"$push": "$$ROOT"},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        results = list(mongo.hydration_logs.aggregate(pipeline))

        daily_totals: dict[str, int] = {}
        all_entries = []
        for result in results:
            date_key = result.get("_id")
            daily_totals[date_key] = int(result.get("total_ml", 0))
            for entry in result.get("entries", []):
                entry["_id"] = str(entry["_id"])
                all_entries.append(entry)

        today_str = _date_str(now)
        today_total_ml = daily_totals.get(today_str, 0)

        context["hydration"] = {
            "entries": all_entries,
            "daily_totals": daily_totals,
            "today_total_ml": today_total_ml,
        }

    if "mood" in requested:
        cursor = mongo.mood_logs.find(
            {"user_id": user_id, "logged_at": {"$gte": cutoff}},
            sort=[("logged_at", 1)],
        )
        entries = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            entries.append(doc)

        scores = [e.get("mood_score", 0) for e in entries]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        if len(entries) < 4:
            trend = "insufficient_data"
        else:
            mid = len(entries) // 2
            older = entries[:mid]
            newer = entries[mid:]
            older_avg = (
                sum(e.get("mood_score", 0) for e in older) / len(older)
                if older
                else 0.0
            )
            newer_avg = (
                sum(e.get("mood_score", 0) for e in newer) / len(newer)
                if newer
                else 0.0
            )
            if newer_avg > older_avg + 0.3:
                trend = "improving"
            elif newer_avg < older_avg - 0.3:
                trend = "declining"
            else:
                trend = "stable"

        context["mood"] = {
            "entries": entries,
            "avg_score": round(avg_score, 2),
            "trend": trend,
        }

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

    daily_sleep: dict[str, float] = {}
    for entry in context["sleep"]["entries"]:
        d = _date_str(entry["logged_at"])
        daily_sleep[d] = daily_sleep.get(d, 0.0) + (
            entry.get("duration_minutes", 0) / 60
        )
    sleep_duration_7d = _fill_7_day_series(daily_sleep, "hours", 0.0)
    for point in sleep_duration_7d:
        point["hours"] = round(point["hours"], 1)

    calorie_target = context["profile"]["daily_calorie_target"]
    raw_kcal = context["meals"]["daily_totals"]
    calories_7d = _fill_7_day_series(raw_kcal, "kcal", 0)
    for point in calories_7d:
        point["target"] = calorie_target

    raw_counts = {
        d: info["count"] for d, info in context["workouts"]["by_day"].items()
    }
    workout_count_7d = _fill_7_day_series(raw_counts, "count", 0)

    hydration_goal = context["profile"]["hydration_goal"]
    raw_ml = context["hydration"]["daily_totals"]
    hydration_7d = _fill_7_day_series(raw_ml, "ml", 0)
    for point in hydration_7d:
        point["goal"] = hydration_goal
        if hydration_goal and hydration_goal > 0:
            point["pct_of_goal"] = round((point["ml"] / hydration_goal) * 100, 1)
        else:
            point["pct_of_goal"] = None

    raw_mood: dict[str, float] = {}
    for entry in context["mood"]["entries"]:
        d = entry.get("date") or _date_str(entry["logged_at"])
        raw_mood[d] = entry.get("mood_score", 0)
    mood_7d = _fill_7_day_series(raw_mood, "score", None)

    today_ml = context["hydration"]["today_total_ml"]
    if hydration_goal and hydration_goal > 0:
        today_hydration_pct = round((today_ml / hydration_goal) * 100, 1)
    else:
        today_hydration_pct = None

    return {
        "sleep_duration_7d": sleep_duration_7d,
        "calories_7d": calories_7d,
        "workout_count_7d": workout_count_7d,
        "hydration_7d": hydration_7d,
        "mood_7d": mood_7d,
        "today_hydration_pct": today_hydration_pct,
    }
