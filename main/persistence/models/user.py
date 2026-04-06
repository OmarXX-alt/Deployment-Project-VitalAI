from __future__ import annotations

from datetime import datetime
from typing import Optional, TypedDict


class UserDocument(TypedDict):
    _id: str
    display_name: str
    email: str
    password_hash: str
    daily_calorie_target: Optional[int]
    hydration_goal: Optional[int]
    wellness_goal: Optional[str]
    last_briefing_date: Optional[str]
    created_at: datetime


class UserPublic(TypedDict):
    user_id: str
    display_name: str
    email: str
    daily_calorie_target: Optional[int]
    hydration_goal: Optional[int]
    wellness_goal: Optional[str]
