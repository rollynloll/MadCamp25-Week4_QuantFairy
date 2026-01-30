from __future__ import annotations

from typing import Any, Dict

from app.core.config import Settings
from app.core.time import now_kst, plus_hours
from app.storage.supabase_client import get_supabase_client


_memory_settings: Dict[str, Dict[str, Any]] = {}


DEFAULT_SETTINGS = {
    "environment": "paper",
    "kill_switch": False,
    "kill_switch_reason": None,
    "bot_state": "running",
    "next_run_at": None,
}


class UserSettingsRepository:
    def __init__(self, settings: Settings) -> None:
        self.supabase = get_supabase_client(settings)

    def get_or_create(self, user_id: str) -> Dict[str, Any]:
        if self.supabase is None:
            return self._get_memory(user_id)
        try:
            result = (
                self.supabase.table("user_settings")
                .select("*")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0]
        except Exception:
            return self._get_memory(user_id)

        row = {
            "user_id": user_id,
            **DEFAULT_SETTINGS,
            "next_run_at": plus_hours(1).isoformat(),
            "updated_at": now_kst().isoformat(),
        }
        try:
            self.supabase.table("user_settings").insert(row).execute()
        except Exception:
            return self._get_memory(user_id)
        return row

    def update(self, user_id: str, values: Dict[str, Any]) -> Dict[str, Any]:
        row = {
            "user_id": user_id,
            **values,
            "updated_at": now_kst().isoformat(),
        }
        if self.supabase is None:
            current = self._get_memory(user_id)
            current.update(row)
            _memory_settings[user_id] = current
            return current
        try:
            self.supabase.table("user_settings").upsert(row).execute()
            return row
        except Exception:
            current = self._get_memory(user_id)
            current.update(row)
            _memory_settings[user_id] = current
            return current

    def _get_memory(self, user_id: str) -> Dict[str, Any]:
        if user_id not in _memory_settings:
            _memory_settings[user_id] = {
                "user_id": user_id,
                **DEFAULT_SETTINGS,
                "next_run_at": plus_hours(1).isoformat(),
                "updated_at": now_kst().isoformat(),
            }
        return _memory_settings[user_id]
