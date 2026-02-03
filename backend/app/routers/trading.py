from __future__ import annotations

import asyncio
import json
from typing import Any, Literal, Optional

import websockets
from websockets.exceptions import ConnectionClosed

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

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


def _parse_symbols(raw: str | None) -> list[str]:
    if not raw:
        return ["AAPL"]
    symbols = [item.strip().upper() for item in raw.split(",") if item.strip()]
    return symbols or ["AAPL"]


def _parse_channels(raw: str | None) -> set[str]:
    if not raw:
        return {"trades", "quotes", "bars"}
    items = {item.strip().lower() for item in raw.split(",") if item.strip()}
    allowed = {"trades", "quotes", "bars"}
    return {item for item in items if item in allowed} or {"trades", "quotes", "bars"}


def _map_event(event: dict[str, Any]) -> dict[str, Any] | None:
    event_type = event.get("T")
    if event_type in {"success", "error", "subscription"}:
        return {"type": "status", "message": event.get("msg"), "raw": event}
    if event_type == "q":
        return {
            "type": "quote",
            "symbol": event.get("S"),
            "bid": event.get("bp"),
            "bid_size": event.get("bs"),
            "ask": event.get("ap"),
            "ask_size": event.get("as"),
            "time": event.get("t"),
        }
    if event_type == "t":
        return {
            "type": "trade",
            "symbol": event.get("S"),
            "price": event.get("p"),
            "size": event.get("s"),
            "time": event.get("t"),
        }
    if event_type == "b":
        return {
            "type": "bar",
            "symbol": event.get("S"),
            "open": event.get("o"),
            "high": event.get("h"),
            "low": event.get("l"),
            "close": event.get("c"),
            "volume": event.get("v"),
            "time": event.get("t"),
        }
    return None


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


@router.websocket("/stream")
async def stream_market_data(websocket: WebSocket):
    await websocket.accept()
    settings = get_settings()
    if not settings.alpaca_api_key or not settings.alpaca_secret_key:
        await websocket.close(code=1011)
        return

    query = websocket.query_params
    symbols = _parse_symbols(query.get("symbols"))
    channels = _parse_channels(query.get("channels"))
    feed = query.get("feed") or settings.alpaca_data_feed
    stream_url = settings.alpaca_data_stream_url or f"wss://stream.data.alpaca.markets/v2/{feed}"

    async def forward_messages(alpaca_ws):
        while True:
            message = await alpaca_ws.recv()
            try:
                events = json.loads(message)
            except json.JSONDecodeError:
                continue
            if isinstance(events, dict):
                events = [events]
            for event in events:
                mapped = _map_event(event)
                if mapped:
                    await websocket.send_text(json.dumps(mapped))

    try:
        async with websockets.connect(stream_url, ping_interval=20, ping_timeout=20) as alpaca_ws:
            await alpaca_ws.send(
                json.dumps(
                    {
                        "action": "auth",
                        "key": settings.alpaca_api_key,
                        "secret": settings.alpaca_secret_key,
                    }
                )
            )
            # wait for auth response
            auth_timeout = asyncio.get_event_loop().time() + 5
            while True:
                raw = await alpaca_ws.recv()
                events = json.loads(raw)
                if isinstance(events, dict):
                    events = [events]
                for event in events:
                    mapped = _map_event(event)
                    if mapped:
                        await websocket.send_text(json.dumps(mapped))
                if any(evt.get("msg") == "authenticated" for evt in events):
                    break
                if asyncio.get_event_loop().time() > auth_timeout:
                    await websocket.close(code=1011)
                    return

            subscribe_payload: dict[str, Any] = {"action": "subscribe"}
            if "trades" in channels:
                subscribe_payload["trades"] = symbols
            if "quotes" in channels:
                subscribe_payload["quotes"] = symbols
            if "bars" in channels:
                subscribe_payload["bars"] = symbols
            await alpaca_ws.send(json.dumps(subscribe_payload))

            forward_task = asyncio.create_task(forward_messages(alpaca_ws))
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                forward_task.cancel()
            finally:
                if not forward_task.done():
                    forward_task.cancel()
    except ConnectionClosed:
        await websocket.close(code=1011)
