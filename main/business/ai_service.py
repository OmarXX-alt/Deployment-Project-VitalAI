from __future__ import annotations

from typing import Optional

from main.persistence.extensions import mongo
from main.persistence.models import UserPublic


SYSTEM_PERSONA = "You are VitalAI, a concise wellness assistant."


def get_reaction(
    log_type: str,
    context: dict,
    new_entry: dict,
    gemini_api_key: str = "",
    timeout_seconds: int = 3,
) -> Optional[dict]:
    """Generate a short supportive reaction for a new log entry.

    Purpose:
        Produce a lightweight reaction for a single log entry.
    Expected Input / Output:
        log_type (str), context (dict), new_entry (dict), gemini_api_key (str),
        timeout_seconds (int) → Optional[dict] {"type", "message", "tags"}.

    # TODO: [Logic-Issue-013]
    Prompt engineering contract:
        System persona: You are VitalAI, a concise wellness assistant.
        Instruction: Return a brief supportive reaction tailored to the log entry.
        JSON schema: {"type": str, "message": str, "tags": [str, str]}
    """
    _ = (mongo, UserPublic)
    return None


def get_wellness_insights(
    user_id: str,
    context: dict,
    gemini_api_key: str = "",
    timeout_seconds: int = 10,
) -> Optional[dict]:
    """Generate weekly wellness insights for the user.

    Purpose:
        Summarize positives, concerns, and suggestions for the past week.
    Expected Input / Output:
        user_id (str), context (dict), gemini_api_key (str), timeout_seconds (int)
        → Optional[dict] {"positives": [str,str], "concern": str,
        "suggestions": [str,str,str]}.

    # TODO: [Logic-Issue-014]
    Prompt engineering contract:
        System persona: You are VitalAI, a concise wellness assistant.
        Instruction: Summarize weekly positives, concerns, and suggestions.
        JSON schema: {"positives": [str, str], "concern": str,
                      "suggestions": [str, str, str]}
    """
    _ = mongo
    return None


def get_goal_coach_plan(
    goal_text: str,
    context: dict,
    gemini_api_key: str = "",
    timeout_seconds: int = 15,
) -> Optional[dict]:
    """Generate a multi-week goal plan.

    Purpose:
        Provide a structured, week-by-week plan for a user goal.
    Expected Input / Output:
        goal_text (str), context (dict), gemini_api_key (str), timeout_seconds (int)
        → Optional[dict] {"goal": str, "weeks": [{"week": int, "tasks": [str]}]}.

    # TODO: [Logic-Issue-027]
    Prompt engineering contract:
        System persona: You are VitalAI, a concise wellness assistant.
        Instruction: Create a weekly plan with 2-5 tasks per week.
        JSON schema: {"goal": str, "weeks": [{"week": int, "tasks": [str]}]}
    """
    _ = mongo
    return None


def get_chat_response(
    message: str,
    history: list[dict],
    context: dict,
    gemini_api_key: str = "",
    timeout_seconds: int = 10,
    max_history_turns: int = 10,
) -> Optional[str]:
    """Generate a chat reply for the conversation.

    Purpose:
        Respond to a chat message using recent context and message history.
    Expected Input / Output:
        message (str), history (list[dict]), context (dict), gemini_api_key (str),
        timeout_seconds (int), max_history_turns (int) → Optional[str].

    # TODO: [Logic-Issue-028]
    Prompt engineering contract:
        System persona: You are VitalAI, a concise wellness assistant.
        Instruction: Respond empathetically in 2-4 sentences.
        JSON schema: {"response": str}
    """
    _ = mongo
    return None


def get_morning_briefing(
    user_id: str,
    yesterday_context: dict,
    gemini_api_key: str = "",
    timeout_seconds: int = 5,
) -> Optional[dict]:
    """Generate a morning briefing summary for the user.

    Purpose:
        Provide a short briefing with focus areas and encouragement.
    Expected Input / Output:
        user_id (str), yesterday_context (dict), gemini_api_key (str),
        timeout_seconds (int) → Optional[dict] {"date", "yesterday_summary",
        "focus_area", "focus_message"}.

    # TODO: [Logic-Issue-016]
    Prompt engineering contract:
        System persona: You are VitalAI, a concise wellness assistant.
        Instruction: Return a short briefing with a single focus area.
        JSON schema: {"date": str, "yesterday_summary": str,
                      "focus_area": str, "focus_message": str}
    """
    _ = mongo
    return None
