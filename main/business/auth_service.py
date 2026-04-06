from __future__ import annotations

from datetime import datetime, timedelta, timezone

from persistence.extensions import mongo
from persistence.models import UserDocument, UserPublic


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
    _ = (mongo, UserDocument)
    return (
        {
            "token": "stub.jwt.token",
            "user_id": "stub_001",
            "display_name": display_name,
        },
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
    _ = (mongo, UserPublic)
    return ({"token": "stub.jwt.token", "display_name": "Stub User"}, 200)


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
    _ = (mongo, UserPublic)
    return (
        {
            "user_id": user_id,
            "display_name": "Stub User",
            "email": "stub@example.com",
            "daily_calorie_target": None,
            "hydration_goal": None,
            "wellness_goal": None,
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
    _ = (mongo, UserPublic)
    return (
        {
            "user_id": user_id,
            "display_name": updates.get("display_name") or "Stub User",
            "email": "stub@example.com",
            "daily_calorie_target": updates.get("daily_calorie_target"),
            "hydration_goal": updates.get("hydration_goal"),
            "wellness_goal": updates.get("wellness_goal"),
        },
        200,
    )
