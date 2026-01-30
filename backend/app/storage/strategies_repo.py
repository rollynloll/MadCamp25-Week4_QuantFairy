from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


_memory_strategies: Dict[str, Dict[str, Any]] = {}


DEFAULT_STRATEGIES = [
    {
        "strategy_id": "strat_momentum_top10",
        "name": "Momentum Breakout",
        "state": "running",
        "description": "Top-10 momentum breakout strategy",
        "params": {"rebalance": "weekly", "universe": 10},
        "risk_limits": {"max_position_pct": 20},
        "positions_count": 2,
        "pnl_today_value": 1240.2,
        "pnl_today_pct": 1.24,
    },
    {
        "strategy_id": "strat_mean_reversion",
        "name": "Mean Reversion Alpha",
        "state": "paused",
        "description": "Mean reversion on large cap universe",
        "params": {"lookback_days": 20},
        "risk_limits": {"max_loss_pct": 5},
        "positions_count": 1,
        "pnl_today_value": -120.5,
        "pnl_today_pct": -0.12,
    },
]


class StrategiesRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.supabase = get_supabase_client(settings)

    def _seed_memory(self) -> None:
        if _memory_strategies:
            return
        now = now_kst().isoformat()
        for strat in DEFAULT_STRATEGIES:
            _memory_strategies[strat["strategy_id"]] = {
                **strat,
                "created_at": now,
                "updated_at": now,
            }

    def ensure_seed(self) -> None:
        if self.supabase is None:
            self._seed_memory()
            return
        try:
            result = self.supabase.table("strategies").select("strategy_id").execute()
            data = getattr(result, "data", None)
            if data:
                return
            now = now_kst().isoformat()
            seed_rows = [
                {**item, "created_at": now, "updated_at": now}
                for item in DEFAULT_STRATEGIES
            ]
            self.supabase.table("strategies").insert(seed_rows).execute()
        except Exception:
            self._seed_memory()

    def list(self) -> List[Dict[str, Any]]:
        if self.supabase is None:
            self._seed_memory()
            return list(_memory_strategies.values())
        try:
            result = self.supabase.table("strategies").select("*").execute()
            data = getattr(result, "data", None)
            if data is not None:
                return data
        except Exception:
            self._seed_memory()
        return list(_memory_strategies.values())

    def get(self, strategy_id: str) -> Dict[str, Any] | None:
        if self.supabase is None:
            self._seed_memory()
            return _memory_strategies.get(strategy_id)
        try:
            result = (
                self.supabase.table("strategies")
                .select("*")
                .eq("strategy_id", strategy_id)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            self._seed_memory()
        return _memory_strategies.get(strategy_id)

    def update_state(self, strategy_id: str, state: str) -> Dict[str, Any] | None:
        now = now_kst().isoformat()
        if self.supabase is None:
            self._seed_memory()
            strat = _memory_strategies.get(strategy_id)
            if not strat:
                return None
            strat["state"] = state
            strat["updated_at"] = now
            return strat
        try:
            result = (
                self.supabase.table("strategies")
                .update({"state": state, "updated_at": now})
                .eq("strategy_id", strategy_id)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            self._seed_memory()
            strat = _memory_strategies.get(strategy_id)
            if strat:
                strat["state"] = state
                strat["updated_at"] = now
                return strat
        return None

    def list_active(self) -> List[Dict[str, Any]]:
        items = [item for item in self.list() if item.get("state") == "running"]
        return items
