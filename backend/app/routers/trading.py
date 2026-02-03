from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from app.core.config import get_settings
from app.core.errors import APIError
from app.db import get_db_connection
from app.schemas.trading import (
    OrderDetailResponse,
    OrderListResponse,
    PositionListResponse,
    LastFillResponse,
)
from app.services.trading_service import (
    fetch_order_by_id,
    fetch_orders,
    fetch_positions,
    fetch_last_fill,
)


router = APIRouter(prefix="/trading", tags=["trading-monitor"])

EnvLiteral = Literal["paper", "live"]
ScopeLiteral = Literal["open", "filled", "all"]


def _resolve_user_id(user_id: Optional[str]) -> str:
    settings = get_settings()
    resolved = user_id or settings.default_user_id
    if not resolved:
        raise APIError("VALIDATION_ERROR", "user_id is required", status_code=400)
    return resolved


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    scope: ScopeLiteral = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=200),
    env: EnvLiteral = Query(default="paper"),
    user_id: Optional[str] = Query(default=None),
    conn=Depends(get_db_connection),
):
    resolved_user_id = _resolve_user_id(user_id)
    items = await fetch_orders(
        conn,
        user_id=resolved_user_id,
        environment=env,
        scope=scope,
        limit=limit,
    )
    return {"items": items}


@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: str,
    env: EnvLiteral = Query(default="paper"),
    user_id: Optional[str] = Query(default=None),
    conn=Depends(get_db_connection),
):
    resolved_user_id = _resolve_user_id(user_id)
    item = await fetch_order_by_id(
        conn,
        user_id=resolved_user_id,
        environment=env,
        order_id=order_id,
    )
    if not item:
        raise APIError("NOT_FOUND", "Order not found", status_code=404)
    return item


@router.get("/positions", response_model=PositionListResponse)
async def list_positions(
    env: EnvLiteral = Query(default="paper"),
    user_id: Optional[str] = Query(default=None),
    conn=Depends(get_db_connection),
):
    resolved_user_id = _resolve_user_id(user_id)
    items = await fetch_positions(
        conn,
        user_id=resolved_user_id,
        environment=env,
    )
    return {"items": items}


@router.get("/positions/{symbol}/last-fill", response_model=LastFillResponse)
async def get_last_fill(
    symbol: str,
    user_id: Optional[str] = Query(default=None),
    conn=Depends(get_db_connection),
):
    resolved_user_id = _resolve_user_id(user_id)
    item = await fetch_last_fill(conn, user_id=resolved_user_id, symbol=symbol)
    if not item:
        raise APIError("NOT_FOUND", "No trades for symbol", status_code=404)
    return item
