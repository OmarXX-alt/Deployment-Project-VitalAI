from __future__ import annotations

import json
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, current_app, g, jsonify, request

from main.ai.gemini_client import call_gemini
from main.business import aggregation_service
from main.persistence.db import get_db
from main.persistence.models.chat_sessions import create_chat_session
from main.server.middleware.auth import require_auth

chat_bp = Blueprint("chat", __name__)

_FALLBACK_REPLY = (
    "I'm having trouble connecting right now. Please try again."
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _trim_messages(
    messages: list[dict[str, object]], max_messages: int = 20
) -> list[dict[str, object]]:
    if not isinstance(messages, list):
        return []
    if len(messages) <= max_messages:
        return messages
    return messages[-max_messages:]


def _simplify_context(context: dict) -> dict[str, object]:
    """Extract only essential metrics from full context to reduce token usage."""
    return {
        "meal_avg_kcal": context.get("meal_avg_kcal", 0),
        "meal_days_logged": context.get("meal_days_logged", 0),
        "sleep_avg_duration_hours": context.get("sleep_avg_duration_hours", 0),
        "sleep_avg_quality_score": context.get("sleep_avg_quality_score"),
        "hydration_today_ml": context.get("hydration_today_ml", 0),
        "hydration_pct_of_goal": context.get("hydration_pct_of_goal"),
        "workout_sessions": context.get("workout_sessions", 0),
        "workout_avg_intensity_label": context.get("workout_avg_intensity_label"),
        "mood_avg_score": context.get("mood_avg_score"),
        "wellness_goal": context.get("wellness_goal"),
    }


def _system_message(context: dict) -> dict[str, str]:
    simplified_context = _simplify_context(context)
    context_json = json.dumps(simplified_context, ensure_ascii=True)
    content = (
        "You are VitalAI, a concise wellness assistant. "
        "Go beyond summarizing by giving practical guidance and advice. "
        "Offer 1-3 actionable next steps tied to the 7-day summary. "
        "Avoid medical diagnosis; suggest professional help for urgent concerns. "
        "Use the 7-day health summary to answer clearly and safely. "
        f"7-day wellness summary: {context_json}"
    )
    return {"role": "system", "content": content}


def _format_prompt(messages: list[dict[str, object]]) -> str:
    lines: list[str] = []
    for message in messages:
        role = message.get("role")
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        if role == "system":
            lines.append(f"System: {content.strip()}")
        elif role == "assistant":
            lines.append(f"Assistant: {content.strip()}")
        else:
            lines.append(f"User: {content.strip()}")
    return "\n".join(lines).strip()


@chat_bp.post("/api/chat")
@require_auth
def chat():
    body = request.get_json(silent=True)
    if body is None:
        current_app.logger.info("chat: missing or invalid JSON body")
        return (
            jsonify(
                {
                    "error": "invalid_json",
                    "message": "Request body is required.",
                }
            ),
            400,
        )

    message = body.get("message")
    if not isinstance(message, str) or not message.strip():
        return (
            jsonify(
                {
                    "error": "invalid_message",
                    "message": "message is required.",
                }
            ),
            400,
        )

    message = message.strip()
    session_id = body.get("session_id")
    skip_context = body.get("lightweight", False)

    try:
        user_obj_id = ObjectId(g.user_id)
    except (InvalidId, TypeError):
        return (
            jsonify(
                {
                    "error": "invalid_user",
                    "message": "Invalid user identifier.",
                }
            ),
            401,
        )

    db = get_db()
    sessions = db["chat_sessions"]
    history: list[dict[str, object]] = []
    session_obj_id = None

    if session_id:
        try:
            session_obj_id = ObjectId(session_id)
        except InvalidId:
            return (
                jsonify(
                    {
                        "error": "invalid_session_id",
                        "message": "session_id is invalid.",
                    }
                ),
                400,
            )

        try:
            session_doc = sessions.find_one(
                {"_id": session_obj_id, "user_id": user_obj_id}
            )
        except Exception as exc:
            current_app.logger.warning(
                "chat session lookup error: %s", exc
            )
            session_doc = None

        if session_doc is None:
            return (
                jsonify(
                    {
                        "error": "session_not_found",
                        "message": "Session not found.",
                    }
                ),
                404,
            )
        history = session_doc.get("messages") or []

    trimmed_history = _trim_messages(history, max_messages=20)

    # Optimize: Skip full context for lightweight requests or greetings
    if skip_context or len(message) < 15:
        context = {}
    else:
        try:
            # Only load essential log types to reduce token usage
            # Skip daily series (only keep aggregates)
            context = aggregation_service.build_context(
                g.user_id, log_types=["sleep", "hydration", "mood"], days=7
            )
        except Exception as exc:
            current_app.logger.warning(
                "chat context build error: %s", exc
            )
            context = {}

    messages = [_system_message(context)] + trimmed_history
    user_message = {
        "role": "user",
        "content": message,
        "timestamp": _now(),
    }
    messages.append(user_message)

    prompt = _format_prompt(messages)
    reply_text = None
    try:
        reply_text = call_gemini(prompt)
    except Exception as exc:
        current_app.logger.warning("chat gemini error: %s", exc)

    if not reply_text:
        reply_text = _FALLBACK_REPLY

    assistant_message = {
        "role": "assistant",
        "content": reply_text,
        "timestamp": _now(),
    }

    updated_messages = _trim_messages(
        trimmed_history + [user_message, assistant_message],
        max_messages=20,
    )
    now = _now()

    if session_obj_id is None:
        chat_doc = create_chat_session(
            user_obj_id,
            updated_messages,
            created_at=now,
        )
        chat_doc["updated_at"] = now
        try:
            result = sessions.insert_one(chat_doc)
            session_obj_id = result.inserted_id
        except Exception as exc:
            current_app.logger.warning(
                "chat session insert error: %s", exc
            )
            # Still return response even if save fails
            session_obj_id = None
    else:
        try:
            sessions.update_one(
                {"_id": session_obj_id, "user_id": user_obj_id},
                {"$set": {"messages": updated_messages, "updated_at": now}},
            )
        except Exception as exc:
            current_app.logger.warning(
                "chat session update error: %s", exc
            )

    return (
        jsonify(
            {
                "reply": reply_text,
                "session_id": str(session_obj_id) if session_obj_id else None,
            }
        ),
        200,
    )
