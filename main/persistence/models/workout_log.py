from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, TypedDict

IntensityLevel = Literal["low", "moderate", "high"]


class WorkoutLogDocument(TypedDict):
    _id: str
    user_id: str
    exercise_type: str
    duration_minutes: int
    sets: Optional[int]
    reps: Optional[int]
    intensity: IntensityLevel
    logged_at: datetime
    created_at: datetime
