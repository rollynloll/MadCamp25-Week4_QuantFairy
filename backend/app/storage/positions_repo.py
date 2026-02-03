from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config import Settings
from app.storage.supabase_client import get_supabase_client


class PositionsRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def count(self, user_id: str, environment: str) -> int:
        if self.supabase is None:
            return 0
        try:
            result = (
                self.supabase.table("positions")
                .select("position_id", count="exact")
                .eq("user_id", user_id)
                .eq("environment", environment)
                .execute()
            )
            count = getattr(result, "count", None)
            if count is not None:
                return int(count)
            data = getattr(result, "data", None)
            if data is not None:
                return len(data)
        except Exception:
            return 0
        return 0

    def list(
        self,
        user_id: str,
        environment: str,
        *,
        q: Optional[str] = None,
        side: Optional[str] = None,
        strategy_id: Optional[str] = None,
        sort: Optional[str] = None,
        order: str = "desc",
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return []

        def _build_query(use_alt_strategy_id: bool = False):
            query = (
                self.supabase.table("positions")
                .select("*")
                .eq("user_id", user_id)
                .eq("environment", environment)
            )
            if q:
                query = query.ilike("symbol", f"%{q}%")
            if side and side != "all":
                query = query.eq("side", side)
            if strategy_id:
                col = "user_strategy_id" if use_alt_strategy_id else "strategy_id"
                query = query.eq(col, strategy_id)
            if sort:
                sort_col = {
                    "symbol": "symbol",
                    "value": "market_value",
                    "pnl": "unrealized_pnl",
                    "pnl_pct": "unrealized_pnl_pct",
                }.get(sort, sort)
                if sort_col:
                    query = query.order(sort_col, desc=(order == "desc"))
            return query.limit(limit)

        try:
            result = _build_query().execute()
            data = getattr(result, "data", None)
            if data is not None:
                return data
        except Exception:
            if strategy_id:
                try:
                    result = _build_query(use_alt_strategy_id=True).execute()
                    data = getattr(result, "data", None)
                    if data is not None:
                        return data
                except Exception:
                    return []
            return []
        return []
