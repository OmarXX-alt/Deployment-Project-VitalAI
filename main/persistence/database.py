"""Compatibility shim for legacy imports.

Use main.persistence.db as the canonical DB extension module.
"""

from main.persistence.db import DatabaseConnection, db, get_db

__all__ = ["DatabaseConnection", "db", "get_db"]
