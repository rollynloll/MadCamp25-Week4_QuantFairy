from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import Settings
from app.storage.supabase_client import get_supabase_client


DEFAULT_TRADES = [
    {
        "fill_id": "fill_001",
        "filled_at": "2026-01-29T16:40:12+09:00",
        "symbol": "AAPL",
        "side": "buy",
        "qty": 100,
        "price": 178.25,
        "strategy_id": "strat_mean_reversion",
        "strategy_name": "Mean Reversion Alpha",
    }
]


class TradesRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def list_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return DEFAULT_TRADES[:limit]
        try:
            result = (
                self.supabase.table("trades")
                .select("*")
                .order("filled_at", desc=True)
                .limit(limit)
                .execute()
            )
            data = getattr(result, "data", None)
            if data is not None:
                return data
        except Exception:
            return DEFAULT_TRADES[:limit]
        return DEFAULT_TRADES[:limit]
