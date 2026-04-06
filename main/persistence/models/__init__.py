"""MongoDB document types for VitalAI models."""

from __future__ import annotations

from .hydration_log import HydrationLogDocument
from .meal_log import MealLogDocument, MealType
from .mood_log import MoodLogDocument
from .sleep_log import SleepLogDocument
from .user import UserDocument, UserPublic
from .workout_log import IntensityLevel, WorkoutLogDocument

__all__ = [
	"UserDocument",
	"UserPublic",
	"WorkoutLogDocument",
	"IntensityLevel",
	"MealLogDocument",
	"MealType",
	"SleepLogDocument",
	"HydrationLogDocument",
	"MoodLogDocument",
]
