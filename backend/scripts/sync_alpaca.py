from __future__ import annotations

import argparse
import hashlib
import pathlib
import sys
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.alpaca.client import AlpacaClient
from app.core.config import get_settings
from app.core.time import now_kst
from app.core.user import resolve_user_id
from app.storage.my_strategies_repo import MyStrategiesRepository
from app.storage.orders_repo import OrdersRepository
from app.storage.positions_repo import PositionsRepository
from app.storage.trades_repo import TradesRepository


def _get_field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _normalize_enum_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    if "." in text:
        text = text.split(".")[-1]
    return text.lower()


def _normalize_orders(
    raw_orders: Any,
    *,
    user_id: str,
    environment: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
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
                "qty": _to_float(_get_field(order, "qty", 0)),
                "type": _normalize_enum_text(_get_field(order, "type", "market"), default="market"),
                "status": _normalize_enum_text(_get_field(order, "status", "unknown"), default="unknown"),
                "submitted_at": _to_iso(_get_field(order, "submitted_at")),
                "filled_at": _to_iso(_get_field(order, "filled_at")),
                "strategy_id": None,
            }
        )
    return rows


def _normalize_filled_orders_to_trades(
    raw_orders: Any,
    *,
    user_id: str,
    environment: str,
    symbol_strategy_map: Dict[str, str] | None = None,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    now = now_kst().isoformat()
    for order in raw_orders or []:
        status = _normalize_enum_text(_get_field(order, "status", "unknown"), default="unknown")
        if status != "filled":
            continue
        order_id = _get_field(order, "id") or _get_field(order, "client_order_id")
        symbol = str(_get_field(order, "symbol", "")).upper()
        if not order_id or not symbol:
            continue
        qty = _to_float(_get_field(order, "filled_qty", _get_field(order, "qty", 0)))
        if qty <= 0:
            continue
        price = _to_float(_get_field(order, "filled_avg_price", 0))
        if price <= 0:
            price = _to_float(_get_field(order, "limit_price", 0))
        rows.append(
            {
                "fill_id": str(order_id),
                "user_id": user_id,
                "environment": environment,
                "filled_at": _to_iso(_get_field(order, "filled_at")) or now,
                "symbol": symbol,
                "side": _normalize_enum_text(_get_field(order, "side", "buy"), default="buy"),
                "qty": qty,
                "price": price,
                "strategy_id": (symbol_strategy_map or {}).get(symbol),
                "strategy_name": "Unknown Strategy",
            }
        )
    return rows


def _build_strategy_hints(settings, user_id: str) -> tuple[Dict[str, str], str | None, List[str]]:
    repo = MyStrategiesRepository(settings)
    try:
        rows = repo.list(user_id, {}, "updated_at", "desc", 1000, None)
    except Exception:
        return {}, None, []
    running = [row for row in rows if str(row.get("state", "")).lower() in {"running", "paused"}]
    if not running:
        return {}, None, []

    hints: Dict[str, str] = {}
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


def _pick_strategy_for_symbol(symbol: str, running_ids: List[str]) -> str | None:
    if not running_ids:
        return None
    digest = hashlib.sha256(symbol.encode("utf-8")).hexdigest()
    idx = int(digest[:8], 16) % len(running_ids)
    return running_ids[idx]


def _normalize_positions(
    raw_positions: Any,
    *,
    user_id: str,
    environment: str,
) -> List[Dict[str, Any]]:
    now = now_kst().isoformat()
    rows: List[Dict[str, Any]] = []
    for pos in raw_positions or []:
        symbol = str(_get_field(pos, "symbol", "")).upper()
        if not symbol:
            continue
        rows.append(
            {
                "user_id": user_id,
                "environment": environment,
                "symbol": symbol,
                "qty": _to_float(_get_field(pos, "qty", 0)),
                "avg_entry_price": _to_float(_get_field(pos, "avg_entry_price", 0)),
                "unrealized_pnl": _to_float(_get_field(pos, "unrealized_pl", 0)),
                "strategy_id": None,
                "updated_at": now,
            }
        )
    return rows


def main() -> None:
    env_path = pathlib.Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    parser = argparse.ArgumentParser(description="Sync Alpaca orders/positions into DB")
    parser.add_argument("--env", default="paper", choices=["paper", "live"])
    parser.add_argument("--user-id", default=None)
    parser.add_argument("--orders", action="store_true", help="Sync orders")
    parser.add_argument("--positions", action="store_true", help="Sync positions")
    parser.add_argument("--status", default="all", help="Alpaca order status filter")
    parser.add_argument("--limit", type=int, default=200, help="Orders limit")
    args = parser.parse_args()

    settings = get_settings()
    user_id = resolve_user_id(settings, args.user_id)
    client = AlpacaClient(settings, args.env)
    strategy_hints, default_strategy_id, running_strategy_ids = _build_strategy_hints(settings, user_id)

    existing_orders = OrdersRepository(settings).list_recent(user_id, args.env, limit=2000)
    existing_positions = PositionsRepository(settings).list(user_id, args.env, limit=2000)
    existing_symbol_strategy_map: Dict[str, str] = {}
    for row in existing_orders:
        symbol = str(row.get("symbol", "")).upper()
        sid = row.get("strategy_id")
        if symbol and sid and symbol not in existing_symbol_strategy_map:
            existing_symbol_strategy_map[symbol] = str(sid)
    for row in existing_positions:
        symbol = str(row.get("symbol", "")).upper()
        sid = row.get("strategy_id")
        if symbol and sid and symbol not in existing_symbol_strategy_map:
            existing_symbol_strategy_map[symbol] = str(sid)

    raw_orders = client.get_orders(status=args.status, limit=args.limit) if args.orders else []
    raw_positions = client.get_positions() if args.positions else []
    order_rows = _normalize_orders(raw_orders or [], user_id=user_id, environment=args.env)
    position_rows = _normalize_positions(raw_positions or [], user_id=user_id, environment=args.env)

    symbols = {
        str(row.get("symbol", "")).upper()
        for row in order_rows + position_rows
        if row.get("symbol")
    }
    symbol_strategy_map: Dict[str, str] = {}
    for symbol in sorted(symbols):
        sid = (
            existing_symbol_strategy_map.get(symbol)
            or strategy_hints.get(symbol)
            or default_strategy_id
            or _pick_strategy_for_symbol(symbol, running_strategy_ids)
        )
        if sid:
            symbol_strategy_map[symbol] = sid

    if args.orders:
        for row in order_rows:
            symbol = str(row.get("symbol", "")).upper()
            if symbol and symbol in symbol_strategy_map:
                row["strategy_id"] = symbol_strategy_map[symbol]
        OrdersRepository(settings).upsert_many(order_rows)
        trade_rows = _normalize_filled_orders_to_trades(
            raw_orders or [],
            user_id=user_id,
            environment=args.env,
            symbol_strategy_map=symbol_strategy_map,
        )
        TradesRepository(settings).upsert_many(trade_rows)
        print(f"synced orders: {len(order_rows)}")
        print(f"synced trades: {len(trade_rows)}")

    if args.positions:
        for row in position_rows:
            symbol = str(row.get("symbol", "")).upper()
            if symbol and symbol in symbol_strategy_map:
                row["strategy_id"] = symbol_strategy_map[symbol]
        PositionsRepository(settings).replace_all(user_id, args.env, position_rows)
        print(f"synced positions: {len(position_rows)}")

    if not args.orders and not args.positions:
        print("no action: pass --orders and/or --positions")


if __name__ == "__main__":
    main()
