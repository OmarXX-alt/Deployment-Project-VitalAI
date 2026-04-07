from __future__ import annotations

import logging

from pymongo.collection import Collection

from main.persistence.db import get_db

logger = logging.getLogger(__name__)


class MongoDB:
    """Lazy collection accessor that connects only on first use."""

    def __init__(self) -> None:
        self._indexes_ready = False

    def _collection(self, name: str) -> Collection:
        db = get_db()
        if not self._indexes_ready:
            self._bootstrap_indexes(db)
            self._indexes_ready = True
        return db[name]

    @property
    def users(self) -> Collection:
        return self._collection("users")

    @property
    def workout_logs(self) -> Collection:
        return self._collection("workout_logs")

    @property
    def meal_logs(self) -> Collection:
        return self._collection("meal_logs")

    @property
    def sleep_logs(self) -> Collection:
        return self._collection("sleep_logs")

    @property
    def hydration_logs(self) -> Collection:
        return self._collection("hydration_logs")

    @property
    def mood_logs(self) -> Collection:
        return self._collection("mood_logs")

    def _bootstrap_indexes(self, db) -> None:
        """Create indexes on first use; safe to call multiple times."""

        db["users"].create_index("email", unique=True, name="uq_users_email")

        log_collections = [
            "workout_logs",
            "meal_logs",
            "sleep_logs",
            "hydration_logs",
            "mood_logs",
        ]
        for name in log_collections:
            db[name].create_index(
                [("user_id", 1), ("logged_at", -1)],
                name=f"idx_{name}_user_time",
            )

        db["mood_logs"].create_index(
            [("user_id", 1), ("date", 1)],
            unique=True,
            name="uq_mood_user_date",
            partialFilterExpression={"date": {"$exists": True}},
        )

        db["wellness_insights"].create_index(
            [("user_id", 1), ("generated_at", -1)],
            name="idx_wellness_user_time",
        )
        db["goal_plans"].create_index(
            "user_id",
            unique=True,
            name="uq_goal_plans_user",
        )
        db["chat_sessions"].create_index(
            [("user_id", 1), ("created_at", -1)],
            name="idx_chat_sessions_user_time",
        )

        logger.debug("Indexes verified.")


mongo = MongoDB()
