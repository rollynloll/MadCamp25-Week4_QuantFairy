from __future__ import annotations

from typing import Any, Dict

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


class UserAccountsRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def get_latest(self, user_id: str, environment: str) -> Dict[str, Any] | None:
        if self.supabase is None:
            return None
        try:
            result = (
                self.supabase.table("user_accounts")
                .select("*")
                .eq("user_id", user_id)
                .eq("environment", environment)
                .order("updated_at", desc=True)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None

    def upsert_account(
        self,
        user_id: str,
        environment: str,
        account_id: str,
        equity: float,
        cash: float,
        buying_power: float,
        currency: str,
    ) -> Dict[str, Any]:
        row = {
            "account_id": account_id,
            "user_id": user_id,
            "environment": environment,
            "equity": equity,
            "cash": cash,
            "buying_power": buying_power,
            "currency": currency,
            "updated_at": now_kst().isoformat(),
        }
        if self.supabase is None:
            return row
        try:
            self.supabase.table("user_accounts").upsert(row).execute()
        except Exception:
            return row
        return row
