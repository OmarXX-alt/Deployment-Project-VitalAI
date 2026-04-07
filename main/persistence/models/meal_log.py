from __future__ import annotations

from datetime import datetime
from typing import Literal, TypedDict

MealType = Literal["breakfast", "lunch", "dinner", "snack"]


class MealLogDocument(TypedDict):
    _id: str
    user_id: str
    meal_name: str
    calories: int
    meal_type: MealType
    logged_at: datetime
    created_at: datetime
