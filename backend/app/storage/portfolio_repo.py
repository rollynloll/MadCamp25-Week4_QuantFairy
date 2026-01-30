from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


class PortfolioRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def list_equity_curve(
        self, user_id: str, environment: str, range_days: int
    ) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return []
        start = now_kst() - timedelta(days=range_days)
        try:
            result = (
                self.supabase.table("portfolio_snapshots")
                .select("as_of,equity")
                .eq("user_id", user_id)
                .eq("environment", environment)
                .gte("as_of", start.isoformat())
                .order("as_of", desc=False)
                .execute()
            )
            data = getattr(result, "data", None)
            if data is not None:
                return [
                    {"t": item["as_of"], "equity": float(item["equity"])}
                    for item in data
                ]
        except Exception:
            return []
        return []
