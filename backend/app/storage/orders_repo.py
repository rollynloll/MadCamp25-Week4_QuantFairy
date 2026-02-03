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
