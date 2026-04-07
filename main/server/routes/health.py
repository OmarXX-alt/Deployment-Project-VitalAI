"""Health check endpoints isolated from persistence layers."""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """Unconditional probe ensuring container viability."""
    # FIX: No DB connections or get_db() calls happen here (Rule 3)
    return jsonify({"status": "ok"}), 200
