from __future__ import annotations

import asyncio
import json
from typing import Any, Literal, Optional
import logging
import anyio
from datetime import datetime, timedelta, timezone

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
    BarsResponse,
)
from app.services.trading_service import (
    fetch_order_by_id,
    fetch_orders,
    fetch_positions,
    fetch_last_fill,
)


router = APIRouter(prefix="/trading", tags=["trading-monitor"])
logger = logging.getLogger("uvicorn.error")

try:  # optional alpaca-py data client
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    from alpaca.data.enums import DataFeed
except Exception:  # pragma: no cover - optional dependency
    StockHistoricalDataClient = None
    StockBarsRequest = None
    TimeFrame = None
    TimeFrameUnit = None
    DataFeed = None

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


def _parse_timeframe(raw: str) -> Any:
    if TimeFrame is None or TimeFrameUnit is None:
        raise APIError("SERVER_ERROR", "alpaca data client unavailable", status_code=500)
    value = raw.strip().lower()
    if value in {"1min", "1m", "minute"}:
        return TimeFrame.Minute
    if value in {"1hour", "1h", "hour"}:
        return TimeFrame.Hour
    if value in {"1day", "1d", "day"}:
        return TimeFrame.Day
    if value.endswith("min"):
        amount = int(value[:-3])
        return TimeFrame(amount, TimeFrameUnit.Minute)
    if value.endswith("hour") or value.endswith("hr"):
        amount = int(value[:-4]) if value.endswith("hour") else int(value[:-2])
        return TimeFrame(amount, TimeFrameUnit.Hour)
    if value.endswith("day"):
        amount = int(value[:-3])
        return TimeFrame(amount, TimeFrameUnit.Day)
    raise APIError("VALIDATION_ERROR", f"unsupported timeframe: {raw}", status_code=400)


def _parse_data_feed(raw: str | None) -> Any:
    if not raw:
        return None
    if DataFeed is None:
        return raw
    try:
        return DataFeed(raw)
    except Exception:
        raise APIError("VALIDATION_ERROR", f"unsupported feed: {raw}", status_code=400)


def _bar_attr(bar: Any, *names: str) -> Any:
    for name in names:
        if hasattr(bar, name):
            return getattr(bar, name)
        if isinstance(bar, dict) and name in bar:
            return bar[name]
    return None


def _map_event(event: dict[str, Any]) -> dict[str, Any] | None:
    event_type = event.get("T")
    if event_type in {"success", "error", "subscription"}:
        message = event.get("msg")
        if event_type == "subscription" and not message:
            message = "subscribed"
        if event_type == "error" and not message:
            message = "error"
        return {"type": "status", "message": message, "raw": event}
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


@router.get("/bars", response_model=BarsResponse)
async def get_bars(
    symbol: str,
    timeframe: str = Query(default="1Min"),
    limit: int = Query(default=200, ge=1, le=1000),
    feed: Optional[str] = Query(default=None),
):
    settings = get_settings()
    if not settings.alpaca_api_key or not settings.alpaca_secret_key:
        raise APIError("CONFIG_ERROR", "Alpaca keys missing", status_code=400)
    if StockHistoricalDataClient is None or StockBarsRequest is None:
        raise APIError("SERVER_ERROR", "alpaca data client unavailable", status_code=500)

    data_feed = feed or settings.alpaca_data_feed
    parsed_feed = _parse_data_feed(data_feed)
    tf = _parse_timeframe(timeframe)

    def _fetch(start_dt: datetime | None = None):
        client = StockHistoricalDataClient(
            settings.alpaca_api_key,
            settings.alpaca_secret_key,
        )
        request = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=tf,
            limit=limit,
            start=start_dt,
            feed=parsed_feed,
        )
        return client.get_stock_bars(request)

    barset = await anyio.to_thread.run_sync(_fetch)
    raw_bars = []
    if barset is not None:
        raw_bars = barset.data.get(symbol, [])

    if not raw_bars and timeframe.lower().endswith("day"):
        fallback_start = datetime.now(timezone.utc) - timedelta(days=max(365, limit * 2))
        logger.info(
            "alpaca.bars fallback start=%s timeframe=%s feed=%s",
            fallback_start.isoformat(),
            timeframe,
            data_feed,
        )
        barset = await anyio.to_thread.run_sync(lambda: _fetch(fallback_start))
        if barset is not None:
            raw_bars = barset.data.get(symbol, [])

    items = []
    for bar in raw_bars:
        timestamp = _bar_attr(bar, "t", "timestamp", "time")
        if hasattr(timestamp, "isoformat"):
            timestamp = timestamp.isoformat()
        else:
            timestamp = str(timestamp)
        open_val = _bar_attr(bar, "o", "open")
        high_val = _bar_attr(bar, "h", "high")
        low_val = _bar_attr(bar, "l", "low")
        close_val = _bar_attr(bar, "c", "close")
        volume_val = _bar_attr(bar, "v", "volume")
        items.append(
            {
                "time": timestamp,
                "open": float(open_val),
                "high": float(high_val),
                "low": float(low_val),
                "close": float(close_val),
                "volume": float(volume_val),
            }
        )

    logger.info(
        "alpaca.bars symbol=%s timeframe=%s feed=%s count=%s",
        symbol,
        timeframe,
        data_feed,
        len(items),
    )

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "feed": data_feed,
        "bars": items,
    }


@router.websocket("/stream")
async def stream_market_data(websocket: WebSocket):
    await websocket.accept()
    settings = get_settings()
    if not settings.alpaca_api_key or not settings.alpaca_secret_key:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "status",
                    "message": "missing_alpaca_keys",
                }
            )
        )
        await websocket.close(code=1011)
        return

    query = websocket.query_params
    symbols = _parse_symbols(query.get("symbols"))
    channels = _parse_channels(query.get("channels"))
    feed = query.get("feed") or settings.alpaca_data_feed
    stream_url = settings.alpaca_data_stream_url or f"wss://stream.data.alpaca.markets/v2/{feed}"
    logger.info(
        "alpaca.stream.connect feed=%s symbols=%s channels=%s url=%s",
        feed,
        ",".join(symbols),
        ",".join(sorted(channels)),
        stream_url,
    )

    async def forward_messages(alpaca_ws):
        total_messages = 0
        last_log = asyncio.get_event_loop().time()
        while True:
            message = await alpaca_ws.recv()
            try:
                events = json.loads(message)
            except json.JSONDecodeError:
                continue
            if isinstance(events, dict):
                events = [events]
            total_messages += 1
            now = asyncio.get_event_loop().time()
            if now - last_log >= 10:
                logger.info(
                    "alpaca.stream.recv count=%s last_types=%s",
                    total_messages,
                    ",".join(sorted({str(evt.get("T")) for evt in events})),
                )
                last_log = now
            for event in events:
                mapped = _map_event(event)
                if mapped:
                    try:
                        await websocket.send_text(json.dumps(mapped))
                    except WebSocketDisconnect:
                        return
                    except RuntimeError:
                        return

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
                logger.info("alpaca.stream.auth %s", events)
                for event in events:
                    mapped = _map_event(event)
                    if mapped:
                        try:
                            await websocket.send_text(json.dumps(mapped))
                        except WebSocketDisconnect:
                            return
                        except RuntimeError:
                            return
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
            logger.info("alpaca.stream.subscribe %s", subscribe_payload)
            try:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "status",
                            "message": "subscribed",
                            "raw": {"channels": list(channels), "symbols": symbols, "feed": feed},
                        }
                    )
                )
            except WebSocketDisconnect:
                return
            except RuntimeError:
                return

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
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass
        except WebSocketDisconnect:
            pass
    except Exception as exc:  # pragma: no cover - defensive log for websocket failures
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "status",
                        "message": f"stream_error:{exc.__class__.__name__}",
                    }
                )
            )
        except RuntimeError:
            pass
        except WebSocketDisconnect:
            pass
        try:
            await websocket.close(code=1011)
        except RuntimeError:
            pass
        except WebSocketDisconnect:
            pass
