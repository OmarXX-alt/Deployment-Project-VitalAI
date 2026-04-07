"""Gemini API wrapper and prompt builders."""

import logging
import os

import requests

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = (
    "You are a personal wellness coach. Reply in 2-3 sentences. "
    "Be encouraging, specific, and actionable. Do not use lists or markdown."
)


def call_gemini(prompt: str, timeout: int = 60) -> str | None:
    """Send a single prompt to Gemini 2.5 Flash."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY is missing.")
        return None
    if not prompt:
        logger.warning("Gemini prompt is empty.")
        return None

    try:
        try:
            import google.generativeai as genai
        except Exception:
            genai = None

        if genai is not None:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(
                prompt,
                request_options={"timeout": timeout},
            )
            text = getattr(response, "text", None)
            if text:
                return text.strip() or None
            return None

        url = (
            "https://generativelanguage.googleapis.com/"
            "v1beta/models/gemini-2.5-flash:generateContent"
        )
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(
            f"{url}?key={api_key}",
            json=payload,
            timeout=timeout,
        )
        if not response.ok:
            snippet = response.text[:200] if response.text else ""
            logger.warning(
                "Gemini request failed with status %s: %s",
                response.status_code,
                snippet,
            )
            return None
        try:
            data = response.json()
        except Exception as exc:
            snippet = response.text[:200] if response.text else ""
            logger.warning("Gemini response JSON error: %s", exc)
            logger.warning("Gemini response snippet: %s", snippet)
            return None
        candidates = data.get("candidates") or []
        if not candidates:
            return None
        content = candidates[0].get("content") or {}
        parts = content.get("parts") or []
        if not parts:
            return None
        text = parts[0].get("text")
        if not text:
            return None
        return str(text).strip() or None
    except Exception as exc:
        logger.warning("Gemini call failed: %s", exc)
        return None


def build_meal_prompt(new_entry: dict, context: dict) -> str:
    """Build a Gemini prompt for meal reactions."""
    return (
        f"{SYSTEM_INSTRUCTION}\n"
        "Return only the reaction message, no preamble, no labels.\n\n"
        f"New meal entry: {new_entry}\n"
        f"Context (7 days): {context}\n"
    )


def build_workout_prompt(new_entry: dict, context: dict) -> str:
    """Build a Gemini prompt for workout reactions."""
    return (
        f"{SYSTEM_INSTRUCTION}\n"
        "Return only the reaction message, no preamble, no labels.\n\n"
        "Focus on recovery time based on intensity and duration. "
        "Mention training balance from the last 7 days and give one "
        "concrete suggestion for the next session.\n\n"
        f"New workout entry: {new_entry}\n"
        f"Context (7 days): {context}\n"
    )


def build_sleep_prompt(new_entry: dict, context: dict) -> str:
    """Build a Gemini prompt for sleep reactions."""
    return (
        f"{SYSTEM_INSTRUCTION}\n"
        "Return only the reaction message, no preamble, no labels.\n\n"
        "Compare tonight's duration and quality to the 7-day average. "
        "Give one recovery or habit suggestion tied to the numbers.\n\n"
        f"New sleep entry: {new_entry}\n"
        f"Context (7 days): {context}\n"
    )


def build_hydration_prompt(new_entry: dict, context: dict) -> str:
    """Build a Gemini prompt for hydration reactions."""
    return (
        f"{SYSTEM_INSTRUCTION}\n"
        "Return only the reaction message, no preamble, no labels.\n\n"
        "Highlight progress toward the daily target from the context. "
        "Adjust advice if a workout was logged today.\n\n"
        f"New hydration entry: {new_entry}\n"
        f"Context (7 days): {context}\n"
    )


def build_mood_prompt(new_entry: dict, context: dict) -> str:
    """Build a Gemini prompt for mood reactions."""
    return (
        f"{SYSTEM_INSTRUCTION}\n"
        "Return only the reaction message, no preamble, no labels.\n\n"
        "Connect today's mood score to 7-day sleep and workout patterns. "
        "Give one actionable suggestion tied to the score.\n\n"
        f"New mood entry: {new_entry}\n"
        f"Context (7 days): {context}\n"
    )
