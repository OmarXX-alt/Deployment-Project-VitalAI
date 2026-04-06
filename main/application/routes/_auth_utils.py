import functools
import logging

import jwt
from flask import current_app, jsonify, request

logger = logging.getLogger(__name__)


def login_required(f):
    """
    Decorator that validates the JWT token from the Authorization header.

    Expected header:
        Authorization: Bearer <token>

    On success the wrapped function receives `current_user_id` as a keyword argument.
    Returns 401 if the token is missing, expired, or invalid.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"message": "Missing or invalid authorization token."}), 401

        token = auth_header.split(" ", 1)[1]
        secret = current_app.config.get("SECRET_KEY", "dev-secret")

        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token. Please log in again."}), 401

        return f(*args, current_user_id=payload["sub"], **kwargs)

    return decorated
