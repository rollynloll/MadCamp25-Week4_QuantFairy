from __future__ import annotations

from app.core.config import Settings
from app.storage.supabase_client import get_supabase_client


class PositionsRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def count(self, user_id: str, environment: str) -> int:
        if self.supabase is None:
            return 0
        try:
            result = (
                self.supabase.table("positions")
                .select("position_id", count="exact")
                .eq("user_id", user_id)
                .eq("environment", environment)
                .execute()
            )
            count = getattr(result, "count", None)
            if count is not None:
                return int(count)
            data = getattr(result, "data", None)
            if data is not None:
                return len(data)
        except Exception:
            return 0
        return 0
