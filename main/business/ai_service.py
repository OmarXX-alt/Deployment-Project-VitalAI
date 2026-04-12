from __future__ import annotations

import json
import logging
from typing import Optional

from main.ai.gemini_client import call_gemini
from main.persistence.extensions import mongo
from main.persistence.models import UserPublic

logger = logging.getLogger(__name__)

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
        timeout_seconds (int) -> Optional[dict] {
            "type", "message", "tags"
        }.

    # TODO: [Logic-Issue-013]
    Prompt engineering contract:
        System persona: You are VitalAI, a concise wellness assistant.
        Instruction: Return a brief supportive reaction tailored to the log
        entry.
        JSON schema: {"type": str, "message": str, "tags": [str, str]}
    """
    _ = (mongo, UserPublic, gemini_api_key)
    
    try:
        entry_str = json.dumps(new_entry, default=str)
        prompt = (
            f"{SYSTEM_PERSONA}\n"
            f"A user logged a {log_type} entry: {entry_str}\n"
            f"Respond with ONLY valid JSON (no markdown, no extra text) with fields: "
            f"type (string: 'positive'|'neutral'|'alert'), "
            f"message (1-2 sentence encouragement), "
            f"tags (array of 1-2 relevant tags). Example: "
            f'{{"type":"positive","message":"Great job!","tags":["consistency"]}}'
        )
        response = call_gemini(prompt, timeout=timeout_seconds)
        if not response:
            return None
        
        data = json.loads(response)
        if not isinstance(data, dict):
            return None
        
        return {
            "type": str(data.get("type", "neutral")),
            "message": str(data.get("message", "")),
            "tags": data.get("tags", []) if isinstance(data.get("tags"), list) else [],
        }
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.debug(f"get_reaction JSON parse error: {e}")
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
        Even if no data logged, provide suggestions on what to track.
    Expected Input / Output:
        user_id (str), context (dict), gemini_api_key (str),
        timeout_seconds (int) -> Optional[dict] {
            "positives": [str, str],
            "concern": str,
            "suggestions": [str, str, str],
        }.

    # TODO: [Logic-Issue-014]
    Prompt engineering contract:
        System persona: You are VitalAI, a concise wellness assistant.
        Instruction: Summarize weekly positives, concerns, and suggestions.
        If data is minimal/empty, suggest what to track.
        JSON schema: {
            "positives": [str, str],
            "concern": str,
            "suggestions": [str, str, str],
        }
    """
    _ = (mongo, user_id, gemini_api_key)
    
    try:
        # Extract metrics from each health domain
        meals = context.get("meals", {})
        workouts = context.get("workouts", {})
        sleep = context.get("sleep", {})
        hydration = context.get("hydration", {})
        mood = context.get("mood", {})
        
        # Calculate hydration percentage of goal
        hydration_avg_ml = hydration.get("avg_ml", 0)
        hydration_target = hydration.get("target_ml", 2000)  # Default 2L
        hydration_pct = (
            round((hydration_avg_ml / hydration_target * 100) * 10) / 10
            if hydration_target > 0 else 0
        )
        
        # Check what data exists (even if sparse)
        has_meal_data = meals.get("meal_count", 0) > 0
        has_workout_data = workouts.get("sessions", 0) > 0
        has_sleep_data = sleep.get("entries", 0) > 0
        has_hydration_data = hydration_avg_ml > 0
        has_mood_data = mood.get("entries", 0) > 0
        
        data_logged_count = sum([
            has_meal_data, has_workout_data, has_sleep_data, 
            has_hydration_data, has_mood_data
        ])
        
        slim_context = {
            "period": "past 7 days",
            "meals_logged": meals.get("meal_count", 0),
            "meals_avg_kcal": round(meals.get("avg_calories", 0)) if has_meal_data else None,
            "workouts_count": workouts.get("sessions", 0),
            "workouts_total_min": workouts.get("total_minutes", 0) if has_workout_data else None,
            "sleep_entries": sleep.get("entries", 0),
            "sleep_avg_hours": round(sleep.get("avg_duration_hours", 0) * 10) / 10 if has_sleep_data else None,
            "sleep_avg_quality": round(sleep.get("avg_quality", 0) * 10) / 10 if has_sleep_data and sleep.get("avg_quality") else None,
            "hydration_avg_ml": round(hydration_avg_ml) if has_hydration_data else None,
            "hydration_pct_of_goal": hydration_pct if has_hydration_data else None,
            "mood_entries": mood.get("entries", 0),
            "mood_avg_score": round(mood.get("avg_score", 0) * 10) / 10 if has_mood_data else None,
            "note": "If no data logged for a category, suggest user start tracking it."
        }
        
        context_str = json.dumps(slim_context)
        
        # Adaptive prompt based on data logged
        if data_logged_count == 0:
            # If nothing logged, encourage tracking
            analysis_instruction = (
                "The user hasn't logged any health data yet. "
                "In positives, mention this is a great time to start. "
                "In concern, suggest starting with 1-2 categories. "
                "In suggestions, list the 3 easiest categories to log daily."
            )
        elif data_logged_count < 3:
            # If minimal data, encourage more tracking
            analysis_instruction = (
                "Limited data was logged this week. "
                "In positives, highlight what WAS tracked. "
                "In concern, mention missing health areas. "
                "In suggestions, recommend 2-3 new areas to track."
            )
        else:
            # If good data, provide full analysis
            analysis_instruction = (
                "Analyze the 7-day health data comprehensively. "
                "In positives, highlight 2 key wins or improvements. "
                "In concern, identify 1 priority area to improve. "
                "In suggestions, provide 3 actionable next steps."
            )
        
        prompt = (
            f"{SYSTEM_PERSONA}\n"
            f"{analysis_instruction}\n\n"
            f"7-day health data: {context_str}\n\n"
            f"Respond with ONLY valid JSON (no markdown, no extra text, no code blocks):\n"
            f'{{"positives": ["positive1", "positive2"], "concern": "main concern", "suggestions": ["action1", "action2", "action3"]}}'
        )
        
        response = call_gemini(prompt, timeout=timeout_seconds)
        if not response:
            logger.debug("get_wellness_insights: No response from Gemini")
            return None
        
        # Debug: log the raw response
        logger.debug(f"get_wellness_insights raw response: {response[:300]}")
        
        # Try to extract JSON if response has extra text
        response_clean = response
        try:
            # If response contains JSON, extract it
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                response_clean = response[start:end]
                logger.debug(f"Extracted JSON from response: {response_clean[:200]}")
        except Exception as e:
            logger.debug(f"Could not extract JSON, using full response: {e}")
        
        data = json.loads(response_clean)
        if not isinstance(data, dict):
            logger.debug(f"get_wellness_insights: Response is not dict: {type(data)}")
            return None
        
        positives = data.get("positives", [])
        suggestions = data.get("suggestions", [])
        concern = data.get("concern", "")
        
        # Validate structure - ensure we have arrays
        if not isinstance(positives, list):
            positives = [str(positives)] if positives else []
        if not isinstance(suggestions, list):
            suggestions = [str(suggestions)] if suggestions else []
        
        # Always return valid insight, never empty
        return {
            "positives": positives[:2] if positives else ["Start tracking your health data"],
            "concern": str(concern) if concern else "Limited health data this week",
            "suggestions": suggestions[:3] if suggestions else ["Log your meals", "Track workouts", "Monitor sleep"],
            "data_logged_categories": data_logged_count,
        }
    except json.JSONDecodeError as e:
        logger.debug(f"get_wellness_insights JSON parse error: {e}")
        # Fallback to sensible defaults
        return {
            "positives": ["You're building healthy habits"],
            "concern": "Need more data to provide detailed insights",
            "suggestions": ["Log your meals daily", "Track sleep patterns", "Record your mood"],
            "data_logged_categories": 0,
        }
    except (ValueError, TypeError) as e:
        logger.debug(f"get_wellness_insights error: {e}")
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
        goal_text (str), context (dict), gemini_api_key (str),
        timeout_seconds (int) -> Optional[dict] {
            "goal": str,
            "weeks": [{"week": int, "tasks": [str]}],
        }.

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
        message (str), history (list[dict]), context (dict),
        gemini_api_key (str), timeout_seconds (int),
        max_history_turns (int) -> Optional[str].

    # TODO: [Logic-Issue-028]
    Prompt engineering contract:
        System persona: You are VitalAI, a concise wellness assistant.
        Instruction: Respond empathetically in 2-4 sentences.
        JSON schema: {"response": str}
    """
    _ = (mongo, gemini_api_key)
    
    try:
        recent_history = history[-max_history_turns:] if history else []
        context_str = json.dumps(context, default=str)
        
        history_lines = []
        for turn in recent_history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role == "user":
                history_lines.append(f"User: {content}")
            elif role == "assistant":
                history_lines.append(f"Assistant: {content}")
        
        history_text = "\n".join(history_lines) if history_lines else "(no history)"
        
        prompt = (
            f"{SYSTEM_PERSONA}\n"
            f"Health context: {context_str}\n"
            f"Chat history:\n{history_text}\n"
            f"User: {message}\n\n"
            f"Reply empathetically in 2-4 sentences. Be supportive and actionable."
        )
        
        response = call_gemini(prompt, timeout=timeout_seconds)
        return response if response else None
    except (ValueError, TypeError) as e:
        logger.debug(f"get_chat_response error: {e}")
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
