"""
VitalAI — MongoDB seed script
Usage:  python seed.py
        MONGO_URI="mongodb+srv://..." python seed.py
"""

import os
from datetime import datetime, timezone
from flask import Flask
from pymongo import MongoClient
from dotenv import load_dotenv

try:
    import certifi
except Exception:
    certifi = None


# ── Reuse the project's DatabaseConnection exactly as written ─────────────────


class DatabaseConnection:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        mongo_uri = os.environ.get(
            "MONGO_URI", "mongodb://localhost:27017/vital_ai"
        )
        app.config.setdefault("MONGO_URI", mongo_uri)
        client_kwargs = {
            "serverSelectionTimeoutMS": 5000,
        }
        ca_file = os.environ.get("MONGO_TLS_CA_FILE")
        if ca_file:
            client_kwargs["tlsCAFile"] = ca_file
        elif certifi is not None:
            client_kwargs["tlsCAFile"] = certifi.where()

        self.client = MongoClient(app.config["MONGO_URI"], **client_kwargs)
        self.db = self.client.get_default_database(default="vital_ai")
        try:
            self.client.admin.command("ping")
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
        app.db = self.db


env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".env")
)
load_dotenv(dotenv_path=env_path)

db_conn = DatabaseConnection()


def get_db():
    return db_conn.db


# ── Helpers ───────────────────────────────────────────────────────────────────


def dt(iso: str) -> datetime:
    """Parse an ISO string into a UTC-aware datetime."""
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


# ── Seed data ─────────────────────────────────────────────────────────────────


def seed_injections():
    db = get_db()

    # ── Drop existing collections so the script is idempotent ────────────────
    collections = [
        "users",
        "workout_logs",
        "meal_logs",
        "sleep_logs",
        "hydration_logs",
        "mood_logs",
        "wellness_insights",
        "goal_plans",
        "chat_sessions",
    ]
    for col in collections:
        db[col].drop()
    print("Collections cleared.")

    # ── User ─────────────────────────────────────────────────────────────────
    user = {
        "email": "sara@example.com",
        "password_hash": "$2b$12$exampleHashedPasswordABC123xyz",  # bcrypt placeholder
        "display_name": "Sara",
        "daily_calorie_target": 2000,
        "hydration_goal_ml": 2500,
        "wellness_goal": "Improve sleep quality and build a consistent workout habit",
        "created_at": dt("2026-03-28T08:00:00"),
    }
    user_id = db.users.insert_one(user).inserted_id
    print(f"✓ users           → _id: {user_id}")

    # ── Workout logs ─────────────────────────────────────────────────────────
    workout_logs = [
        {
            "user_id": user_id,
            "exercise_type": "Running",
            "duration_min": 35,
            "sets": None,
            "reps": None,
            "intensity": "medium",
            "logged_at": dt("2026-03-29T07:15:00"),
            "ai_reaction": {
                "type": "recovery",
                "message": (
                    "Great 35-minute run! Your last two sessions were back-to-back — "
                    "consider a rest day tomorrow to let your muscles recover."
                ),
                "tags": ["recovery", "consistency"],
            },
        },
        {
            "user_id": user_id,
            "exercise_type": "Weight Training",
            "duration_min": 50,
            "sets": 4,
            "reps": 10,
            "intensity": "high",
            "logged_at": dt("2026-03-31T06:45:00"),
            "ai_reaction": {
                "type": "training_balance",
                "message": (
                    "Solid strength session. You've done 3 high-intensity workouts this week — "
                    "pair tonight's dinner with extra protein to support muscle repair."
                ),
                "tags": ["nutrition", "recovery", "strength"],
            },
        },
        {
            "user_id": user_id,
            "exercise_type": "Yoga",
            "duration_min": 25,
            "sets": None,
            "reps": None,
            "intensity": "low",
            "logged_at": dt("2026-04-02T08:00:00"),
            "ai_reaction": {
                "type": "balance",
                "message": (
                    "A light yoga session is perfect after yesterday's heavy lifting. "
                    "Your workout variety this week looks well-balanced."
                ),
                "tags": ["balance", "flexibility"],
            },
        },
    ]
    result = db.workout_logs.insert_many(workout_logs)
    print(f"✓ workout_logs     → {len(result.inserted_ids)} documents")

    # ── Meal logs ─────────────────────────────────────────────────────────────
    meal_logs = [
        {
            "user_id": user_id,
            "meal_name": "Oatmeal with banana and peanut butter",
            "calories": 480,
            "meal_type": "breakfast",
            "logged_at": dt("2026-04-02T08:30:00"),
            "ai_reaction": {
                "type": "calorie_pacing",
                "message": (
                    "Good start — 480 kcal leaves you 1520 kcal for the rest of the day. "
                    "The oats and banana are great pre-workout fuel."
                ),
                "tags": ["calorie_pacing", "pre_workout"],
            },
        },
        {
            "user_id": user_id,
            "meal_name": "Grilled chicken salad with quinoa",
            "calories": 620,
            "meal_type": "lunch",
            "logged_at": dt("2026-04-02T13:00:00"),
            "ai_reaction": {
                "type": "macro_balance",
                "message": (
                    "Excellent protein and fibre choice at lunch. "
                    "You're at 1100 kcal for the day — well on track for your 2000 kcal target."
                ),
                "tags": ["macro_balance", "protein"],
            },
        },
        {
            "user_id": user_id,
            "meal_name": "Protein bar",
            "calories": 210,
            "meal_type": "snack",
            "logged_at": dt("2026-04-02T16:30:00"),
            "ai_reaction": {
                "type": "pre_workout_nutrition",
                "message": (
                    "Good timing — a 210 kcal snack 90 minutes before your evening workout "
                    "should give you a steady energy boost without weighing you down."
                ),
                "tags": ["pre_workout", "timing"],
            },
        },
        {
            "user_id": user_id,
            "meal_name": "Salmon with sweet potato and broccoli",
            "calories": 680,
            "meal_type": "dinner",
            "logged_at": dt("2026-04-02T19:45:00"),
            "ai_reaction": {
                "type": "daily_summary",
                "message": (
                    "You finished the day at 1610 kcal — slightly under target, fine for a rest day. "
                    "The omega-3 from salmon will support muscle recovery overnight."
                ),
                "tags": ["recovery", "omega3", "daily_close"],
            },
        },
    ]
    result = db.meal_logs.insert_many(meal_logs)
    print(f"✓ meal_logs        → {len(result.inserted_ids)} documents")

    # ── Sleep logs ────────────────────────────────────────────────────────────
    sleep_logs = [
        {
            "user_id": user_id,
            "sleep_start": dt("2026-03-29T23:10:00"),
            "sleep_end": dt("2026-03-30T06:45:00"),
            "duration_hrs": round(7 + 35 / 60, 2),  # 7.58
            "quality": 4,
            "logged_at": dt("2026-03-30T07:00:00"),
            "ai_reaction": {
                "type": "recovery_analysis",
                "message": (
                    "7.5 hours with quality 4/5 — solid night. "
                    "Your average this week is 7.2 hrs; keep it above 7 to support workout recovery."
                ),
                "tags": ["recovery", "trend"],
            },
        },
        {
            "user_id": user_id,
            "sleep_start": dt("2026-03-31T00:30:00"),
            "sleep_end": dt("2026-03-31T06:15:00"),
            "duration_hrs": round(5 + 45 / 60, 2),  # 5.75
            "quality": 2,
            "logged_at": dt("2026-03-31T06:30:00"),
            "ai_reaction": {
                "type": "trend_alert",
                "message": (
                    "Only 5.75 hours and quality 2/5 tonight. After a high-intensity workout "
                    "yesterday, your body needs more rest — aim for 8 hours tonight."
                ),
                "tags": ["sleep_debt", "recovery_risk"],
            },
        },
        {
            "user_id": user_id,
            "sleep_start": dt("2026-04-01T22:45:00"),
            "sleep_end": dt("2026-04-02T07:00:00"),
            "duration_hrs": round(8 + 15 / 60, 2),  # 8.25
            "quality": 5,
            "logged_at": dt("2026-04-02T07:10:00"),
            "ai_reaction": {
                "type": "positive_trend",
                "message": (
                    "8.25 hours at quality 5/5 — your best night this week! "
                    "Going to bed before 23:00 clearly works well for you. Stick to it."
                ),
                "tags": ["positive", "consistency"],
            },
        },
    ]
    result = db.sleep_logs.insert_many(sleep_logs)
    print(f"✓ sleep_logs       → {len(result.inserted_ids)} documents")

    # ── Hydration logs ────────────────────────────────────────────────────────
    hydration_logs = [
        {
            "user_id": user_id,
            "amount_ml": 500,
            "daily_total_ml": 500,
            "logged_at": dt("2026-04-02T08:10:00"),
            "ai_reaction": {
                "type": "pacing",
                "message": (
                    "Good morning hydration start. You need 2000 ml more to hit your 2500 ml goal "
                    "today — spread it every 2 hours."
                ),
                "tags": ["pacing", "morning"],
            },
        },
        {
            "user_id": user_id,
            "amount_ml": 750,
            "daily_total_ml": 1250,
            "logged_at": dt("2026-04-02T12:30:00"),
            "ai_reaction": {
                "type": "on_track",
                "message": (
                    "Halfway through the day at 1250 ml — you're right on pace. "
                    "Remember to add an extra 300–400 ml after your evening workout."
                ),
                "tags": ["on_track", "workout_adjusted"],
            },
        },
        {
            "user_id": user_id,
            "amount_ml": 400,
            "daily_total_ml": 1650,
            "logged_at": dt("2026-04-02T16:00:00"),
            "ai_reaction": {
                "type": "workout_adjusted",
                "message": (
                    "850 ml left to reach your goal. With a workout coming up, aim to drink "
                    "250 ml before, 150 ml during, and 400 ml after exercise."
                ),
                "tags": ["pre_workout", "adjustment"],
            },
        },
        {
            "user_id": user_id,
            "amount_ml": 600,
            "daily_total_ml": 2250,
            "logged_at": dt("2026-04-02T20:30:00"),
            "ai_reaction": {
                "type": "goal_near",
                "message": (
                    "Only 250 ml away from today's target! A glass before bed will get you there. "
                    "You've been consistent with hydration all week."
                ),
                "tags": ["goal_near", "consistency"],
            },
        },
    ]
    result = db.hydration_logs.insert_many(hydration_logs)
    print(f"✓ hydration_logs   → {len(result.inserted_ids)} documents")

    # ── Mood logs ─────────────────────────────────────────────────────────────
    mood_logs = [
        {
            "user_id": user_id,
            "mood_rating": 3,
            "note": "Felt groggy and slow to start",
            "logged_at": dt("2026-03-31T09:00:00"),
            "ai_reaction": {
                "type": "correlation",
                "message": (
                    "Your mood of 3/5 lines up with last night's short sleep (5.75 hrs, quality 2/5). "
                    "Prioritising rest tonight should help lift your energy tomorrow."
                ),
                "tags": ["sleep_correlation", "energy"],
            },
        },
        {
            "user_id": user_id,
            "mood_rating": 4,
            "note": "Felt good after the yoga session",
            "logged_at": dt("2026-04-02T09:30:00"),
            "ai_reaction": {
                "type": "positive_pattern",
                "message": (
                    "Mood 4/5 after a good night's sleep and morning yoga — this pattern shows up "
                    "consistently in your logs. Keep the morning movement habit going."
                ),
                "tags": ["exercise_correlation", "positive"],
            },
        },
        {
            "user_id": user_id,
            "mood_rating": 5,
            "note": "Really energised and focused today",
            "logged_at": dt("2026-04-03T10:00:00"),
            "ai_reaction": {
                "type": "peak_pattern",
                "message": (
                    "Your best mood rating this week! It follows your highest sleep quality night "
                    "(8.25 hrs, 5/5). Sleep quality is clearly your biggest mood lever."
                ),
                "tags": ["peak", "sleep_correlation", "insight"],
            },
        },
    ]
    result = db.mood_logs.insert_many(mood_logs)
    print(f"✓ mood_logs        → {len(result.inserted_ids)} documents")

    # ── Wellness insight (on-demand weekly AI analysis) ───────────────────────
    wellness_insight = {
        "user_id": user_id,
        "positives": [
            "Your sleep duration improved steadily across the week, finishing at 8.25 hours on Thursday.",
            "Workout variety was excellent — you mixed cardio, strength, and flexibility training.",
        ],
        "concern": (
            "Tuesday's sleep was only 5.75 hours following a high-intensity session, "
            "which correlated with your lowest mood rating of the week."
        ),
        "suggestions": [
            "Schedule rest or low-intensity days the night after every high-intensity workout.",
            "Set a consistent bedtime alarm for 22:30 to protect your sleep window.",
            "Log your evening meal at least 2 hours before bed to improve sleep quality scores.",
        ],
        "generated_at": dt("2026-04-03T12:00:00"),
    }
    insight_id = db.wellness_insights.insert_one(wellness_insight).inserted_id
    print(f"✓ wellness_insights → _id: {insight_id}")

    # ── Goal plan (extension — AI Goal Coach) ─────────────────────────────────
    goal_plan = {
        "user_id": user_id,
        "goal": "Run 5 km without stopping within 4 weeks",
        "weekly_tasks": [
            {
                "week": 1,
                "tasks": [
                    "Run/walk intervals: 1 min run, 2 min walk × 8 reps (3×)",
                    "Log every session immediately after finishing",
                    "Sleep at least 7.5 hours on training nights",
                ],
            },
            {
                "week": 2,
                "tasks": [
                    "Run/walk intervals: 2 min run, 1 min walk × 8 reps (3×)",
                    "Add one 20-minute yoga or stretch session mid-week",
                    "Hit daily hydration goal on all training days",
                ],
            },
            {
                "week": 3,
                "tasks": [
                    "Continuous run: 15 minutes without stopping (2×)",
                    "One long easy run: 25–30 minutes at low intensity",
                    "Log mood before and after each run to track correlation",
                ],
            },
            {
                "week": 4,
                "tasks": [
                    "Continuous run: 25 minutes (mid-week)",
                    "Rest day before the final attempt",
                    "5 km time trial — run at a comfortable, steady pace",
                ],
            },
        ],
        "created_at": dt("2026-04-03T13:00:00"),
    }
    plan_id = db.goal_plans.insert_one(goal_plan).inserted_id
    print(f"✓ goal_plans       → _id: {plan_id}")

    # ── Chat session (extension — AI Chat Assistant) ───────────────────────────
    chat_session = {
        "user_id": user_id,
        "messages": [
            {
                "role": "user",
                "content": "Why do I feel so tired even after sleeping 7 hours?",
                "timestamp": dt("2026-04-03T14:00:00"),
            },
            {
                "role": "assistant",
                "content": (
                    "Looking at your logs, last Tuesday you slept only 5.75 hours at quality 2/5 "
                    "after a high-intensity workout. That sleep debt can linger 2–3 days. "
                    "Your 8.25-hour night on Wednesday was a great recovery — if tiredness "
                    "persists today, a 20-minute nap before 15:00 can help without affecting tonight's sleep."
                ),
                "timestamp": dt("2026-04-03T14:00:05"),
            },
            {
                "role": "user",
                "content": "What should I eat before my run tomorrow morning?",
                "timestamp": dt("2026-04-03T14:02:00"),
            },
            {
                "role": "assistant",
                "content": (
                    "For a morning run, eat something light and carb-forward 30–60 minutes before: "
                    "a banana, a small bowl of oatmeal, or a slice of toast with honey. "
                    "Based on your meal logs, your oatmeal-and-banana breakfast on Wednesday gave "
                    "you a mood rating of 4/5 and fuelled a good yoga session — that's a safe bet."
                ),
                "timestamp": dt("2026-04-03T14:02:08"),
            },
        ],
        "created_at": dt("2026-04-03T14:00:00"),
    }
    session_id = db.chat_sessions.insert_one(chat_session).inserted_id
    print(f"✓ chat_sessions    → _id: {session_id}")

    print("\nSeed complete. Collections summary:")
    for col in collections:
        print(f"  {col:<22} {db[col].count_documents({})} document(s)")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = Flask(__name__)
    db_conn.init_app(app)

    with app.app_context():
        seed_injections()
