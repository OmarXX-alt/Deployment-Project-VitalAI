"""
ai.py
Gemini API client + all VitalAI AI functions.
Handles: auth, HTTP, response parsing, and all prompt logic.

MongoDB-ready: the weekly_insight function accepts plain computed values.
When MongoDB is wired up, app.py queries the DB, computes the summaries,
and passes them in — this file does not need to change.
"""

import os, re
import requests

MODEL        = "gemini-2.5-flash-lite"
API_ENDPOINT = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{MODEL}:generateContent"


# ── Low-level client ──────────────────────────────────────────────────────────

def _call(prompt: str) -> str:
    """Send a prompt to Gemini and return the raw text response."""
    api_key = os.environ["GEMINI_KEY"]
    url     = f"{API_ENDPOINT}?key={api_key}"

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ]
    }

    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def _clean_json(text: str) -> str:
    """Strip markdown fences from a JSON string returned by the model."""
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


# ── Meal ──────────────────────────────────────────────────────────────────────

def analyse_meal(food: str, calories: int, protein: int) -> str:
    """Return a short personalised nutrition tip for a logged meal."""
    prompt = f"""A user just logged a meal:
Food: {food}
Calories: {calories} kcal
Protein: {protein}g

Give a 2-3 sentence personalised nutrition insight about this meal.
Focus on nutritional value, balance, and one practical improvement tip."""
    return _call(prompt).strip()


# ── Workout ───────────────────────────────────────────────────────────────────

def analyse_workout(exercise: str, duration: int, intensity: str) -> str:
    """Return a short recovery and benefit tip for a logged workout."""
    prompt = f"""A user just logged a workout:
Exercise: {exercise}
Duration: {duration} minutes
Intensity: {intensity}

Give a 2-3 sentence personalised recovery and performance tip.
Mention the key benefit of this exercise and one recovery suggestion."""
    return _call(prompt).strip()


# ── Sleep ─────────────────────────────────────────────────────────────────────

def analyse_sleep(hours: float, quality: str) -> str:
    """Return a short sleep health insight for a logged sleep entry."""
    prompt = f"""A user just logged their sleep:
Hours slept: {hours}
Quality: {quality}

Give a 2-3 sentence personalised sleep insight.
Comment on whether the duration is healthy and give one actionable tip to improve sleep quality."""
    return _call(prompt).strip()


# ── Hydration ─────────────────────────────────────────────────────────────────

def analyse_hydration(ml: int) -> str:
    """Return a short hydration tip for a logged water intake entry."""
    prompt = f"""A user just logged {ml} ml of water.

Give a 2-3 sentence personalised hydration insight.
Mention whether this is a good amount relative to daily needs and give one tip to stay on track."""
    return _call(prompt).strip()


# ── Mood ──────────────────────────────────────────────────────────────────────

def analyse_mood(rating: int, notes: str) -> str:
    """Return a short wellness tip for a logged mood check-in."""
    prompt = f"""A user just logged their mood:
Mood rating: {rating}/10
Notes: "{notes}"

Give a 2-3 sentence empathetic and personalised mental wellness insight.
Acknowledge their mood and suggest one practical wellbeing activity."""
    return _call(prompt).strip()


# ── Weekly insight ────────────────────────────────────────────────────────────

def weekly_insight(
    total_meals: int,
    total_workouts: int,
    avg_sleep_hours: float,
    total_water_ml: int,
    avg_mood: float,
) -> str:
    """Return a personalised weekly wellness summary.

    Accepts plain computed values from app.py.
    When MongoDB is added, app.py queries the DB, computes these values,
    and passes them in — this function does not need to change.
    """
    prompt = f"""A user's weekly wellness summary:
- Meals logged: {total_meals}
- Workouts logged: {total_workouts}
- Average sleep: {avg_sleep_hours} hours/night
- Total water intake: {total_water_ml} ml
- Average mood: {avg_mood}/10

Write a 4-5 sentence personalised weekly wellness report.
Highlight their strongest habit, identify their weakest area, and give two concrete goals for next week."""
    return _call(prompt).strip()