from __future__ import annotations

from typing import Any, Dict

from app.core.config import Settings
from app.core.time import now_kst, plus_hours
from app.storage.supabase_client import get_supabase_client


_memory_settings: Dict[str, Any] = {}


class SettingsRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.supabase = get_supabase_client(settings)

    def _get_memory(self, key: str, default: Any) -> Any:
        if key not in _memory_settings:
            _memory_settings[key] = default
        return _memory_settings[key]

    def get(self, key: str, default: Any = None) -> Any:
        if self.supabase is None:
            return self._get_memory(key, default)
        try:
            result = (
                self.supabase.table("settings")
                .select("key,value")
                .eq("key", key)
                .execute()
            )
            data = getattr(result, "data", None)
            if data:
                return data[0].get("value")
        except Exception:
            return self._get_memory(key, default)
        return self._get_memory(key, default)

    def set(self, key: str, value: Any) -> None:
        if self.supabase is None:
            _memory_settings[key] = value
            return
        try:
            self.supabase.table("settings").upsert(
                {
                    "key": key,
                    "value": value,
                    "updated_at": now_kst().isoformat(),
                }
            ).execute()
        except Exception:
            _memory_settings[key] = value

    def ensure_defaults(self) -> None:
        defaults = {
            "environment": "paper",
            "kill_switch": False,
            "bot_state": "running",
            "next_run_at": plus_hours(1).isoformat(),
            "worker_state": "running",
            "worker_last_heartbeat_at": now_kst().isoformat(),
        }
        for key, value in defaults.items():
            if self.get(key, None) is None:
                self.set(key, value)
