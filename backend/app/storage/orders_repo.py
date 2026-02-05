from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.core.config import Settings
from app.storage.supabase_client import get_supabase_client

logger = logging.getLogger("uvicorn.error")


class OrdersRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def upsert_many(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rows:
            return []
        if self.supabase is None:
            return rows
        try:
            self.supabase.table("orders").upsert(rows, on_conflict="order_id").execute()
            return rows
        except Exception as exc:
            logger.warning("orders.upsert_many fallback due to schema mismatch/error: %s", exc)
            # Backward-compatible fallback for older DB schema.
            allowed = {
                "order_id",
                "user_id",
                "environment",
                "symbol",
                "side",
                "qty",
                "type",
                "status",
                "submitted_at",
                "filled_at",
                "strategy_id",
            }
            stripped = [{k: v for k, v in row.items() if k in allowed} for row in rows]
            try:
                self.supabase.table("orders").upsert(stripped, on_conflict="order_id").execute()
            except Exception:
                return rows
        return rows

    def list_recent(
        self,
        user_id: str,
        environment: str,
        *,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        if self.supabase is None:
            return []
        try:
            result = (
                self.supabase.table("orders")
                .select("*")
                .eq("user_id", user_id)
                .eq("environment", environment)
                .order("submitted_at", desc=True)
                .limit(limit)
                .execute()
            )
            data = getattr(result, "data", None)
            if data is not None:
                return data
        except Exception:
            return []
        return []

    def delete_open_orders(self, user_id: str, environment: str, limit: int = 2000) -> int:
        if self.supabase is None:
            return 0
        final_statuses = {"filled", "canceled", "cancelled", "rejected", "expired"}
        try:
            rows = self.list_recent(user_id, environment, limit=limit)
            open_ids: List[str] = []
            for row in rows:
                order_id = row.get("order_id")
                if not order_id:
                    continue
                status = str(row.get("status") or "").strip().lower()
                if "." in status:
                    status = status.split(".")[-1]
                if status in final_statuses:
                    continue
                open_ids.append(str(order_id))
            for order_id in open_ids:
                (
                    self.supabase.table("orders")
                    .delete()
                    .eq("user_id", user_id)
                    .eq("environment", environment)
                    .eq("order_id", order_id)
                    .execute()
                )
            return len(open_ids)
        except Exception:
            return 0
