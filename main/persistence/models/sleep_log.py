from __future__ import annotations

from datetime import datetime
from typing import TypedDict


class SleepLogDocument(TypedDict):
    _id: str
    user_id: str
    sleep_start: datetime
    sleep_end: datetime
    duration_minutes: int
    quality_score: int
    logged_at: datetime
    created_at: datetime
