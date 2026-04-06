from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from business.auth_service import get_profile, update_profile
from persistence.schemas import ProfileUpdateSchema, validate_schema
from server.middleware.auth import require_auth


profile_bp = Blueprint("profile", __name__)

profile_schema = ProfileUpdateSchema()


@profile_bp.get("/api/profile")
@require_auth
def profile_get():
    # TODO: [Logic-Issue-004a]
    response_body, status = get_profile(g.user_id)
    return jsonify(response_body), status


@profile_bp.put("/api/profile")
@require_auth
def profile_update():
    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "invalid_json", "message": "Request body is required."}), 400

    validated, errors = validate_schema(profile_schema, body)
    if errors:
        return jsonify({"error": "validation_error", "fields": errors}), 422

    updates = {key: value for key, value in validated.items() if value is not None}

    # TODO: [Logic-Issue-004b]
    response_body, status = update_profile(g.user_id, updates)
    return jsonify(response_body), status
