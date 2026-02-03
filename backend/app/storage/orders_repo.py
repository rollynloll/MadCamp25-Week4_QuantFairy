from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import Settings
from app.storage.supabase_client import get_supabase_client


class OrdersRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def upsert_many(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rows:
            return []
        if self.supabase is None:
            return rows
        try:
            self.supabase.table("orders").upsert(rows, on_conflict="order_id").execute()
        except Exception:
            return rows
        return rows

    def list_recent(
        self,
        user_id: str,
        environment: str,
        *,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return []
        try:
            result = (
                self.supabase.table("orders")
                .select("*")
                .eq("user_id", user_id)
                .eq("environment", environment)
                .order("submitted_at", desc=True)
                .limit(limit)
                .execute()
            )
            data = getattr(result, "data", None)
            if data is not None:
                return data
        except Exception:
            return []
        return []
