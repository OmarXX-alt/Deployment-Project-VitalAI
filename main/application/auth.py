from __future__ import annotations

from flask import Blueprint, current_app, jsonify, make_response, request

from main.business import auth_service
from main.persistence.schemas import (
    LoginSchema,
    RegisterSchema,
    validate_schema,
)

auth_bp = Blueprint("auth", __name__)

register_schema = RegisterSchema()
login_schema = LoginSchema()


def _set_auth_cookie(response, token: str) -> None:
    cookie_name = current_app.config.get("AUTH_COOKIE_NAME", "vitalai_auth")
    response.set_cookie(
        cookie_name,
        token,
        httponly=True,
        secure=current_app.config.get("AUTH_COOKIE_SECURE", False),
        samesite=current_app.config.get("AUTH_COOKIE_SAMESITE", "Lax"),
        max_age=current_app.config.get("AUTH_COOKIE_MAX_AGE", 86400),
        path="/",
    )


def _clear_auth_cookie(response) -> None:
    cookie_name = current_app.config.get("AUTH_COOKIE_NAME", "vitalai_auth")
    response.delete_cookie(cookie_name, path="/")


@auth_bp.post("/api/register")
def register():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("register: missing or invalid JSON body")
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body is required.",
                }
            ),
            400,
        )

    validated, errors = validate_schema(register_schema, body)
    if errors:
        current_app.logger.info("register: validation_error %s", errors)
        return jsonify({"error": "validation_error", "fields": errors}), 422

    # Purpose:  Hash password, create user in MongoDB, issue JWT.
    # Delegated to: business.auth_service.register_user()
    # TODO: [Logic-Issue-001]
    response_body, status = auth_service.register_user(
        validated["display_name"],
        validated["email"],
        validated["password"],
        current_app.config.get("JWT_SECRET"),
        current_app.config.get("JWT_EXPIRY_HOURS", 24),
    )
    token = response_body.get("token") if isinstance(response_body, dict) else None
    if status in {200, 201} and token:
        safe_body = {
            key: value
            for key, value in response_body.items()
            if key != "token"
        }
        response = make_response(jsonify(safe_body), status)
        _set_auth_cookie(response, token)
        return response
    return jsonify(response_body), status


@auth_bp.post("/api/login")
def login():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("login: missing or invalid JSON body")
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body is required.",
                }
            ),
            400,
        )

    validated, errors = validate_schema(login_schema, body)
    if errors:
        current_app.logger.info("login: validation_error %s", errors)
        return jsonify({"error": "validation_error", "fields": errors}), 422

    # Purpose:  Authenticate user and issue JWT.
    # Delegated to: business.auth_service.login_user()
    # TODO: [Logic-Issue-002]
    response_body, status = auth_service.login_user(
        validated["email"],
        validated["password"],
        current_app.config.get("JWT_SECRET"),
        current_app.config.get("JWT_EXPIRY_HOURS", 24),
    )
    token = response_body.get("token") if isinstance(response_body, dict) else None
    if status == 200 and token:
        safe_body = {
            key: value
            for key, value in response_body.items()
            if key != "token"
        }
        response = make_response(jsonify(safe_body), status)
        _set_auth_cookie(response, token)
        return response
    return jsonify(response_body), status


@auth_bp.post("/api/logout")
def logout():
    response = make_response(jsonify({"success": True}), 200)
    _clear_auth_cookie(response)
    return response
