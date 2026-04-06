from __future__ import annotations

from datetime import datetime
from typing import Optional, TypedDict


class MoodLogDocument(TypedDict):
    _id: str
    user_id: str
    date: str
    mood_score: int
    note: Optional[str]
    logged_at: datetime
    created_at: datetime
