from __future__ import annotations

from typing import Any, Dict

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


class BotRunsRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def get_latest(self, user_id: str) -> Dict[str, Any] | None:
        if self.supabase is None:
            return None
        try:
            result = (
                self.supabase.table("bot_runs")
                .select("*")
                .eq("user_id", user_id)
                .order("started_at", desc=True)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None

    def create_run(self, user_id: str, run_id: str) -> Dict[str, Any]:
        row = {
            "run_id": run_id,
            "user_id": user_id,
            "started_at": now_kst().isoformat(),
            "result": "partial",
            "orders_created": 0,
            "orders_failed": 0,
        }
        if self.supabase is None:
            return row
        try:
            self.supabase.table("bot_runs").insert(row).execute()
        except Exception:
            return row
        return row

    def finalize_run(self, run_id: str, result: str = "success") -> None:
        if self.supabase is None:
            return
        try:
            self.supabase.table("bot_runs").update(
                {
                    "ended_at": now_kst().isoformat(),
                    "result": result,
                }
            ).eq("run_id", run_id).execute()
        except Exception:
            return
