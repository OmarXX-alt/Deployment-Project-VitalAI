from __future__ import annotations

from datetime import datetime
from typing import TypedDict


class HydrationLogDocument(TypedDict):
    _id: str
    user_id: str
    amount_ml: int
    logged_at: datetime
    created_at: datetime
