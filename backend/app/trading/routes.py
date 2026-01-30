from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.errors import APIError
from app.schemas.trading import (
    KillSwitchRequest,
    KillSwitchResponse,
    TradingModeRequest,
    TradingModeResponse,
)
from app.storage.settings_repo import SettingsRepository


router = APIRouter()


@router.post("/trading/mode", response_model=TradingModeResponse)
async def set_trading_mode(payload: TradingModeRequest):
    settings = get_settings()
    repo = SettingsRepository(settings)
    if payload.environment == "live" and not settings.allow_live_trading:
        raise APIError(
            "LIVE_TRADING_DISABLED",
            "Live trading is disabled",
            "Set ALLOW_LIVE_TRADING=true to enable",
            status_code=403,
        )
    repo.set("environment", payload.environment)
    return TradingModeResponse(environment=payload.environment)


@router.post("/trading/kill-switch", response_model=KillSwitchResponse)
async def set_kill_switch(payload: KillSwitchRequest):
    settings = get_settings()
    repo = SettingsRepository(settings)
    repo.set("kill_switch", payload.enabled)
    if payload.reason:
        repo.set("kill_switch_reason", payload.reason)
    return KillSwitchResponse(enabled=payload.enabled)
