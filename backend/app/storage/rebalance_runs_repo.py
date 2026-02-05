from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


class RebalanceRunsRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            **payload,
            "created_at": payload.get("created_at") or now_kst().isoformat(),
            "updated_at": payload.get("updated_at") or now_kst().isoformat(),
        }
        if self.supabase is None:
            return row
        try:
            result = self.supabase.table("rebalance_runs").insert(row).execute()
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return row
        return row

    def update(self, run_id: str, payload: Dict[str, Any]) -> Dict[str, Any] | None:
        if self.supabase is None:
            return None
        update_payload = {**payload, "updated_at": now_kst().isoformat()}
        try:
            result = (
                self.supabase.table("rebalance_runs")
                .update(update_payload)
                .eq("run_id", run_id)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None

    def list_recent(
        self,
        user_id: str,
        environment: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return []
        try:
            result = (
                self.supabase.table("rebalance_runs")
                .select("*")
                .eq("user_id", user_id)
                .eq("environment", environment)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            data = getattr(result, "data", None)
            if data is not None:
                return data
        except Exception:
            return []
        return []
