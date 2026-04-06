import logging

import bcrypt
import jwt
from flask import Blueprint, current_app, jsonify, render_template, request
from datetime import datetime, timedelta, timezone

from main.persistence.repositories import user_repository

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


# ──────────────────────────────────────────────
# Page routes
# ──────────────────────────────────────────────

@auth_bp.get("/login")
def login_page():
    """Render the login page."""
    return render_template("login.html")


@auth_bp.get("/register")
def register_page():
    """Render the registration page."""
    return render_template("register.html")


# ──────────────────────────────────────────────
# API routes
# ──────────────────────────────────────────────

@auth_bp.post("/api/login")
def login():
    """
    Authenticate a user and return a JWT token.

    Request body (JSON):
        email    (str) – user's email address
        password (str) – plain-text password

    Returns 200 with {"token": <jwt>} on success.
    Returns 400 if fields are missing.
    Returns 401 if credentials are invalid.
    Returns 500 on unexpected server error.
    """
    body = request.get_json(silent=True) or {}
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")

    if not email or not password:
        return jsonify({"message": "Email and password are required."}), 400

    try:
        user = user_repository.find_by_email(email)
    except RuntimeError:
        logger.exception("login: repository error for email=%s", email)
        return jsonify({"message": "Server error. Please try again later."}), 500

    if not user:
        return jsonify({"message": "Invalid email or password."}), 401

    password_hash = user.get("password_hash", "")
    if not bcrypt.checkpw(password.encode(), password_hash.encode()):
        return jsonify({"message": "Invalid email or password."}), 401

    token = _generate_token(str(user["_id"]))
    return jsonify({"token": token}), 200


@auth_bp.post("/api/register")
def register():
    """
    Create a new user account and return a JWT token.

    Request body (JSON):
        displayName      (str)      – visible name
        email            (str)      – unique email address
        password         (str)      – must be ≥ 6 chars, contain a digit and special char
        calorieTarget    (int)      – daily calorie goal (default 2000)
        hydrationTarget  (int)      – daily hydration goal in ml (default 2500)
        wellnessGoal     (str|null) – optional wellness goal key

    Returns 201 with {"token": <jwt>, "success": true} on success.
    Returns 400 on validation failure or duplicate email.
    Returns 500 on unexpected server error.
    """
    body = request.get_json(silent=True) or {}

    display_name = body.get("displayName", "").strip()
    email = body.get("email", "").strip().lower()
    password = body.get("password", "")
    calorie_target = int(body.get("calorieTarget") or 2000)
    hydration_target = int(body.get("hydrationTarget") or 2500)
    wellness_goal = body.get("wellnessGoal") or None

    # Basic server-side validation
    if not display_name:
        return jsonify({"message": "Display name is required."}), 400
    if not email or "@" not in email:
        return jsonify({"message": "A valid email address is required."}), 400
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters."}), 400

    try:
        existing = user_repository.find_by_email(email)
    except RuntimeError:
        logger.exception("register: repository error checking email=%s", email)
        return jsonify({"message": "Server error. Please try again later."}), 500

    if existing:
        return jsonify({"message": "An account with that email already exists."}), 400

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user_doc = {
        "display_name": display_name,
        "email": email,
        "password_hash": password_hash,
        "daily_calorie_target": calorie_target,
        "hydration_goal_ml": hydration_target,
        "wellness_goal": wellness_goal,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
    }

    try:
        inserted_id = user_repository.insert(user_doc)
    except RuntimeError:
        logger.exception("register: failed to insert user email=%s", email)
        return jsonify({"message": "Could not create account. Please try again."}), 500

    token = _generate_token(inserted_id)
    return jsonify({"token": token, "success": True}), 201


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _generate_token(user_id: str) -> str:
    """Return a signed JWT valid for 24 hours."""
    secret = current_app.config.get("SECRET_KEY", "dev-secret")
    payload = {
        "sub": user_id,
        "iat": datetime.now(tz=timezone.utc),
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, secret, algorithm="HS256")
