"""
test-ai.py
Run this locally to verify all ai.py functions work correctly.

Usage:
    $env:GEMINI_KEY="your_key_here"  # PowerShell
    python test-ai.py
"""

import os, sys

# ── Check env var first ───────────────────────────────────────────────────────
if not os.environ.get("GEMINI_KEY"):
    print("❌  GEMINI_KEY not set. Run: export GEMINI_KEY=your_key_here")
    sys.exit(1)

import ai  # ai.py must be in the same folder

PASS = "✅"
FAIL = "❌"

def run(label, fn, *args, **kwargs):
    print(f"\n{'─'*50}")
    print(f"Testing: {label}")
    try:
        result = fn(*args, **kwargs)
        assert isinstance(result, str) and len(result) > 10, "Response too short or wrong type"
        print(f"{PASS}  {result[:120]}{'...' if len(result) > 120 else ''}")
    except Exception as e:
        print(f"{FAIL}  {e}")

# ── Run each function ─────────────────────────────────────────────────────────
run("analyse_meal",
    ai.analyse_meal, "grilled chicken and rice", 520, 45)

run("analyse_workout",
    ai.analyse_workout, "Running", 30, "high")

run("analyse_sleep",
    ai.analyse_sleep, 6.5, "fair")

run("analyse_hydration",
    ai.analyse_hydration, 750)

run("analyse_mood",
    ai.analyse_mood, 4, "Feeling a bit stressed from work")

run("weekly_insight",
    ai.weekly_insight,
    total_meals=5,
    total_workouts=3,
    avg_sleep_hours=6.8,
    total_water_ml=4200,
    avg_mood=6.5)

print(f"\n{'─'*50}")
print("Done.")