from __future__ import annotations

from typing import Any, Dict

from app.core.config import Settings
from app.core.time import now_kst
from app.storage.supabase_client import get_supabase_client


class UsersRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def get(self, user_id: str) -> Dict[str, Any] | None:
        if self.supabase is None:
            return None
        try:
            result = (
                self.supabase.table("app_users")
                .select("*")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None

    def get_any(self) -> Dict[str, Any] | None:
        if self.supabase is None:
            return None
        try:
            result = (
                self.supabase.table("app_users")
                .select("*")
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return None
        return None

    def ensure(self, user_id: str, display_name: str | None = None) -> Dict[str, Any]:
        existing = self.get(user_id)
        if existing:
            return existing
        row = {
            "id": user_id,
            "display_name": display_name,
            "created_at": now_kst().isoformat(),
            "updated_at": now_kst().isoformat(),
        }
        if self.supabase is None:
            return row
        try:
            self.supabase.table("app_users").insert(row).execute()
        except Exception:
            return row
        return row
