from __future__ import annotations

from fastapi import APIRouter, Header, Query

from app.core.config import get_settings
from app.core.user import resolve_user_id
from app.schemas.trading import (
    KillSwitchRequest,
    KillSwitchResponse,
    TradingModeRequest,
    TradingModeResponse,
)
from app.services.trading_service import TradingService

router = APIRouter()


def _svc(user_id: str | None, x_user_id: str | None) -> TradingService:
    settings = get_settings()
    resolved = resolve_user_id(settings, x_user_id or user_id)
    return TradingService(settings, resolved)


@router.post("/trading/mode", response_model=TradingModeResponse)
async def set_trading_mode(
    payload: TradingModeRequest,
    user_id: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    settings = get_settings()
    return _svc(user_id, x_user_id).set_mode(payload.environment, settings.allow_live_trading)


@router.post("/trading/kill-switch", response_model=KillSwitchResponse)
async def set_kill_switch(
    payload: KillSwitchRequest,
    user_id: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    return _svc(user_id, x_user_id).set_kill_switch(payload.enabled, payload.reason)
