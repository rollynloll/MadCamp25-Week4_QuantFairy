from __future__ import annotations

from typing import Optional

from app.core.config import Settings

try:
    from supabase import Client, create_client
except Exception:  # pragma: no cover - optional dependency
    Client = None
    create_client = None


_supabase_client: Optional["Client"] = None


def get_supabase_client(settings: Settings) -> Optional["Client"]:
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None
    if create_client is None:
        return None
    _supabase_client = create_client(
        settings.supabase_url, settings.supabase_service_role_key
    )
    return _supabase_client
