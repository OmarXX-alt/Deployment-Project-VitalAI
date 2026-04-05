import logging
import os

import certifi
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        """
        Initialize the MongoDB connection using the Flask app configuration.
        Connects to the 'vitalai' database on Atlas or a local instance.
        """
        mongo_uri = os.environ.get("MONGO_URI")
        if not mongo_uri:
            logger.warning("MONGO_URI not set; falling back to local MongoDB.")
            mongo_uri = "mongodb://localhost:27017/vitalai"
        app.config.setdefault("MONGO_URI", mongo_uri)

        try:
            self.client = MongoClient(
                app.config["MONGO_URI"],
                tlsCAFile=certifi.where(),      # resolves SSL handshake issues on Atlas
                serverSelectionTimeoutMS=5000,  # fail fast instead of hanging
            )

            # Verify the connection is reachable before the app starts serving
            self.client.admin.command("ping")

            # Use 'vitalai' as the default database
            self.db = self.client.get_default_database(default="vitalai")

            logger.debug("Connected to MongoDB database=%s", self.db.name)

        except ConfigurationError as e:
            logger.error("MongoDB configuration error: %s", e, exc_info=True)
            raise
        except ConnectionFailure as e:
            logger.error("Could not reach MongoDB: %s", e, exc_info=True)
            raise

        # Make db accessible via app context (app.db)
        app.db = self.db

        # Create indexes for common query patterns
        _create_indexes(self.db)


def _create_indexes(db):
    """
    Ensure indexes exist on fields that are queried on every request.
    Called once at startup — safe to re-run (MongoDB skips existing indexes).
    """
    # All log collections are queried by user_id + logged_at for 7-day aggregations
    log_collections = [
        "workout_logs",
        "meal_logs",
        "sleep_logs",
        "hydration_logs",
        "mood_logs",
    ]
    for col in log_collections:
        db[col].create_index([("user_id", 1), ("logged_at", -1)])

    # Users are looked up by email on every login/register
    db["users"].create_index("email", unique=True)

    # Wellness insights and goal plans are fetched by user_id
    db["wellness_insights"].create_index([("user_id", 1), ("generated_at", -1)])
    db["goal_plans"].create_index("user_id", unique=True)
    db["chat_sessions"].create_index([("user_id", 1), ("created_at", -1)])

    logger.debug("Indexes verified.")


# ── Global instance — import this across the app ──────────────────────────────

db_conn = DatabaseConnection()


def get_db():
    """
    Return the active vitalai database instance.
    Call this inside any route or service to access a collection:

        from database import get_db
        db = get_db()
        db.workout_logs.find({"user_id": user_id})
    """
    if db_conn.db is None:
        raise RuntimeError(
            "Database not initialised. Call db_conn.init_app(app) first."
        )
    return db_conn.db