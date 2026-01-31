from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


_memory_strategies: Dict[str, Dict[str, Dict[str, Any]]] = {}


DEFAULT_STRATEGIES = [
    {
        "strategy_id": "strat_momentum_top10",
        "source_public_strategy_id": "momentum_top10_12m_v1",
        "public_version_snapshot": "1.0.0",
        "entrypoint_snapshot": "strategies.momentum_topn_v1:MomentumTopNStrategy",
        "code_version_snapshot": "seed",
        "name": "Momentum Breakout",
        "state": "running",
        "description": "Top-10 momentum breakout strategy",
        "params": {"lookback_days": 252, "top_n": 10, "rebalance": "monthly"},
        "risk_limits": {"max_position_pct": 20},
        "positions_count": 2,
        "pnl_today_value": 1240.2,
        "pnl_today_pct": 1.24,
    },
    {
        "strategy_id": "strat_mean_reversion",
        "source_public_strategy_id": None,
        "public_version_snapshot": None,
        "entrypoint_snapshot": None,
        "code_version_snapshot": None,
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

    def _seed_memory(self, user_id: str) -> None:
        if user_id in _memory_strategies:
            return
        now = now_kst().isoformat()
        _memory_strategies[user_id] = {}
        for strat in DEFAULT_STRATEGIES:
            _memory_strategies[user_id][strat["strategy_id"]] = {
                **strat,
                "user_id": user_id,
                "created_at": now,
                "updated_at": now,
            }

    def ensure_seed(self, user_id: str) -> None:
        if self.supabase is None:
            self._seed_memory(user_id)
            return
        try:
            result = (
                self.supabase.table("user_strategies")
                .select("strategy_id")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return
            now = now_kst().isoformat()
            seed_rows = [
                {
                    **item,
                    "user_id": user_id,
                    "created_at": now,
                    "updated_at": now,
                }
                for item in DEFAULT_STRATEGIES
            ]
            self.supabase.table("user_strategies").insert(seed_rows).execute()
        except Exception:
            self._seed_memory(user_id)

    def list(self, user_id: str) -> List[Dict[str, Any]]:
        if self.supabase is None:
            self._seed_memory(user_id)
            return list(_memory_strategies[user_id].values())
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
            self._seed_memory(user_id)
        return list(_memory_strategies[user_id].values())

    def get(self, user_id: str, strategy_id: str) -> Dict[str, Any] | None:
        if self.supabase is None:
            self._seed_memory(user_id)
            return _memory_strategies[user_id].get(strategy_id)
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
            self._seed_memory(user_id)
        return _memory_strategies[user_id].get(strategy_id)

    def update_state(self, user_id: str, strategy_id: str, state: str) -> Dict[str, Any] | None:
        now = now_kst().isoformat()
        if self.supabase is None:
            self._seed_memory(user_id)
            strat = _memory_strategies[user_id].get(strategy_id)
            if not strat:
                return None
            strat["state"] = state
            strat["updated_at"] = now
            return strat
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
            self._seed_memory(user_id)
            strat = _memory_strategies[user_id].get(strategy_id)
            if strat:
                strat["state"] = state
                strat["updated_at"] = now
                return strat
        return None

    def list_active(self, user_id: str) -> List[Dict[str, Any]]:
        items = [item for item in self.list(user_id) if item.get("state") == "running"]
        return items
