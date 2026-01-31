from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


class BacktestRunsRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def create(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        row = {
            **payload,
            "created_at": now_kst().isoformat(),
            "updated_at": now_kst().isoformat(),
        }
        if self.supabase is None:
            return row
        result = self.supabase.table("backtest_runs").insert(row).execute()
        data = getattr(result, "data", None)
        if data:
            return data[0]
        return row

    def get(self, user_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        if self.supabase is None:
            return None
        result = (
            self.supabase.table("backtest_runs")
            .select("*")
            .eq("user_id", user_id)
            .eq("run_id", run_id)
            .limit(1)
            .execute()
        )
        data = getattr(result, "data", None)
        if data:
            return data[0]
        return None
