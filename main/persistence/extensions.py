from __future__ import annotations

import logging
import os

import certifi
from flask import Flask
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ConfigurationError
from pymongo.uri_parser import parse_uri

logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self) -> None:
        self.client: MongoClient | None = None
        self.db = None

    def init_app(self, app: Flask) -> None:
        # Priority: environment variable > app config > default
        mongo_uri = os.getenv("MONGO_URI") or app.config.get("MONGO_URI")
        if not mongo_uri:
            # Only fallback to localhost in non-production environments
            if os.getenv("FLASK_ENV") == "production":
                logger.error("MONGO_URI not set in production environment!")
                raise ValueError("MONGO_URI environment variable is required for production deployment.")
            logger.warning("MONGO_URI not set; falling back to local MongoDB.")
            mongo_uri = "mongodb://localhost:27017/vitalai"
        app.config.setdefault("MONGO_URI", mongo_uri)
        logger.info("MongoDB connection URI: %s", mongo_uri.split("@")[0] + "@..." if "@" in mongo_uri else mongo_uri)

        try:
            self.client = MongoClient(
                mongo_uri,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=5000,
            )

            # Verify the connection is reachable before the app starts serving
            self.client.admin.command("ping")

            parsed = parse_uri(mongo_uri)
            db_name = parsed.get("database") or "vitalai"
            self.db = self.client[db_name]

            logger.debug("Connected to MongoDB database=%s", self.db.name)

        except ConfigurationError as exc:
            logger.error("MongoDB configuration error: %s", exc, exc_info=True)
            raise
        except ConnectionFailure as exc:
            logger.error("Could not reach MongoDB: %s", exc, exc_info=True)
            raise

        app.db = self.db

        if not app.config.get("TESTING", False):
            self._bootstrap_indexes()

    def _require_db(self) -> None:
        if self.db is None:
            raise RuntimeError("MongoDB not initialized. Call mongo.init_app(app) first.")

    @property
    def users(self) -> Collection:
        self._require_db()
        return self.db["users"]

    @property
    def workout_logs(self) -> Collection:
        self._require_db()
        return self.db["workout_logs"]

    @property
    def meal_logs(self) -> Collection:
        self._require_db()
        return self.db["meal_logs"]

    @property
    def sleep_logs(self) -> Collection:
        self._require_db()
        return self.db["sleep_logs"]

    @property
    def hydration_logs(self) -> Collection:
        self._require_db()
        return self.db["hydration_logs"]

    @property
    def mood_logs(self) -> Collection:
        self._require_db()
        return self.db["mood_logs"]

    def _bootstrap_indexes(self) -> None:
        self._require_db()

        self.users.create_index("email", unique=True, name="uq_users_email")

        log_collections = [
            "workout_logs",
            "meal_logs",
            "sleep_logs",
            "hydration_logs",
            "mood_logs",
        ]
        for name in log_collections:
            self.db[name].create_index(
                [("user_id", 1), ("logged_at", -1)],
                name=f"idx_{name}_user_time",
            )

        self.mood_logs.create_index(
            [("user_id", 1), ("date", 1)],
            unique=True,
            name="uq_mood_user_date",
            partialFilterExpression={"date": {"$exists": True}},
        )

        self.db["wellness_insights"].create_index(
            [("user_id", 1), ("generated_at", -1)],
            name="idx_wellness_user_time",
        )
        self.db["goal_plans"].create_index(
            "user_id",
            unique=True,
            name="uq_goal_plans_user",
        )
        self.db["chat_sessions"].create_index(
            [("user_id", 1), ("created_at", -1)],
            name="idx_chat_sessions_user_time",
        )


mongo = MongoDB()
