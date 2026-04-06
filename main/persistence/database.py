"""Compatibility shim for legacy imports.

Use persistence.extensions as the canonical DB extension module.
"""

from __future__ import annotations

from .extensions import MongoDB, mongo

DatabaseConnection = MongoDB
db = mongo


def get_db():
    if db.db is None:
        raise RuntimeError("Database not initialised. Call db.init_app(app) first.")
    return db.db


__all__ = ["DatabaseConnection", "db", "get_db"]
