from __future__ import annotations

from functools import wraps

import jwt
from flask import current_app, g, jsonify, request
from jwt import ExpiredSignatureError, InvalidTokenError


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        cookie_name = current_app.config.get("AUTH_COOKIE_NAME", "vitalai_auth")
        token = request.cookies.get(cookie_name)
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return (
                jsonify(
                    {
                        "error": "token_missing",
                        "message": "Authorization token is missing.",
                    }
                ),
                401,
            )

        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET"],
                algorithms=["HS256"],
            )
            g.user_id = payload["user_id"]
        except ExpiredSignatureError as exc:
            return (
                jsonify({"error": "token_expired", "message": str(exc)}),
                401,
            )
        except (InvalidTokenError, KeyError) as exc:
            return (
                jsonify({"error": "token_invalid", "message": str(exc)}),
                401,
            )

        return func(*args, **kwargs)

    return wrapper
