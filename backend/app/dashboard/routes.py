from __future__ import annotations

import logging
from typing import List, Literal, Any
from datetime import datetime

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
                "side": str(_get_field(order, "side", "")).lower(),
                "qty": _to_float(_get_field(order, "qty", 0)),
                "type": str(_get_field(order, "type", "market")),
                "status": str(_get_field(order, "status", "unknown")),
                "submitted_at": _to_iso(_get_field(order, "submitted_at")),
                "filled_at": _to_iso(_get_field(order, "filled_at")),
                "strategy_id": None,
            }
        )
    return rows


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
            raw_orders = alpaca.get_orders(status="all", limit=200) or []
            order_rows = _normalize_orders(
                raw_orders, user_id=resolved_user_id, environment=environment
            )
            orders_repo.upsert_many(order_rows)

            raw_positions = alpaca.get_positions() or []
            position_rows = _normalize_positions(
                raw_positions, user_id=resolved_user_id, environment=environment
            )
            positions_repo.replace_all(resolved_user_id, environment, position_rows)

            logger.info(
                "dashboard.alpaca_sync env=%s orders=%s positions=%s",
                environment,
                len(order_rows),
                len(position_rows),
            )
        except Exception as exc:
            logger.warning("dashboard.alpaca_sync failed env=%s error=%s", environment, exc)

    account_row = accounts_repo.get_latest(resolved_user_id, environment)
    if account_row is None and account_result.account:
        account_row = accounts_repo.upsert_account(
            resolved_user_id,
            environment,
            account_id=str(getattr(account_result.account, "id", "alpaca_account")),
            equity=float(account_result.account.equity),
            cash=float(account_result.account.cash),
            buying_power=float(account_result.account.buying_power),
            currency=str(account_result.account.currency),
        )

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
    for strat in strategies_repo.list_active(resolved_user_id):
        state = strat.get("state") if strat.get("state") in allowed_strategy_states else "idle"
        active_strategies.append(
            {
                "strategy_id": strat["strategy_id"],
                "name": strat["name"],
                "state": state,
                "positions_count": int(strat.get("positions_count", 0)),
                "pnl_today": {
                    "value": float(strat.get("pnl_today_value", 0)),
                    "pct": float(strat.get("pnl_today_pct", 0)),
                },
            }
        )

    trades = []
    for trade in trades_repo.list_recent(resolved_user_id, environment):
        filled_at = trade.get("filled_at") or now_kst().isoformat()
        trades.append(
            {
                "fill_id": trade.get("fill_id") or "fill_unknown",
                "filled_at": filled_at,
                "symbol": trade.get("symbol") or "UNKNOWN",
                "side": trade.get("side") or "buy",
                "qty": float(trade.get("qty") or 0),
                "price": float(trade.get("price") or 0),
                "strategy_id": trade.get("strategy_id") or "unknown",
                "strategy_name": trade.get("strategy_name") or "Unknown Strategy",
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

    # ✅ equity_curve: repo 반환 포맷이 달라도 프론트 타입 {t, equity}로 normalize
    equity_curve_raw = portfolio_repo.list_equity_curve(
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
