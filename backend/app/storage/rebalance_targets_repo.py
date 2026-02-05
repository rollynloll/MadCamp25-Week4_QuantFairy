from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


class RebalanceTargetsRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def list(self, user_id: str, environment: str) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return []
        try:
            result = (
                self.supabase.table("rebalance_targets")
                .select("*")
                .eq("user_id", user_id)
                .eq("environment", environment)
                .order("updated_at", desc=True)
                .execute()
            )
            data = getattr(result, "data", None)
            if data is not None:
                return data
        except Exception:
            return []
        return []

    def replace_for_env(
        self,
        user_id: str,
        environment: str,
        targets: Dict[str, float],
        target_cash_pct: float,
    ) -> None:
        if self.supabase is None:
            return
        now = now_kst().isoformat()
        rows: List[Dict[str, Any]] = []
        for strategy_id, weight in targets.items():
            rows.append(
                {
                    "user_id": user_id,
                    "environment": environment,
                    "strategy_id": strategy_id,
                    "target_weight_pct": float(weight),
                    "target_cash_pct": float(target_cash_pct),
                    "updated_at": now,
                }
            )
        try:
            (
                self.supabase.table("rebalance_targets")
                .delete()
                .eq("user_id", user_id)
                .eq("environment", environment)
                .execute()
            )
            if rows:
                self.supabase.table("rebalance_targets").insert(rows).execute()
        except Exception:
            return
