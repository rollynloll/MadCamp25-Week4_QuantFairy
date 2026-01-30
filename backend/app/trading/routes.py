from __future__ import annotations

from fastapi import APIRouter, Header, Query

from app.core.config import get_settings
from app.core.errors import APIError
from app.core.user import resolve_user_id
from app.schemas.trading import (
    KillSwitchRequest,
    KillSwitchResponse,
    TradingModeRequest,
    TradingModeResponse,
)
from app.storage.user_settings_repo import UserSettingsRepository


router = APIRouter()


@router.post("/trading/mode", response_model=TradingModeResponse)
async def set_trading_mode(
    payload: TradingModeRequest,
    user_id: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    settings = get_settings()
    resolved_user_id = resolve_user_id(settings, x_user_id or user_id)
    repo = UserSettingsRepository(settings)
    if payload.environment == "live" and not settings.allow_live_trading:
        raise APIError(
            "LIVE_TRADING_DISABLED",
            "Live trading is disabled",
            "Set ALLOW_LIVE_TRADING=true to enable",
            status_code=403,
        )
    repo.update(resolved_user_id, {"environment": payload.environment})
    return TradingModeResponse(environment=payload.environment)


@router.post("/trading/kill-switch", response_model=KillSwitchResponse)
async def set_kill_switch(
    payload: KillSwitchRequest,
    user_id: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    settings = get_settings()
    resolved_user_id = resolve_user_id(settings, x_user_id or user_id)
    repo = UserSettingsRepository(settings)
    repo.update(
        resolved_user_id,
        {"kill_switch": payload.enabled, "kill_switch_reason": payload.reason},
    )
    return KillSwitchResponse(enabled=payload.enabled)
