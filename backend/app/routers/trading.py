from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any, Literal, Optional
import logging
import anyio
from datetime import datetime, timedelta, timezone, date
from math import ceil
import re

import websockets
from websockets.exceptions import ConnectionClosed

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.alpaca.client import AlpacaClient
from app.core.config import get_settings
from app.core.errors import APIError
from app.core.ttl_cache import TTLCache
from app.db import get_db_connection
from app.schemas.trading import (
    OrderDetailResponse,
    OrderListResponse,
    PositionListResponse,
    LastFillResponse,
    BarsResponse,
    QuoteResponse,
)
from app.services.data_provider import load_price_series
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
    from alpaca.data.requests import StockLatestQuoteRequest
    from alpaca.data.requests import StockLatestTradeRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
    from alpaca.data.enums import DataFeed, Adjustment
except Exception:  # pragma: no cover - optional dependency
    StockHistoricalDataClient = None
    StockBarsRequest = None
    StockLatestQuoteRequest = None
    StockLatestTradeRequest = None
    TimeFrame = None
    TimeFrameUnit = None
    DataFeed = None
    Adjustment = None

EnvLiteral = Literal["paper", "live"]
ScopeLiteral = Literal["open", "filled", "all"]
ORDER_SYNC_TTL = 5.0
POSITION_SYNC_TTL = 5.0
SYNC_CACHE = TTLCache(default_ttl=5.0, maxsize=256)


def _resolve_user_id(user_id: Optional[str]) -> str:
    settings = get_settings()
    resolved = user_id or settings.default_user_id
    if not resolved:
        raise APIError("VALIDATION_ERROR", "user_id is required", status_code=400)
    return resolved


def _get_field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            if value.endswith("Z"):
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_enum_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    if "." in text:
        text = text.split(".")[-1]
    return text.lower()


def _extract_latest_quote(payload: Any, symbol: str) -> dict[str, Any] | None:
    quote_obj = None
    symbol_key = symbol.upper()
    if isinstance(payload, dict):
        quote_obj = payload.get(symbol_key) or payload.get(symbol)
    if quote_obj is None and hasattr(payload, "data"):
        data = getattr(payload, "data", None)
        if isinstance(data, dict):
            quote_obj = data.get(symbol_key) or data.get(symbol)
    if quote_obj is None and hasattr(payload, "get"):
        try:
            quote_obj = payload.get(symbol_key) or payload.get(symbol)
        except Exception:
            quote_obj = None
    if quote_obj is None:
        return None

    bid = _to_float(_get_field(quote_obj, "bid_price", _get_field(quote_obj, "bp")), 0.0)
    ask = _to_float(_get_field(quote_obj, "ask_price", _get_field(quote_obj, "ap")), 0.0)
    bid_size = _to_float(_get_field(quote_obj, "bid_size", _get_field(quote_obj, "bs")), 0.0)
    ask_size = _to_float(_get_field(quote_obj, "ask_size", _get_field(quote_obj, "as")), 0.0)
    timestamp = _to_iso(_get_field(quote_obj, "timestamp", _get_field(quote_obj, "t")))
    if bid <= 0 and ask <= 0:
        return None
    mid = ((bid + ask) / 2.0) if bid > 0 and ask > 0 else (bid if bid > 0 else ask)
    spread = (ask - bid) if bid > 0 and ask > 0 else None
    return {
        "bid": bid if bid > 0 else None,
        "ask": ask if ask > 0 else None,
        "bid_size": bid_size if bid_size > 0 else None,
        "ask_size": ask_size if ask_size > 0 else None,
        "mid": mid if mid and mid > 0 else None,
        "spread": spread if spread is not None and spread >= 0 else None,
        "timestamp": timestamp,
        "source": "quote",
    }


def _extract_latest_trade(payload: Any, symbol: str) -> dict[str, Any] | None:
    trade_obj = None
    symbol_key = symbol.upper()
    if isinstance(payload, dict):
        trade_obj = payload.get(symbol_key) or payload.get(symbol)
    if trade_obj is None and hasattr(payload, "data"):
        data = getattr(payload, "data", None)
        if isinstance(data, dict):
            trade_obj = data.get(symbol_key) or data.get(symbol)
    if trade_obj is None and hasattr(payload, "get"):
        try:
            trade_obj = payload.get(symbol_key) or payload.get(symbol)
        except Exception:
            trade_obj = None
    if trade_obj is None:
        return None
    price = _to_float(_get_field(trade_obj, "price", _get_field(trade_obj, "p")), 0.0)
    size = _to_float(_get_field(trade_obj, "size", _get_field(trade_obj, "s")), 0.0)
    timestamp = _to_iso(_get_field(trade_obj, "timestamp", _get_field(trade_obj, "t")))
    if price <= 0:
        return None
    return {
        "bid": price,
        "ask": price,
        "bid_size": size if size > 0 else 1.0,
        "ask_size": size if size > 0 else 1.0,
        "mid": price,
        "spread": 0.0,
        "timestamp": timestamp,
        "source": "trade_fallback",
    }


def _normalize_filled_orders_to_trades(
    raw_orders: Any,
    *,
    user_id: str,
    environment: str,
    symbol_strategy_map: Optional[dict[str, str]] = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    now_dt = datetime.now(timezone.utc)
    for order in raw_orders or []:
        status = _normalize_enum_text(_get_field(order, "status", "unknown"), default="unknown")
        if status != "filled":
            continue
        order_id = _get_field(order, "id") or _get_field(order, "client_order_id")
        symbol = str(_get_field(order, "symbol", "")).upper()
        if not order_id or not symbol:
            continue
        qty = float(_get_field(order, "filled_qty", _get_field(order, "qty", 0)) or 0)
        if qty <= 0:
            continue
        price = float(_get_field(order, "filled_avg_price", 0) or 0)
        if price <= 0:
            price = float(_get_field(order, "limit_price", 0) or 0)
        rows.append(
            {
                "fill_id": str(order_id),
                "user_id": user_id,
                "environment": environment,
                "filled_at": _to_datetime(_get_field(order, "filled_at")) or now_dt,
                "symbol": symbol,
                "side": _normalize_enum_text(_get_field(order, "side", "buy"), default="buy"),
                "qty": qty,
                "price": price,
                "strategy_id": (symbol_strategy_map or {}).get(symbol),
                "strategy_name": "Unknown Strategy",
            }
        )
    return rows


def _normalize_alpaca_orders(
    raw_orders: Any,
    *,
    user_id: str,
    environment: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for order in raw_orders or []:
        order_id = _get_field(order, "id") or _get_field(order, "client_order_id")
        symbol = str(_get_field(order, "symbol", "")).upper()
        if not order_id or not symbol:
            continue
        rows.append(
            {
                "order_id": str(order_id),
                "user_id": user_id,
                "environment": environment,
                "symbol": symbol,
                "side": _normalize_enum_text(_get_field(order, "side", ""), default="buy"),
                "qty": float(_get_field(order, "qty", 0) or 0),
                "type": _normalize_enum_text(_get_field(order, "type", "market"), default="market"),
                "status": _normalize_enum_text(_get_field(order, "status", "unknown"), default="unknown"),
                "submitted_at": _to_datetime(_get_field(order, "submitted_at")),
                "filled_at": _to_datetime(_get_field(order, "filled_at")),
                "strategy_id": None,
            }
        )
    return rows


def _normalize_alpaca_positions(
    raw_positions: Any,
    *,
    user_id: str,
    environment: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)
    for pos in raw_positions or []:
        symbol = str(_get_field(pos, "symbol", "")).upper()
        if not symbol:
            continue
        rows.append(
            {
                "user_id": user_id,
                "environment": environment,
                "symbol": symbol,
                "qty": float(_get_field(pos, "qty", 0) or 0),
                "avg_entry_price": float(_get_field(pos, "avg_entry_price", 0) or 0),
                "unrealized_pnl": float(_get_field(pos, "unrealized_pl", 0) or 0),
                "strategy_id": None,
                "updated_at": now,
            }
        )
    return rows


async def _upsert_orders(conn: Any, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    query = """
        INSERT INTO orders (
            order_id, user_id, environment, symbol, side, qty, type, status, submitted_at, filled_at, strategy_id
        ) VALUES (
            $1, $2::uuid, $3, $4, $5, $6, $7, $8, $9::timestamptz, $10::timestamptz, $11
        )
        ON CONFLICT (order_id) DO UPDATE SET
            symbol = EXCLUDED.symbol,
            side = EXCLUDED.side,
            qty = EXCLUDED.qty,
            type = EXCLUDED.type,
            status = EXCLUDED.status,
            submitted_at = COALESCE(EXCLUDED.submitted_at, orders.submitted_at),
            filled_at = COALESCE(EXCLUDED.filled_at, orders.filled_at),
            strategy_id = COALESCE(orders.strategy_id, EXCLUDED.strategy_id)
    """
    params = [
        (
            row["order_id"],
            row["user_id"],
            row["environment"],
            row["symbol"],
            row["side"],
            row["qty"],
            row["type"],
            row["status"],
            row["submitted_at"],
            row["filled_at"],
            row["strategy_id"],
        )
        for row in rows
    ]
    await conn.executemany(query, params)


async def _upsert_trades(conn: Any, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    query = """
        INSERT INTO trades (
            fill_id, user_id, environment, filled_at, symbol, side, qty, price, strategy_id, strategy_name
        ) VALUES (
            $1, $2::uuid, $3, $4::timestamptz, $5, $6, $7, $8, $9, $10
        )
        ON CONFLICT (fill_id) DO UPDATE SET
            filled_at = EXCLUDED.filled_at,
            symbol = EXCLUDED.symbol,
            side = EXCLUDED.side,
            qty = EXCLUDED.qty,
            price = EXCLUDED.price,
            strategy_id = COALESCE(trades.strategy_id, EXCLUDED.strategy_id),
            strategy_name = COALESCE(trades.strategy_name, EXCLUDED.strategy_name)
    """
    params = [
        (
            row["fill_id"],
            row["user_id"],
            row["environment"],
            row["filled_at"],
            row["symbol"],
            row["side"],
            row["qty"],
            row["price"],
            row["strategy_id"],
            row["strategy_name"],
        )
        for row in rows
    ]
    await conn.executemany(query, params)


async def _fetch_order_strategy_map(
    conn: Any,
    *,
    user_id: str,
    environment: str,
    order_ids: list[str],
) -> dict[str, str]:
    if not order_ids:
        return {}
    rows = await conn.fetch(
        """
        SELECT order_id, strategy_id
        FROM orders
        WHERE user_id = $1::uuid
          AND environment = $2
          AND order_id = ANY($3::text[])
        """,
        user_id,
        environment,
        order_ids,
    )
    result: dict[str, str] = {}
    for row in rows:
        order_id = row.get("order_id")
        strategy_id = row.get("strategy_id")
        if order_id and strategy_id:
            result[str(order_id)] = str(strategy_id)
    return result


async def _fetch_strategy_hints(
    conn: Any,
    *,
    user_id: str,
) -> tuple[dict[str, str], str | None, list[str]]:
    rows = await conn.fetch(
        """
        SELECT strategy_id, state, params
        FROM user_strategies
        WHERE user_id = $1::uuid
        """,
        user_id,
    )
    running = [row for row in rows if str(row.get("state", "")).lower() in {"running", "paused"}]
    if not running:
        return {}, None, []

    hints: dict[str, str] = {}
    no_hint_ids: list[str] = []
    for row in running:
        sid = row.get("strategy_id")
        if not sid:
            continue
        sid = str(sid)
        params = row.get("params") or {}
        if not isinstance(params, dict):
            params = {}
        row_hints: set[str] = set()
        for key in ("benchmark_symbol", "symbol"):
            value = params.get(key)
            if isinstance(value, str) and value.strip():
                row_hints.add(value.strip().upper())
        if row_hints:
            for sym in row_hints:
                hints.setdefault(sym, sid)
        else:
            no_hint_ids.append(sid)

    default_sid: str | None = None
    if len(running) == 1:
        only_sid = running[0].get("strategy_id")
        default_sid = str(only_sid) if only_sid else None
    elif len(no_hint_ids) == 1:
        default_sid = no_hint_ids[0]
    running_ids = [str(row.get("strategy_id")) for row in running if row.get("strategy_id")]
    return hints, default_sid, running_ids


def _pick_strategy_for_symbol(symbol: str, running_ids: list[str]) -> str | None:
    if not running_ids:
        return None
    digest = hashlib.sha256(symbol.encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(running_ids)
    return running_ids[idx]


async def _fetch_existing_symbol_strategy_map(
    conn: Any,
    *,
    user_id: str,
    environment: str,
) -> dict[str, str]:
    result: dict[str, str] = {}

    pos_rows = await conn.fetch(
        """
        SELECT symbol, strategy_id
        FROM positions
        WHERE user_id = $1::uuid
          AND environment = $2
          AND strategy_id IS NOT NULL
        """,
        user_id,
        environment,
    )
    for row in pos_rows:
        symbol = row.get("symbol")
        strategy_id = row.get("strategy_id")
        if symbol and strategy_id:
            result[str(symbol).upper()] = str(strategy_id)

    order_rows = await conn.fetch(
        """
        SELECT DISTINCT ON (symbol) symbol, strategy_id
        FROM orders
        WHERE user_id = $1::uuid
          AND environment = $2
          AND strategy_id IS NOT NULL
        ORDER BY symbol, COALESCE(filled_at, submitted_at) DESC NULLS LAST
        """,
        user_id,
        environment,
    )
    for row in order_rows:
        symbol = row.get("symbol")
        strategy_id = row.get("strategy_id")
        if symbol and strategy_id and str(symbol).upper() not in result:
            result[str(symbol).upper()] = str(strategy_id)

    return result


async def _replace_positions(
    conn: Any,
    *,
    user_id: str,
    environment: str,
    rows: list[dict[str, Any]],
) -> None:
    existing = await conn.fetch(
        """
        SELECT symbol, strategy_id
        FROM positions
        WHERE user_id = $1::uuid
          AND environment = $2
        """,
        user_id,
        environment,
    )
    existing_strategy_by_symbol: dict[str, str] = {}
    for row in existing:
        symbol = row.get("symbol")
        strategy_id = row.get("strategy_id")
        if symbol and strategy_id:
            existing_strategy_by_symbol[str(symbol).upper()] = str(strategy_id)

    for row in rows:
        symbol = str(row.get("symbol", "")).upper()
        if symbol and not row.get("strategy_id") and symbol in existing_strategy_by_symbol:
            row["strategy_id"] = existing_strategy_by_symbol[symbol]

    order_symbol_strategy = await conn.fetch(
        """
        SELECT DISTINCT ON (symbol) symbol, strategy_id
        FROM orders
        WHERE user_id = $1::uuid
          AND environment = $2
          AND strategy_id IS NOT NULL
        ORDER BY symbol, COALESCE(filled_at, submitted_at) DESC NULLS LAST
        """,
        user_id,
        environment,
    )
    order_strategy_by_symbol: dict[str, str] = {}
    for row in order_symbol_strategy:
        symbol = row.get("symbol")
        strategy_id = row.get("strategy_id")
        if symbol and strategy_id:
            order_strategy_by_symbol[str(symbol).upper()] = str(strategy_id)

    strategy_hints, default_strategy_id, running_strategy_ids = await _fetch_strategy_hints(
        conn, user_id=user_id
    )
    for row in rows:
        symbol = str(row.get("symbol", "")).upper()
        if not symbol or row.get("strategy_id"):
            continue
        row["strategy_id"] = (
            order_strategy_by_symbol.get(symbol)
            or strategy_hints.get(symbol)
            or default_strategy_id
            or _pick_strategy_for_symbol(symbol, running_strategy_ids)
        )

    async with conn.transaction():
        await conn.execute(
            "DELETE FROM positions WHERE user_id = $1::uuid AND environment = $2",
            user_id,
            environment,
        )
        if not rows:
            return
        query = """
            INSERT INTO positions (
                user_id, environment, symbol, qty, avg_entry_price, unrealized_pnl, strategy_id, updated_at
            ) VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8::timestamptz)
        """
        params = [
            (
                row["user_id"],
                row["environment"],
                row["symbol"],
                row["qty"],
                row["avg_entry_price"],
                row["unrealized_pnl"],
                row["strategy_id"],
                row["updated_at"],
            )
            for row in rows
        ]
        await conn.executemany(query, params)


async def _sync_alpaca_snapshot(
    conn: Any,
    *,
    env: str,
    user_id: str,
    sync_orders: bool = False,
    sync_positions: bool = False,
) -> None:
    if not (sync_orders or sync_positions):
        return
    settings = get_settings()
    if not settings.alpaca_api_key or not settings.alpaca_secret_key:
        return

    cache_hits: list[str] = []
    if sync_orders:
        order_key = f"trading:orders:{env}:{user_id}"
        if SYNC_CACHE.get(order_key) is not None:
            cache_hits.append("orders")
            sync_orders = False
    if sync_positions:
        pos_key = f"trading:positions:{env}:{user_id}"
        if SYNC_CACHE.get(pos_key) is not None:
            cache_hits.append("positions")
            sync_positions = False
    if not (sync_orders or sync_positions):
        return

    client = AlpacaClient(settings, env)
    try:
        if sync_orders:
            raw_orders = await anyio.to_thread.run_sync(lambda: client.get_orders(status="all", limit=500))
            if raw_orders is not None:
                order_rows = _normalize_alpaca_orders(raw_orders, user_id=user_id, environment=env)
                order_ids = [row["order_id"] for row in order_rows]
                existing_order_strategy_map = await _fetch_order_strategy_map(
                    conn,
                    user_id=user_id,
                    environment=env,
                    order_ids=order_ids,
                )
                existing_symbol_strategy_map = await _fetch_existing_symbol_strategy_map(
                    conn,
                    user_id=user_id,
                    environment=env,
                )
                strategy_hints, default_strategy_id, running_strategy_ids = await _fetch_strategy_hints(
                    conn,
                    user_id=user_id,
                )
                for row in order_rows:
                    symbol = str(row.get("symbol", "")).upper()
                    sid = (
                        existing_order_strategy_map.get(row["order_id"])
                        or existing_symbol_strategy_map.get(symbol)
                        or strategy_hints.get(symbol)
                        or default_strategy_id
                        or _pick_strategy_for_symbol(symbol, running_strategy_ids)
                    )
                    if sid:
                        row["strategy_id"] = sid
                        if symbol:
                            existing_symbol_strategy_map.setdefault(symbol, sid)
                await _upsert_orders(conn, order_rows)
                trade_rows = _normalize_filled_orders_to_trades(
                    raw_orders,
                    user_id=user_id,
                    environment=env,
                    symbol_strategy_map=existing_symbol_strategy_map,
                )
                await _upsert_trades(conn, trade_rows)
                SYNC_CACHE.set(f"trading:orders:{env}:{user_id}", True, ttl=ORDER_SYNC_TTL)
                logger.info(
                    "trading.sync orders env=%s count=%s trades=%s",
                    env,
                    len(order_rows),
                    len(trade_rows),
                )
            else:
                logger.warning("trading.sync orders skipped env=%s reason=alpaca_none", env)

        if sync_positions:
            raw_positions = await anyio.to_thread.run_sync(client.get_positions)
            if raw_positions is not None:
                position_rows = _normalize_alpaca_positions(
                    raw_positions,
                    user_id=user_id,
                    environment=env,
                )
                await _replace_positions(
                    conn,
                    user_id=user_id,
                    environment=env,
                    rows=position_rows,
                )
                SYNC_CACHE.set(f"trading:positions:{env}:{user_id}", True, ttl=POSITION_SYNC_TTL)
                logger.info("trading.sync positions env=%s count=%s", env, len(position_rows))
            else:
                logger.warning("trading.sync positions skipped env=%s reason=alpaca_none", env)
    except Exception as exc:
        logger.warning(
            "trading.sync failed env=%s sync_orders=%s sync_positions=%s cache_hits=%s error=%s",
            env,
            sync_orders,
            sync_positions,
            ",".join(cache_hits) if cache_hits else "-",
            exc,
        )


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


def _estimate_days(timeframe: str, limit: int) -> int:
    value = timeframe.strip().lower()
    match = re.match(r"(\d+)", value)
    amount = int(match.group(1)) if match else 1
    if "min" in value:
        return max(1, ceil(limit * amount / 60 / 24))
    if "hour" in value:
        return max(1, ceil(limit * amount / 24))
    if "day" in value:
        return max(1, limit)
    return max(1, limit)


def _timeframe_hours(value: str) -> int | None:
    value = value.strip().lower()
    if "hour" not in value:
        return None
    match = re.match(r"(\d+)", value)
    amount = int(match.group(1)) if match else 1
    return max(1, amount)


def _upsample_daily_to_hours(daily: list[dict], hour_step: int) -> list[dict]:
    if not daily:
        return []
    expanded: list[dict] = []
    for bar in daily:
        base_time = str(bar.get("time", ""))[:10]
        for hour in range(0, 24, hour_step):
            ts = f"{base_time}T{hour:02d}:00:00Z"
            expanded.append(
                {
                    "time": ts,
                    "open": bar.get("open", 0),
                    "high": bar.get("high", 0),
                    "low": bar.get("low", 0),
                    "close": bar.get("close", 0),
                    "volume": bar.get("volume", 0),
                }
            )
    return expanded


def _timeframe_minutes(value: str) -> int | None:
    value = value.strip().lower()
    if "min" not in value:
        return None
    match = re.match(r"(\d+)", value)
    amount = int(match.group(1)) if match else 1
    return max(1, amount)


def _upsample_daily_to_minutes(daily: list[dict], minute_step: int) -> list[dict]:
    if not daily:
        return []
    expanded: list[dict] = []
    for bar in daily:
        base_time = str(bar.get("time", ""))[:10]
        # 09:30~16:00 regular session (390 minutes)
        for offset in range(0, 390, minute_step):
            total = 30 + offset
            hour = 9 + (total // 60)
            minute = total % 60
            ts = f"{base_time}T{hour:02d}:{minute:02d}:00Z"
            expanded.append(
                {
                    "time": ts,
                    "open": bar.get("open", 0),
                    "high": bar.get("high", 0),
                    "low": bar.get("low", 0),
                    "close": bar.get("close", 0),
                    "volume": bar.get("volume", 0),
                }
            )
    return expanded


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
    await _sync_alpaca_snapshot(
        conn,
        env=env,
        user_id=resolved_user_id,
        sync_orders=True,
    )
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
    await _sync_alpaca_snapshot(
        conn,
        env=env,
        user_id=resolved_user_id,
        sync_orders=True,
    )
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
    await _sync_alpaca_snapshot(
        conn,
        env=env,
        user_id=resolved_user_id,
        sync_positions=True,
    )
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


@router.get("/quote", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    feed: Optional[str] = Query(default=None),
):
    settings = get_settings()
    if not settings.alpaca_api_key or not settings.alpaca_secret_key:
        raise APIError("CONFIG_ERROR", "Alpaca keys missing", status_code=400)
    if (
        StockHistoricalDataClient is None
        or StockLatestQuoteRequest is None
        or StockLatestTradeRequest is None
    ):
        raise APIError("SERVER_ERROR", "alpaca data client unavailable", status_code=500)

    data_feed = feed or settings.alpaca_data_feed
    parsed_feed = _parse_data_feed(data_feed)
    client = StockHistoricalDataClient(
        settings.alpaca_api_key,
        settings.alpaca_secret_key,
    )

    quote_payload = await anyio.to_thread.run_sync(
        lambda: client.get_stock_latest_quote(
            StockLatestQuoteRequest(
                symbol_or_symbols=[symbol],
                feed=parsed_feed,
            )
        )
    )
    quote = _extract_latest_quote(quote_payload, symbol)
    if quote is not None:
        logger.info(
            "alpaca.quote symbol=%s feed=%s bid=%s ask=%s source=quote",
            symbol,
            data_feed,
            quote["bid"],
            quote["ask"],
        )
        return {
            "symbol": symbol.upper(),
            "feed": data_feed,
            **quote,
        }

    trade_payload = await anyio.to_thread.run_sync(
        lambda: client.get_stock_latest_trade(
            StockLatestTradeRequest(
                symbol_or_symbols=[symbol],
                feed=parsed_feed,
            )
        )
    )
    trade_quote = _extract_latest_trade(trade_payload, symbol)
    if trade_quote is not None:
        logger.info(
            "alpaca.quote symbol=%s feed=%s price=%s source=trade_fallback",
            symbol,
            data_feed,
            trade_quote["mid"],
        )
        return {
            "symbol": symbol.upper(),
            "feed": data_feed,
            **trade_quote,
        }

    # Market-closed fallback: use the latest daily close as a synthetic 1-level quote.
    bars_payload = await anyio.to_thread.run_sync(
        lambda: client.get_stock_bars(
            StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Day,
                limit=5,
                feed=parsed_feed,
                adjustment=Adjustment.ALL if Adjustment is not None else None,
            )
        )
    )
    raw_bars = []
    if bars_payload is not None and hasattr(bars_payload, "data"):
        raw_bars = bars_payload.data.get(symbol, []) or bars_payload.data.get(symbol.upper(), [])
    if raw_bars:
        last_bar = raw_bars[-1]
        close_price = _to_float(_bar_attr(last_bar, "c", "close"), 0.0)
        close_ts = _to_iso(_bar_attr(last_bar, "t", "timestamp", "time"))
        if close_price > 0:
            logger.info(
                "alpaca.quote symbol=%s feed=%s close=%s source=close_fallback",
                symbol,
                data_feed,
                close_price,
            )
            return {
                "symbol": symbol.upper(),
                "feed": data_feed,
                "bid": close_price,
                "ask": close_price,
                "bid_size": 1.0,
                "ask_size": 1.0,
                "mid": close_price,
                "spread": 0.0,
                "timestamp": close_ts,
                "source": "close_fallback",
            }

    logger.warning("alpaca.quote symbol=%s feed=%s source=none", symbol, data_feed)
    return {
        "symbol": symbol.upper(),
        "feed": data_feed,
        "bid": None,
        "ask": None,
        "bid_size": None,
        "ask_size": None,
        "mid": None,
        "spread": None,
        "timestamp": None,
        "source": "none",
    }


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
            adjustment=Adjustment.ALL if Adjustment is not None else None,
        )
        return client.get_stock_bars(request)

    estimated_days = _estimate_days(timeframe, limit)
    if "min" in timeframe.lower():
        estimated_days = max(7, estimated_days * 3)
    elif "hour" in timeframe.lower():
        estimated_days = max(30, estimated_days * 2)
    elif "day" in timeframe.lower():
        estimated_days = max(365, estimated_days)

    start_dt = datetime.now(timezone.utc) - timedelta(days=estimated_days)
    barset = await anyio.to_thread.run_sync(lambda: _fetch(start_dt))
    raw_bars = []
    if barset is not None:
        raw_bars = barset.data.get(symbol, [])

    if not raw_bars:
        fallback_days = max(estimated_days * 2, 14)
        if "day" in timeframe.lower():
            fallback_days = max(fallback_days, 365)
        fallback_start = datetime.now(timezone.utc) - timedelta(days=fallback_days)
        logger.info(
            "alpaca.bars fallback start=%s timeframe=%s feed=%s",
            fallback_start.isoformat(),
            timeframe,
            data_feed,
        )
        barset = await anyio.to_thread.run_sync(lambda: _fetch(fallback_start))
        if barset is not None:
            raw_bars = barset.data.get(symbol, [])

    min_required = max(5, int(limit * 0.2))
    # Minute bars should stay vendor-accurate; avoid synthetic DB fallback that can
    # diverge from Alpaca live prices.
    should_fallback_market_prices = len(raw_bars) < min_required and "min" not in timeframe.lower()
    if should_fallback_market_prices:
        end_date = date.today()
        days = _estimate_days(timeframe, limit)
        if "min" in timeframe.lower():
            days = max(days, 7)
        if "hour" in timeframe.lower():
            days = max(days, 30)
        start_date = end_date - timedelta(days=days)
        series = load_price_series(
            [symbol],
            start_date.isoformat(),
            end_date.isoformat(),
            "adj_close",
        ).get(symbol, {})
        if series:
            daily_bars: list[dict] = []
            for day, value in sorted(series.items()):
                daily_bars.append(
                    {
                        "time": f"{day}T00:00:00Z",
                        "open": value,
                        "high": value,
                        "low": value,
                        "close": value,
                        "volume": 0.0,
                    }
                )
            minute_step = _timeframe_minutes(timeframe)
            hour_step = _timeframe_hours(timeframe)
            if minute_step:
                upsampled = _upsample_daily_to_minutes(daily_bars, minute_step)
                if upsampled:
                    raw_bars = upsampled[-limit:]
            elif hour_step:
                upsampled = _upsample_daily_to_hours(daily_bars, hour_step)
                if upsampled:
                    raw_bars = upsampled[-limit:]
            else:
                raw_bars = daily_bars[-limit:]
            logger.info(
                "alpaca.bars fallback_market_prices symbol=%s timeframe=%s count=%s",
                symbol,
                timeframe,
                len(raw_bars),
            )

    items = []
    for bar in raw_bars:
        if isinstance(bar, dict) and "time" in bar:
            items.append(
                {
                    "time": str(bar.get("time")),
                    "open": float(bar.get("open", 0)),
                    "high": float(bar.get("high", 0)),
                    "low": float(bar.get("low", 0)),
                    "close": float(bar.get("close", 0)),
                    "volume": float(bar.get("volume", 0)),
                }
            )
            continue
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
