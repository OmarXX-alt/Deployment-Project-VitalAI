from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from main.persistence.extensions import mongo


def register_user(
    display_name: str,
    email: str,
    password: str,
    jwt_secret: str,
    jwt_expiry_hours: int,
) -> tuple[dict, int]:
    """Register a new user and issue a JWT.

    Purpose:
        Create a user account, hash the password, store the record in MongoDB,
        and return an auth token for subsequent requests.
    Expected Input types:
        display_name (str), email (str), password (str),
        jwt_secret (str), jwt_expiry_hours (int).
    Expected Output:
        tuple[dict, int] with {"token", "user_id", "display_name"} and status.

    # TODO: [Logic-Issue-001]
    Implementation checklist:
        1. bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
        2. Build UserDocument, mongo.users.insert_one() — catch DuplicateKeyError → 409
        3. Issue JWT: payload = {"user_id": str(inserted_id), "exp": now+expiry}
        4. Return {"token", "user_id", "display_name"}, 201
    """
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt(rounds=12)
    ).decode("utf-8")

    now = datetime.now(timezone.utc)
    clean_display_name = display_name.strip()
    doc = {
        "display_name": clean_display_name,
        "email": email.lower().strip(),
        "password_hash": password_hash,
        "daily_calorie_target": None,
        "hydration_goal": None,
        "wellness_goal": None,
        "last_briefing_date": None,
        "created_at": now,
    }

    try:
        result = mongo.users.insert_one(doc)
        inserted_id = str(result.inserted_id)
    except DuplicateKeyError:
        return (
            {
                "error": "email_conflict",
                "message": "An account with this email already exists.",
            },
            409,
        )

    exp = datetime.now(timezone.utc) + timedelta(hours=jwt_expiry_hours)
    token = jwt.encode(
        {"user_id": inserted_id, "exp": exp},
        jwt_secret,
        algorithm="HS256",
    )

    return (
        {"token": token, "user_id": inserted_id, "display_name": clean_display_name},
        201,
    )


def login_user(
    email: str,
    password: str,
    jwt_secret: str,
    jwt_expiry_hours: int,
) -> tuple[dict, int]:
    """Authenticate a user and issue a JWT.

    Purpose:
        Verify credentials and return a signed JWT for session management.
    Expected Input types:
        email (str), password (str), jwt_secret (str), jwt_expiry_hours (int).
    Expected Output:
        tuple[dict, int] with {"token", "display_name"} and status.

    # TODO: [Logic-Issue-002]
    Implementation checklist:
        1. find_one(email)
        2. checkpw(password, stored_hash)
        3. issue JWT with expiry
        4. return token + display_name
    """
    generic_401 = (
        {
            "error": "invalid_credentials",
            "message": "Invalid email or password.",
        },
        401,
    )

    user = mongo.users.find_one({"email": email.lower().strip()})
    if user is None:
        return generic_401

    stored_hash = user["password_hash"]
    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        return generic_401

    user_id = str(user["_id"])
    exp = datetime.now(timezone.utc) + timedelta(hours=jwt_expiry_hours)
    token = jwt.encode(
        {"user_id": user_id, "exp": exp},
        jwt_secret,
        algorithm="HS256",
    )

    return ({"token": token, "display_name": user["display_name"]}, 200)


def get_profile(user_id: str) -> tuple[dict, int]:
    """Return the authenticated user's profile.

    Purpose:
        Fetch a user profile and return a safe projection.
    Expected Input types:
        user_id (str).
    Expected Output:
        tuple[dict, int] shaped as UserPublic with status.

    # TODO: [Logic-Issue-004a]
    Implementation checklist:
        1. find_one(_id)
        2. project out password_hash
        3. return UserPublic
    """
    try:
        user = mongo.users.find_one({"_id": ObjectId(user_id)})
    except InvalidId:
        return ({"error": "not_found", "message": "User not found."}, 404)

    if user is None:
        return ({"error": "not_found", "message": "User not found."}, 404)

    return (
        {
            "user_id": str(user["_id"]),
            "display_name": user["display_name"],
            "email": user["email"],
            "daily_calorie_target": user.get("daily_calorie_target"),
            "hydration_goal": user.get("hydration_goal"),
            "wellness_goal": user.get("wellness_goal"),
        },
        200,
    )


def update_profile(user_id: str, updates: dict) -> tuple[dict, int]:
    """Update the authenticated user's profile fields.

    Purpose:
        Apply partial updates to the user profile and return the updated record.
    Expected Input types:
        user_id (str), updates (dict).
    Expected Output:
        tuple[dict, int] shaped as UserPublic with status.

    # TODO: [Logic-Issue-004b]
    Implementation checklist:
        1. strip None values
        2. $set update
        3. re-fetch
        4. return UserPublic
    """
    clean: dict = {}
    str_fields = {"display_name", "wellness_goal"}
    for key, value in updates.items():
        if value is None:
            continue
        clean[key] = value.strip() if key in str_fields else value

    if not clean:
        return get_profile(user_id)

    try:
        mongo.users.update_one({"_id": ObjectId(user_id)}, {"$set": clean})
    except InvalidId:
        return ({"error": "not_found", "message": "User not found."}, 404)

    return get_profile(user_id)
