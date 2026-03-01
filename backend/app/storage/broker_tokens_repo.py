from __future__ import annotations

from typing import Any, Dict

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


class BrokerTokensRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def get_latest(
        self, user_id: str, broker: str, environment: str
    ) -> Dict[str, Any] | None:
        if self.supabase is None:
            return None
        try:
            result = (
                self.supabase.table("broker_tokens")
                .select("*")
                .eq("user_id", user_id)
                .eq("broker", broker)
                .eq("environment", environment)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None

    def upsert_token(
        self,
        user_id: str,
        broker: str,
        environment: str,
        access_token: str,
        refresh_token: str | None = None,
        token_type: str | None = None,
        scope: str | None = None,
        expires_at: str | None = None,
    ) -> Dict[str, Any]:
        row = {
            "user_id": user_id,
            "broker": broker,
            "environment": environment,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": token_type,
            "scope": scope,
            "expires_at": expires_at,
            "updated_at": now_kst().isoformat(),
        }
        if self.supabase is None:
            return row
        try:
            self.supabase.table("broker_tokens").upsert(row).execute()
        except Exception:
            return row
        return row
