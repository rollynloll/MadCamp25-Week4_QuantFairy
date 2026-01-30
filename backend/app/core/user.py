from __future__ import annotations

from typing import Iterable

from app.core.config import Settings
from app.core.errors import APIError
from app.storage.supabase_client import get_supabase_client
from app.storage.users_repo import UsersRepository


def resolve_user_id(settings: Settings, raw_user_id: str | None) -> str:
    if raw_user_id:
        return raw_user_id
    if settings.default_user_id:
        return settings.default_user_id

    users_repo = UsersRepository(settings)
    existing_user = users_repo.get_any()
    if existing_user and existing_user.get("id"):
        return existing_user["id"]

    supabase = get_supabase_client(settings)
    if supabase is not None:
        for table in _candidate_tables():
            try:
                result = (
                    supabase.table(table)
                    .select("user_id")
                    .limit(1)
                    .execute()
                )
                data = getattr(result, "data", None)
                if data:
                    return data[0]["user_id"]
            except Exception:
                continue

    raise APIError(
        "USER_ID_REQUIRED",
        "User id is required",
        "Provide user_id query or X-User-Id header, or set DEFAULT_USER_ID",
        status_code=400,
    )


def _candidate_tables() -> Iterable[str]:
    return [
        "user_settings",
        "user_accounts",
        "user_strategies",
        "trades",
        "positions",
        "alerts",
    ]
