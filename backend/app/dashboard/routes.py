from __future__ import annotations

import hashlib
import logging
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Header, Query

from app.alpaca.client import AlpacaClient
from app.core.config import get_settings
from app.core.time import now_kst, parse_datetime, plus_hours
from app.core.user import resolve_user_id
from app.schemas.dashboard import DashboardResponse
from app.storage.alerts_repo import AlertsRepository
from app.storage.bot_runs_repo import BotRunsRepository
from app.storage.portfolio_repo import PortfolioRepository
from app.storage.positions_repo import PositionsRepository
from app.storage.strategies_repo import StrategiesRepository
from app.storage.trades_repo import TradesRepository
from app.storage.user_accounts_repo import UserAccountsRepository
from app.storage.user_settings_repo import UserSettingsRepository
from app.storage.orders_repo import OrdersRepository


router = APIRouter()
logger = logging.getLogger("quantfairy.dashboard")


RangeLiteral = Literal["1D", "1W", "1M", "3M", "1Y", "ALL"]


def _range_days(range_value: str) -> int:
    return {
        "1D": 1,
        "1W": 7,
        "1M": 30,
        "3M": 90,
        "1Y": 365,
        "ALL": 730,
    }.get(range_value, 30)


def _range_to_alpaca_period(range_value: str) -> str:
    return {
        "1D": "1D",
        "1W": "1W",
        "1M": "1M",
        "3M": "3M",
        "1Y": "1A",
        "ALL": "ALL",
    }.get(range_value, "1M")


def _range_to_alpaca_timeframe(range_value: str) -> str:
    # Intraday detail for 1D chart; keep daily bars for longer windows.
    if range_value == "1D":
        return "1Min"
    return "1D"


def _equity_curve_fallback(equity_value: float) -> List[dict]:
    return [{"t": now_kst(), "equity": equity_value}]


def _max_drawdown_pct(equity_curve: List[dict]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]["equity"]
    max_drawdown = 0.0
    for point in equity_curve:
        equity = point["equity"]
        if equity > peak:
            peak = equity
        if peak:
            drawdown = (equity - peak) / peak * 100
            if drawdown < max_drawdown:
                max_drawdown = drawdown
    return max_drawdown


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


def _to_equity_timestamp_iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 10_000_000_000:
            ts = ts / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
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


def _history_to_equity_points(history: Any) -> List[dict]:
    timestamps = _get_field(history, "timestamp") or _get_field(history, "timestamps")
    equity = _get_field(history, "equity")
    if not timestamps or not equity:
        return []
    points: List[dict] = []
    for ts, eq in zip(timestamps, equity):
        points.append({"t": _to_equity_timestamp_iso(ts), "equity": _to_float(eq, 0.0)})
    return _sanitize_equity_curve(points)


def _sanitize_equity_curve(points: List[dict]) -> List[dict]:
    cleaned: List[dict] = []
    for point in sorted(points, key=lambda item: str(item.get("t", ""))):
        ts = point.get("t")
        if ts is None:
            continue
        equity = _to_float(point.get("equity", 0.0), 0.0)
        if not math.isfinite(equity):
            continue
        cleaned.append({"t": str(ts), "equity": equity})

    # Drop zero placeholder points when valid positive points exist.
    if any(item["equity"] > 0 for item in cleaned):
        cleaned = [item for item in cleaned if item["equity"] > 0]
    return cleaned


def _downsample_equity_to_hourly(points: List[dict]) -> List[dict]:
    if not points:
        return []
    bucketed: Dict[str, dict] = {}
    for point in points:
        ts = point.get("t")
        if ts is None:
            continue
        try:
            dt = parse_datetime(str(ts))
        except Exception:
            continue
        key = dt.replace(minute=0, second=0, microsecond=0).isoformat()
        bucketed[key] = point
    downsampled = sorted(bucketed.values(), key=lambda item: str(item.get("t", "")))
    return _sanitize_equity_curve(downsampled)


def _ensure_latest_equity_point(
    equity_curve: List[dict],
    latest_equity: float,
    *,
    now_dt: datetime | None = None,
) -> tuple[List[dict], bool]:
    if latest_equity <= 0:
        return equity_curve, False
    now_dt = now_dt or now_kst()
    now_iso = now_dt.isoformat()
    if not equity_curve:
        return [{"t": now_iso, "equity": latest_equity}], True

    last_point = equity_curve[-1]
    last_equity = _to_float(last_point.get("equity"), latest_equity)
    last_ts = last_point.get("t")
    last_dt: datetime | None = None
    if last_ts is not None:
        try:
            last_dt = parse_datetime(str(last_ts))
        except Exception:
            last_dt = None

    # Reflect latest account equity when history lags by day or value changed intraday.
    should_append = abs(last_equity - latest_equity) > 0.01
    if last_dt is not None and last_dt.date() < now_dt.date():
        should_append = True
    if not should_append:
        return equity_curve, False
    return [*equity_curve, {"t": now_iso, "equity": latest_equity}], True


def _normalize_orders(
    raw_orders: Any,
    *,
    user_id: str,
    environment: str,
) -> List[dict]:
    rows: List[dict] = []
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
) -> List[dict]:
    rows: List[dict] = []
    now_iso = now_kst().isoformat()
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
                "filled_at": _to_iso(_get_field(order, "filled_at")) or now_iso,
                "symbol": symbol,
                "side": _normalize_enum_text(_get_field(order, "side", "buy"), default="buy"),
                "qty": qty,
                "price": price,
                "strategy_id": (symbol_strategy_map or {}).get(symbol),
                "strategy_name": "Unknown Strategy",
            }
        )
    return rows


def _build_strategy_hints(strategies: List[dict]) -> tuple[Dict[str, str], str | None, List[str]]:
    running = [row for row in strategies if str(row.get("state", "")).lower() in {"running", "paused"}]
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
) -> List[dict]:
    now = now_kst().isoformat()
    rows: List[dict] = []
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


def _compute_strategy_runtime_metrics(position_rows: List[dict]) -> Dict[str, Dict[str, float | int]]:
    metrics: Dict[str, Dict[str, float | int]] = {}
    for row in position_rows:
        strategy_id = row.get("strategy_id") or row.get("user_strategy_id")
        if not strategy_id:
            continue
        strategy_key = str(strategy_id)
        qty = abs(_to_float(row.get("qty", 0.0)))
        avg_entry_price = _to_float(row.get("avg_entry_price", 0.0))
        unrealized_pnl = _to_float(row.get("unrealized_pnl", row.get("unrealized_pl", 0.0)))
        exposure_value = abs(qty * avg_entry_price)
        item = metrics.setdefault(
            strategy_key,
            {
                "positions_count": 0,
                "pnl_today_value": 0.0,
                "pnl_today_pct": 0.0,
                "managed_value": 0.0,
            },
        )
        if qty > 0:
            item["positions_count"] = int(item["positions_count"]) + 1
        item["pnl_today_value"] = float(item["pnl_today_value"]) + unrealized_pnl
        item["managed_value"] = float(item["managed_value"]) + exposure_value

    for item in metrics.values():
        managed_value = float(item.get("managed_value", 0.0) or 0.0)
        pnl_value = float(item.get("pnl_today_value", 0.0) or 0.0)
        item["pnl_today_pct"] = (pnl_value / managed_value * 100.0) if managed_value > 0 else 0.0
    return metrics

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    range: RangeLiteral = Query(default="1M", description="Time range"),
    user_id: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    settings = get_settings()
    resolved_user_id = resolve_user_id(settings, x_user_id or user_id)

    logger.info("GET /api/v1/dashboard range=%s user_id=%s", range, resolved_user_id)
    print("PRINT: hello world ", resolved_user_id)

    settings_repo = UserSettingsRepository(settings)
    strategies_repo = StrategiesRepository(settings)
    trades_repo = TradesRepository(settings)
    alerts_repo = AlertsRepository(settings)
    accounts_repo = UserAccountsRepository(settings)
    portfolio_repo = PortfolioRepository(settings)
    positions_repo = PositionsRepository(settings)
    bot_runs_repo = BotRunsRepository(settings)
    orders_repo = OrdersRepository(settings)

    user_settings = settings_repo.get_or_create(resolved_user_id)
    environment = user_settings.get("environment", "paper")
    kill_switch = bool(user_settings.get("kill_switch", False))

    alpaca = AlpacaClient(settings, environment)
    account_result = alpaca.get_account()
    broker_state = "connected" if account_result.account else "down"
    if account_result.account:
        try:
            strategy_rows = strategies_repo.list(resolved_user_id)
            strategy_hints, default_strategy_id, running_strategy_ids = _build_strategy_hints(
                strategy_rows
            )
            existing_orders = orders_repo.list_recent(
                resolved_user_id,
                environment,
                limit=1000,
            )
            existing_positions = positions_repo.list(resolved_user_id, environment, limit=1000)
            existing_symbol_strategy_map: Dict[str, str] = {
                str(row.get("symbol")).upper(): str(row.get("strategy_id"))
                for row in existing_orders
                if row.get("symbol") and row.get("strategy_id")
            }
            existing_symbol_strategy_map.update(
                {
                    str(row.get("symbol")).upper(): str(row.get("strategy_id"))
                    for row in existing_positions
                    if row.get("symbol")
                    and row.get("strategy_id")
                    and str(row.get("symbol")).upper() not in existing_symbol_strategy_map
                }
            )

            raw_orders = alpaca.get_orders(status="all", limit=200) or []
            order_rows = _normalize_orders(
                raw_orders, user_id=resolved_user_id, environment=environment
            )
            for row in order_rows:
                symbol = str(row.get("symbol", "")).upper()
                if not symbol:
                    continue
                sid = (
                    existing_symbol_strategy_map.get(symbol)
                    or strategy_hints.get(symbol)
                    or default_strategy_id
                    or _pick_strategy_for_symbol(symbol, running_strategy_ids)
                )
                if sid:
                    row["strategy_id"] = sid
                    existing_symbol_strategy_map.setdefault(symbol, sid)

            orders_repo.upsert_many(order_rows)
            trade_rows = _normalize_filled_orders_to_trades(
                raw_orders,
                user_id=resolved_user_id,
                environment=environment,
                symbol_strategy_map=existing_symbol_strategy_map,
            )
            trades_repo.upsert_many(trade_rows)

            raw_positions = alpaca.get_positions() or []
            position_rows = _normalize_positions(
                raw_positions, user_id=resolved_user_id, environment=environment
            )
            for row in position_rows:
                symbol = str(row.get("symbol", "")).upper()
                if not symbol:
                    continue
                sid = (
                    existing_symbol_strategy_map.get(symbol)
                    or strategy_hints.get(symbol)
                    or default_strategy_id
                    or _pick_strategy_for_symbol(symbol, running_strategy_ids)
                )
                if sid:
                    row["strategy_id"] = sid
                    existing_symbol_strategy_map.setdefault(symbol, sid)

            positions_repo.replace_all(resolved_user_id, environment, position_rows)
            existing_order_strategy_map = {
                str(row.get("order_id")): str(row.get("strategy_id"))
                for row in existing_orders
                if row.get("order_id") and row.get("strategy_id")
            }

            logger.info(
                "dashboard.alpaca_sync env=%s orders=%s trades=%s positions=%s",
                environment,
                len(order_rows),
                len(trade_rows),
                len(position_rows),
            )
        except Exception as exc:
            logger.warning("dashboard.alpaca_sync failed env=%s error=%s", environment, exc)

    account_row = None
    if account_result.account:
        account_row = accounts_repo.upsert_account(
            resolved_user_id,
            environment,
            account_id=str(getattr(account_result.account, "id", "alpaca_account")),
            equity=float(account_result.account.equity),
            cash=float(account_result.account.cash),
            buying_power=float(account_result.account.buying_power),
            currency=str(account_result.account.currency),
        )
    if account_row is None:
        account_row = accounts_repo.get_latest(resolved_user_id, environment)

    equity = float(account_row["equity"]) if account_row else 0.0
    cash = float(account_row["cash"]) if account_row else 0.0

    # ✅ 프론트 타입이 string을 기대하므로 ISO string 고정
    worker_state= "running"  # (타입 alias 있으면 맞춰도 됨)
    worker_heartbeat = now_kst().isoformat()

    # ✅ bot_state: 프론트 타입과 불일치 값 방지
    bot_state = user_settings.get("bot_state", "running")
    allowed_bot_states = {"running", "stopped", "error", "queued"}
    if bot_state not in allowed_bot_states:
        bot_state = "running"

    next_run_at = user_settings.get("next_run_at") or plus_hours(1).isoformat()
    default_run = {
        "run_id": "run_init",
        "started_at": now_kst().isoformat(),
        "ended_at": now_kst().isoformat(),
        "result": "success",
        "orders_created": 0,
        "orders_failed": 0,
    }
    bot_last_run = bot_runs_repo.get_latest(resolved_user_id)
    if not isinstance(bot_last_run, dict):
        bot_last_run = default_run
    else:
        for key, value in default_run.items():
            bot_last_run.setdefault(key, value)
    if bot_last_run.get("ended_at") is None:
        bot_last_run["ended_at"] = now_kst().isoformat()

    active_strategies = []
    allowed_strategy_states = {"running", "paused", "idle", "error"}
    strategies_repo.ensure_seed(resolved_user_id)
    strategy_runtime_metrics: Dict[str, Dict[str, float | int]] = {}
    try:
        position_rows = positions_repo.list(resolved_user_id, environment, limit=1000)
        strategy_runtime_metrics = _compute_strategy_runtime_metrics(position_rows)
    except Exception:
        strategy_runtime_metrics = {}

    try:
        strategies_repo.update_runtime_metrics(resolved_user_id, strategy_runtime_metrics)
    except Exception as exc:
        logger.warning(
            "dashboard.strategy_metrics_update_failed user_id=%s env=%s error=%s",
            resolved_user_id,
            environment,
            exc,
        )

    for strat in strategies_repo.list_active(resolved_user_id):
        state = strat.get("state") if strat.get("state") in allowed_strategy_states else "idle"
        strategy_id = str(strat["strategy_id"])
        runtime_metrics = strategy_runtime_metrics.get(strategy_id, {})
        positions_count = int(runtime_metrics.get("positions_count", strat.get("positions_count", 0)) or 0)
        pnl_today_value = float(runtime_metrics.get("pnl_today_value", strat.get("pnl_today_value", 0)) or 0.0)
        pnl_today_pct = float(runtime_metrics.get("pnl_today_pct", strat.get("pnl_today_pct", 0)) or 0.0)
        managed_value = float(runtime_metrics.get("managed_value", 0.0) or 0.0)
        active_strategies.append(
            {
                "strategy_id": strategy_id,
                "name": strat["name"],
                "state": state,
                "positions_count": positions_count,
                "managed_value": managed_value,
                "pnl_today": {
                    "value": pnl_today_value,
                    "pct": pnl_today_pct,
                },
            }
        )

    all_strategy_name_map: Dict[str, str] = {}
    try:
        for row in strategies_repo.list(resolved_user_id):
            sid = row.get("strategy_id")
            name = row.get("name")
            if sid and name:
                all_strategy_name_map[str(sid)] = str(name)
    except Exception:
        all_strategy_name_map = {}
    strategy_name_map = {str(item["strategy_id"]): str(item["name"]) for item in active_strategies}
    strategy_name_map.update({k: v for k, v in all_strategy_name_map.items() if k not in strategy_name_map})

    trades = []
    for trade in trades_repo.list_recent(resolved_user_id, environment):
        filled_at = trade.get("filled_at") or now_kst().isoformat()
        strategy_id = trade.get("strategy_id") or "unknown"
        raw_strategy_name = str(trade.get("strategy_name") or "").strip()
        is_placeholder_name = raw_strategy_name.lower() in {"", "unknown", "unknown strategy", "-"}
        strategy_name = (
            strategy_name_map.get(str(strategy_id))
            if is_placeholder_name
            else raw_strategy_name
        ) or "Unknown Strategy"
        trades.append(
            {
                "fill_id": trade.get("fill_id") or "fill_unknown",
                "filled_at": filled_at,
                "symbol": trade.get("symbol") or "UNKNOWN",
                "side": trade.get("side") or "buy",
                "qty": float(trade.get("qty") or 0),
                "price": float(trade.get("price") or 0),
                "strategy_id": strategy_id,
                "strategy_name": strategy_name,
            }
        )

    # ✅ alerts.link: tab이 없으면 키를 제거해서 (undefined vs null) 이슈 방지
    alerts = []
    for alert in alerts_repo.list_recent(resolved_user_id):
        link = alert.get("link") or {}
        link_obj = {"page": link.get("page") or "trading"}
        if link.get("tab") is not None:
            link_obj["tab"] = link.get("tab")

        alerts.append(
            {
                "alert_id": alert.get("alert_id") or "alert_unknown",
                "severity": alert.get("severity") or "info",
                "type": alert.get("type") or "general",
                "title": alert.get("title") or "Alert",
                "message": alert.get("message") or "",
                "occurred_at": alert.get("occurred_at") or now_kst().isoformat(),
                "link": link_obj,
            }
        )

    history_curve: List[dict] = []
    try:
        history_timeframe = _range_to_alpaca_timeframe(range)
        history = alpaca.get_portfolio_history(
            period=_range_to_alpaca_period(range),
            timeframe=history_timeframe,
        )
        history_curve = _history_to_equity_points(history)
        if range == "1D":
            history_curve = _downsample_equity_to_hourly(history_curve)
        history_curve, _ = _ensure_latest_equity_point(history_curve, equity)
        if history_curve:
            portfolio_repo.replace_equity_curve_range(
                resolved_user_id,
                environment,
                history_curve,
                cash=cash,
            )
            logger.info(
                "dashboard.performance_from_alpaca env=%s range=%s points=%s",
                environment,
                range,
                len(history_curve),
            )
    except Exception as exc:
        logger.warning(
            "dashboard.performance_alpaca_failed env=%s range=%s error=%s",
            environment,
            range,
            exc,
        )

    # ✅ equity_curve: Alpaca history 우선, 없으면 snapshots fallback
    equity_curve_raw = history_curve or portfolio_repo.list_equity_curve(
        resolved_user_id, environment, _range_days(range)
    ) or []

    def _pick_time_key(row: dict) -> str | None:
        # 흔히 나오는 key들을 모두 허용
        return (
            row.get("t")
            or row.get("time")
            or row.get("ts")
            or row.get("date")
            or row.get("datetime")
            or row.get("created_at")
        )

    equity_curve = []
    for row in equity_curve_raw:
        if not isinstance(row, dict):
            continue
        t = _pick_time_key(row)
        if t is None:
            continue
        equity_val = row.get("equity")
        # 혹시 다른 이름(value 등)으로 올 수도 있으니 보조
        if equity_val is None:
            equity_val = row.get("value") or row.get("equity_value")
        equity_curve.append({"t": str(t), "equity": float(equity_val or 0)})
    equity_curve = _sanitize_equity_curve(equity_curve)

    if not equity_curve and equity > 0:
        # fallback도 프론트 타입에 맞게 {t, equity}로
        fallback = _equity_curve_fallback(equity) or []
        equity_curve = []
        for row in fallback:
            if isinstance(row, dict):
                t = _pick_time_key(row) or row.get("t")
                equity_val = row.get("equity") if row.get("equity") is not None else row.get("value")
                if t is not None:
                    equity_curve.append({"t": str(t), "equity": float(equity_val or 0)})

    equity_curve, appended_latest = _ensure_latest_equity_point(equity_curve, equity)
    if appended_latest and equity_curve:
        try:
            portfolio_repo.replace_equity_curve_range(
                resolved_user_id,
                environment,
                equity_curve,
                cash=cash,
            )
        except Exception:
            pass

    first_equity = equity_curve[0]["equity"] if equity_curve else equity
    last_equity = equity_curve[-1]["equity"] if equity_curve else equity
    return_pct = ((last_equity - first_equity) / first_equity) * 100 if first_equity else 0.0
    max_drawdown_pct = _max_drawdown_pct(equity_curve)

    today_pnl_value = sum(float(s["pnl_today"]["value"]) for s in active_strategies)
    today_pnl_pct = (today_pnl_value / equity * 100) if equity else 0.0

    positions_count = positions_repo.count(resolved_user_id, environment)
    active_positions_count = positions_count or sum(s["positions_count"] for s in active_strategies)
    active_positions_new = 0

    total_pnl_value = last_equity - first_equity
    total_pnl_pct = return_pct

    return DashboardResponse(
        mode={"environment": environment, "kill_switch": kill_switch},
        status={
            "broker": {
                "state": broker_state,
                "latency_ms": account_result.latency_ms or 0,
            },
            "worker": {
                "state": worker_state,
                # ✅ string 고정 (TS: string)
                "last_heartbeat_at": worker_heartbeat,
            },
            "data": {"state": "ok", "lag_seconds": 2},
        },
        account={
            "equity": float(equity),
            "cash": float(cash),
            "today_pnl": {"value": today_pnl_value, "pct": today_pnl_pct},
            "active_positions": {
                "count": active_positions_count,
                "new_today": active_positions_new,
            },
        },
        kpi={
            "today_pnl": {"value": today_pnl_value, "pct": today_pnl_pct},
            "total_pnl": {"value": total_pnl_value, "pct": total_pnl_pct},
            "active_positions": {
                "count": active_positions_count,
                "new_today": active_positions_new,
            },
            "selected_metric": {
                "name": "max_drawdown",
                "value": max_drawdown_pct,
                "unit": "pct",
                "window": range,
            },
        },
        performance={
            "range": range,
            # ✅ {t, equity} 보장
            "equity_curve": equity_curve,
            "summary": {"return_pct": return_pct, "max_drawdown_pct": max_drawdown_pct},
        },
        bot={
            "state": bot_state,
            "last_run": {
                "run_id": bot_last_run["run_id"],
                # 프론트가 string 기대하므로 iso string으로 고정하는 게 가장 안전
                "started_at": str(parse_datetime(bot_last_run["started_at"])),
                "ended_at": str(parse_datetime(bot_last_run["ended_at"])),
                "result": bot_last_run["result"],
                "orders_created": bot_last_run["orders_created"],
                "orders_failed": bot_last_run["orders_failed"],
            },
            "next_run_at": str(parse_datetime(next_run_at)),
        },
        active_strategies=active_strategies,
        recent_trades=trades,
        alerts=alerts,
    )
