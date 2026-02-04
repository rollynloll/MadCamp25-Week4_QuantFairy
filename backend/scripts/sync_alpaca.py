from __future__ import annotations

import argparse
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
                "strategy_id": None,
                "strategy_name": "Unknown Strategy",
            }
        )
    return rows


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

    if args.orders:
        raw_orders = client.get_orders(status=args.status, limit=args.limit) or []
        order_rows = _normalize_orders(raw_orders, user_id=user_id, environment=args.env)
        OrdersRepository(settings).upsert_many(order_rows)
        trade_rows = _normalize_filled_orders_to_trades(raw_orders, user_id=user_id, environment=args.env)
        TradesRepository(settings).upsert_many(trade_rows)
        print(f"synced orders: {len(order_rows)}")
        print(f"synced trades: {len(trade_rows)}")

    if args.positions:
        raw_positions = client.get_positions() or []
        position_rows = _normalize_positions(raw_positions, user_id=user_id, environment=args.env)
        PositionsRepository(settings).replace_all(user_id, args.env, position_rows)
        print(f"synced positions: {len(position_rows)}")

    if not args.orders and not args.positions:
        print("no action: pass --orders and/or --positions")


if __name__ == "__main__":
    main()
