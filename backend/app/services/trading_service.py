from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import asyncpg

from app.core.config import Settings
from app.core.errors import APIError
from app.storage.user_settings_repo import UserSettingsRepository
from engine.errors import BrokerConnectionError, OrderRejectedError


class TradingService:
    """Thin web-layer service for trading settings. Maps engine errors to HTTP errors."""

    def __init__(self, settings: Settings, user_id: str) -> None:
        self._user_id = user_id
        self._repo = UserSettingsRepository(settings)

    def set_mode(self, environment: str, allow_live: bool) -> dict:
        if environment == "live" and not allow_live:
            raise APIError("LIVE_TRADING_DISABLED", "Live trading is disabled", "Set ALLOW_LIVE_TRADING=true to enable", status_code=403)
        try:
            self._repo.update(self._user_id, {"environment": environment})
        except BrokerConnectionError as exc:
            raise APIError("BROKER_CONNECTION_ERROR", "Broker connection failed", str(exc), status_code=503) from exc
        return {"environment": environment}

    def set_kill_switch(self, enabled: bool, reason: str | None) -> dict:
        try:
            self._repo.update(self._user_id, {"kill_switch": enabled, "kill_switch_reason": reason})
        except OrderRejectedError as exc:
            raise APIError("ORDER_REJECTED", str(exc), status_code=422) from exc
        return {"enabled": enabled}


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _order_row_to_dict(row: asyncpg.Record) -> Dict[str, Any]:
    strategy_id = row.get("strategy_id")
    strategy_name = row.get("strategy_name")
    return {
        "order_id": row["order_id"],
        "submitted_at": _to_iso(row.get("submitted_at")),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "type": row.get("type"),
        "qty": _to_float(row.get("qty")),
        "status": row.get("status"),
        "filled_at": _to_iso(row.get("filled_at")),
        "strategy_id": strategy_id,
        "strategy": (
            {
                "id": str(strategy_id),
                "name": str(strategy_name) if strategy_name else str(strategy_id),
            }
            if strategy_id
            else None
        ),
    }


def _position_row_to_dict(row: asyncpg.Record) -> Dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "qty": _to_float(row.get("qty")),
        "avg_price": _to_float(row.get("avg_entry_price")),
        "unrealized_pnl": _to_float(row.get("unrealized_pnl")),
        "strategy_id": row.get("strategy_id"),
        "updated_at": _to_iso(row.get("updated_at")),
    }


async def fetch_orders(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    environment: str,
    scope: str,
    limit: int,
) -> List[Dict[str, Any]]:
    where = ""
    params = [user_id, environment, limit]
    status_norm = r"regexp_replace(lower(trim(coalesce(o.status, ''))), '^.*\.', '')"
    if scope == "open":
        where = (
            f"AND {status_norm} NOT IN "
            "('filled','canceled','cancelled','rejected','expired')"
        )
    elif scope == "filled":
        where = f"AND {status_norm} = 'filled'"

    query = f"""
        SELECT
          o.order_id, o.submitted_at, o.symbol, o.side, o.type, o.qty, o.status, o.filled_at, o.strategy_id,
          us.name AS strategy_name
        FROM orders o
        LEFT JOIN user_strategies us
          ON us.strategy_id = o.strategy_id
         AND us.user_id = o.user_id
        WHERE o.user_id = $1
          AND o.environment = $2
          {where}
        ORDER BY o.submitted_at DESC NULLS LAST
        LIMIT $3
    """
    rows = await conn.fetch(query, *params)
    return [_order_row_to_dict(row) for row in rows]


async def fetch_order_by_id(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    environment: str,
    order_id: str,
) -> Dict[str, Any] | None:
    query = """
        SELECT
          o.order_id, o.submitted_at, o.symbol, o.side, o.type, o.qty, o.status, o.filled_at, o.strategy_id,
          us.name AS strategy_name
        FROM orders o
        LEFT JOIN user_strategies us
          ON us.strategy_id = o.strategy_id
         AND us.user_id = o.user_id
        WHERE o.user_id = $1
          AND o.environment = $2
          AND o.order_id = $3
        LIMIT 1
    """
    row = await conn.fetchrow(query, user_id, environment, order_id)
    if not row:
        return None
    return _order_row_to_dict(row)


async def fetch_positions(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    environment: str,
) -> List[Dict[str, Any]]:
    query = """
        SELECT symbol, qty, avg_entry_price, unrealized_pnl, strategy_id, updated_at
        FROM positions
        WHERE user_id = $1
          AND environment = $2
        ORDER BY symbol ASC
    """
    rows = await conn.fetch(query, user_id, environment)
    return [_position_row_to_dict(row) for row in rows]


async def fetch_last_fill(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    symbol: str,
) -> Dict[str, Any] | None:
    query = """
        SELECT fill_id, filled_at, symbol, side, qty, price
        FROM trades
        WHERE user_id = $1
          AND symbol = $2
        ORDER BY filled_at DESC NULLS LAST
        LIMIT 1
    """
    row = await conn.fetchrow(query, user_id, symbol)
    if not row:
        return None
    return {
        "symbol": row.get("symbol"),
        "price": _to_float(row.get("price")),
        "filled_at": _to_iso(row.get("filled_at")),
    }
