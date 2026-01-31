from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


class MyStrategiesRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def list(
        self,
        user_id: str,
        filters: Dict[str, Any],
        sort: str,
        order: str,
        limit: int,
        cursor_value: Optional[str],
    ) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return []
        query = (
            self.supabase.table("my_strategies")
            .select("*")
            .eq("user_id", user_id)
        )

        if filters.get("q"):
            q = filters["q"]
            query = query.ilike("name", f"%{q}%")
        if filters.get("source_public_strategy_id"):
            query = query.eq("source_public_strategy_id", filters["source_public_strategy_id"])

        if cursor_value:
            op = "lt" if order == "desc" else "gt"
            query = query.filter(sort, op, cursor_value)

        query = query.order(sort, desc=(order == "desc")).limit(limit)
        result = query.execute()
        data = getattr(result, "data", None)
        return data or []

    def get(self, user_id: str, my_strategy_id: str) -> Optional[Dict[str, Any]]:
        if self.supabase is None:
            return None
        try:
            result = (
                self.supabase.table("my_strategies")
                .select("*")
                .eq("user_id", user_id)
                .eq("my_strategy_id", my_strategy_id)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None

    def create(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "user_id": user_id,
            **payload,
            "created_at": now_kst().isoformat(),
            "updated_at": now_kst().isoformat(),
        }
        if self.supabase is None:
            return row
        self.supabase.table("my_strategies").insert(row).execute()
        return row

    def update(self, user_id: str, my_strategy_id: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        payload["updated_at"] = now_kst().isoformat()
        if self.supabase is None:
            return None
        result = (
            self.supabase.table("my_strategies")
            .update(payload)
            .eq("user_id", user_id)
            .eq("my_strategy_id", my_strategy_id)
            .execute()
        )
        data = getattr(result, "data", None)
        if data:
            return data[0]
        return None

    def delete(self, user_id: str, my_strategy_id: str) -> None:
        if self.supabase is None:
            return
        self.supabase.table("my_strategies").delete().eq("user_id", user_id).eq(
            "my_strategy_id", my_strategy_id
        ).execute()
