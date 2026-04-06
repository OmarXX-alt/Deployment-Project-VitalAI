import json
import logging

import requests
from flask import Blueprint, current_app, jsonify

from main.application.routes._auth_utils import login_required
from main.business.utils.aggregation import format_context_for_prompt, get_user_context

logger = logging.getLogger(__name__)

insights_bp = Blueprint("insights", __name__)

_GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

_SYSTEM_PROMPT = """
You are VitalAI, a supportive and knowledgeable health and wellness coach.
Based on the user's 7-day activity summary below, provide a brief, encouraging
weekly wellness insight.

Your response must be a valid JSON object with exactly these keys:
  - "positives": a list of 1-3 short strings highlighting what the user did well
  - "concern":   a single string identifying the most important area to improve
  - "suggestions": a list of 1-3 short, actionable strings the user can try next week

Keep the tone warm, concise, and motivating. Return ONLY the JSON object — no
markdown, no preamble, no explanation.
""".strip()


@insights_bp.get("/api/insights/weekly")
@login_required
def get_weekly_insight(current_user_id: str):
    """
    Generate a personalised weekly wellness insight for the authenticated user.

    Builds a 7-day activity summary from the user's logs across all categories,
    then calls the Gemini API to produce structured feedback.

    Returns 200 with:
        {
            "insight": "<formatted insight string>",
            "detail": {
                "positives":    [...],
                "concern":      "...",
                "suggestions":  [...]
            }
        }
    Returns 500 if the AI call fails or the response cannot be parsed.
    """
    # ── 1. Build the user context from the last 7 days ──────────────────────
    try:
        context = get_user_context(current_user_id, log_type="all")
        context_text = format_context_for_prompt(context)
    except Exception:
        logger.exception("get_weekly_insight: failed to build context user=%s", current_user_id)
        return jsonify({"message": "Could not retrieve your activity data."}), 500

    if not context_text.strip():
        return jsonify({
            "insight": "No data yet — start logging your meals, workouts, sleep, "
                       "hydration, and mood to get your first weekly insight! 🌱",
            "detail": {}
        }), 200

    # ── 2. Call Gemini ───────────────────────────────────────────────────────
    api_key = current_app.config.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.error("get_weekly_insight: GEMINI_API_KEY not configured")
        return jsonify({"message": "AI service is not configured."}), 500

    prompt = f"{_SYSTEM_PROMPT}\n\nUser's 7-day summary:\n{context_text}"

    try:
        response = requests.post(
            f"{_GEMINI_API_URL}?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512},
            },
            timeout=15,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("get_weekly_insight: Gemini request timed out user=%s", current_user_id)
        return jsonify({"message": "AI service timed out. Please try again."}), 500
    except requests.exceptions.RequestException:
        logger.exception("get_weekly_insight: Gemini request failed user=%s", current_user_id)
        return jsonify({"message": "AI service unavailable. Please try again later."}), 500

    # ── 3. Parse the Gemini response ─────────────────────────────────────────
    try:
        raw_text = (
            response.json()["candidates"][0]["content"]["parts"][0]["text"]
        )
        detail = json.loads(raw_text)
    except (KeyError, IndexError, json.JSONDecodeError):
        logger.exception("get_weekly_insight: failed to parse Gemini response user=%s", current_user_id)
        return jsonify({"message": "Could not parse AI response. Please try again."}), 500

    # ── 4. Format a human-readable summary string ────────────────────────────
    positives = detail.get("positives", [])
    concern = detail.get("concern", "")
    suggestions = detail.get("suggestions", [])

    lines = []
    if positives:
        lines.append("✅ " + " · ".join(positives))
    if concern:
        lines.append(f"⚠️ {concern}")
    if suggestions:
        lines.append("💡 " + " · ".join(suggestions))

    insight_str = "\n".join(lines) if lines else "Keep logging to unlock your insight!"

    return jsonify({"insight": insight_str, "detail": detail}), 200
