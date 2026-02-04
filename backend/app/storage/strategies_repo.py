from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


_memory_strategies: Dict[str, Dict[str, Dict[str, Any]]] = {}


class StrategiesRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.supabase = get_supabase_client(settings)

    def ensure_seed(self, user_id: str) -> None:
        return

    def list(self, user_id: str) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return []
        try:
            result = (
                self.supabase.table("user_strategies")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            data = getattr(result, "data", None)
            if data is not None:
                return data
        except Exception:
            return []
        return []

    def get(self, user_id: str, strategy_id: str) -> Dict[str, Any] | None:
        if self.supabase is None:
            return None
        try:
            result = (
                self.supabase.table("user_strategies")
                .select("*")
                .eq("user_id", user_id)
                .eq("strategy_id", strategy_id)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None

    def update_state(self, user_id: str, strategy_id: str, state: str) -> Dict[str, Any] | None:
        now = now_kst().isoformat()
        if self.supabase is None:
            return None
        try:
            result = (
                self.supabase.table("user_strategies")
                .update({"state": state, "updated_at": now})
                .eq("user_id", user_id)
                .eq("strategy_id", strategy_id)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None

    def list_active(self, user_id: str) -> List[Dict[str, Any]]:
        items = [item for item in self.list(user_id) if item.get("state") == "running"]
        return items

    def update_runtime_metrics(
        self,
        user_id: str,
        metrics_by_strategy: Dict[str, Dict[str, float | int]],
    ) -> None:
        """Persist latest per-strategy runtime metrics used by dashboard/portfolio views."""
        if self.supabase is None:
            return
        rows = self.list(user_id)
        if not rows:
            return
        now = now_kst().isoformat()
        for row in rows:
            strategy_id = row.get("strategy_id")
            if not strategy_id:
                continue
            metrics = metrics_by_strategy.get(str(strategy_id), {})
            payload = {
                "positions_count": int(metrics.get("positions_count", 0) or 0),
                "pnl_today_value": float(metrics.get("pnl_today_value", 0.0) or 0.0),
                "pnl_today_pct": float(metrics.get("pnl_today_pct", 0.0) or 0.0),
                "updated_at": now,
            }
            try:
                (
                    self.supabase.table("user_strategies")
                    .update(payload)
                    .eq("user_id", user_id)
                    .eq("strategy_id", strategy_id)
                    .execute()
                )
            except Exception:
                continue
