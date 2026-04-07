"""Database connection manager with strict lazy evaluation."""

from flask import current_app
from pymongo import MongoClient

# Module-level singletons to enforce Rule 1
_client = None
_db = None


def get_db():
    """Lazily connect to MongoDB on the first request only."""
    global _client, _db

    # FIX: If connection already established, return it immediately
    if _db is not None:
        return _db

    # Setup the connection based on app config
    mongo_uri = current_app.config.get("MONGO_URI")
    db_name = current_app.config.get("DB_NAME", "vitalai")

    if not mongo_uri:
        raise ValueError("MONGO_URI is not set in application config")

    _client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    _db = _client[db_name]
    return _db


def close_db(e=None):
    """Close the database connection and clean up singletons."""
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None

