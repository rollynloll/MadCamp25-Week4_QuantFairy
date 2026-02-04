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

    def replace_equity_curve_range(
        self,
        user_id: str,
        environment: str,
        points: List[Dict[str, Any]],
        *,
        cash: float,
    ) -> None:
        """Replace snapshot rows in the incoming time window with fresh Alpaca history points."""
        if self.supabase is None or not points:
            return
        sorted_points = sorted(
            [p for p in points if p.get("t") is not None],
            key=lambda p: str(p["t"]),
        )
        if not sorted_points:
            return
        start = str(sorted_points[0]["t"])
        end = str(sorted_points[-1]["t"])
        rows = []
        for point in sorted_points:
            rows.append(
                {
                    "user_id": user_id,
                    "environment": environment,
                    "as_of": str(point["t"]),
                    "equity": float(point.get("equity", 0.0) or 0.0),
                    "cash": float(cash),
                }
            )
        try:
            (
                self.supabase.table("portfolio_snapshots")
                .delete()
                .eq("user_id", user_id)
                .eq("environment", environment)
                .gte("as_of", start)
                .lte("as_of", end)
                .execute()
            )
            self.supabase.table("portfolio_snapshots").insert(rows).execute()
        except Exception:
            return
