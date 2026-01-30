from __future__ import annotations

from typing import Any, Dict, List

from app.core.config import Settings
from app.storage.supabase_client import get_supabase_client


DEFAULT_ALERTS = [
    {
        "alert_id": "al_001",
        "severity": "warning",
        "type": "risk_limit_hit",
        "title": "Max per-symbol exposure hit",
        "message": "TSLA order blocked by risk limit",
        "occurred_at": "2026-01-29T16:40:12+09:00",
        "link": {"page": "trading", "tab": "risk"},
    }
]


class AlertsRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def list_recent(self, limit: int = 5) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return DEFAULT_ALERTS[:limit]
        try:
            result = (
                self.supabase.table("alerts")
                .select("*")
                .order("occurred_at", desc=True)
                .limit(limit)
                .execute()
            )
            data = getattr(result, "data", None)
            if data is not None:
                return data
        except Exception:
            return DEFAULT_ALERTS[:limit]
        return DEFAULT_ALERTS[:limit]
