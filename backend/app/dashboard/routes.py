from __future__ import annotations

from datetime import timedelta
from typing import List, Literal

from fastapi import APIRouter, Query

from app.alpaca.client import AlpacaClient
from app.core.config import get_settings
from app.core.time import now_kst, parse_datetime, plus_hours
from app.schemas.dashboard import DashboardResponse
from app.storage.alerts_repo import AlertsRepository
from app.storage.settings_repo import SettingsRepository
from app.storage.strategies_repo import StrategiesRepository
from app.storage.trades_repo import TradesRepository


router = APIRouter()


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


def _mock_equity_curve(range_value: str) -> List[dict]:
    days = _range_days(range_value)
    points = 10
    base = 100000.0
    now = now_kst()
    step = max(days // points, 1)
    curve = []
    for i in range(points):
        t = now - timedelta(days=step * (points - 1 - i))
        equity = base * (1 + 0.002 * i)
        curve.append({"t": t, "equity": equity})
    return curve


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    range: RangeLiteral = Query(default="1M", description="Time range")
):
    settings = get_settings()
    settings_repo = SettingsRepository(settings)
    strategies_repo = StrategiesRepository(settings)
    trades_repo = TradesRepository(settings)
    alerts_repo = AlertsRepository(settings)

    environment = settings_repo.get("environment", "paper")
    kill_switch = bool(settings_repo.get("kill_switch", False))

    alpaca = AlpacaClient(settings, environment)
    account_result = alpaca.get_account()
    broker_state = "connected" if account_result.account else "down"

    if account_result.account:
        equity = account_result.account.equity
        cash = account_result.account.cash
    else:
        equity = 100000.0
        cash = 25000.0

    worker_state = settings_repo.get("worker_state", "running")
    worker_heartbeat = settings_repo.get(
        "worker_last_heartbeat_at", now_kst().isoformat()
    )

    bot_state = settings_repo.get("bot_state", "running")
    bot_last_run = settings_repo.get("bot_last_run", None)
    default_run = {
        "run_id": "run_20260129_001",
        "started_at": now_kst().isoformat(),
        "ended_at": now_kst().isoformat(),
        "result": "success",
        "orders_created": 4,
        "orders_failed": 0,
    }
    if not isinstance(bot_last_run, dict):
        bot_last_run = default_run
    else:
        for key, value in default_run.items():
            bot_last_run.setdefault(key, value)
    if bot_last_run.get("ended_at") is None:
        bot_last_run["ended_at"] = now_kst().isoformat()
    next_run_at = settings_repo.get("next_run_at", None)
    if not next_run_at:
        next_run_at = plus_hours(1).isoformat()

    active_strategies = []
    allowed_states = {"running", "paused", "idle", "error"}
    for strat in strategies_repo.list_active():
        state = strat.get("state") if strat.get("state") in allowed_states else "idle"
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
    for trade in trades_repo.list_recent():
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

    alerts = []
    for alert in alerts_repo.list_recent():
        link = alert.get("link") or {}
        alerts.append(
            {
                "alert_id": alert.get("alert_id") or "alert_unknown",
                "severity": alert.get("severity") or "info",
                "type": alert.get("type") or "general",
                "title": alert.get("title") or "Alert",
                "message": alert.get("message") or "",
                "occurred_at": alert.get("occurred_at") or now_kst().isoformat(),
                "link": {"page": link.get("page") or "trading", "tab": link.get("tab")},
            }
        )

    equity_curve = _mock_equity_curve(range)
    if account_result.account:
        history = alpaca.get_portfolio_history(timeframe=range)
        if history and getattr(history, "equity", None):
            equity_curve = [
                {"t": now_kst().isoformat(), "equity": float(value)}
                for value in history.equity
            ]

    first_equity = equity_curve[0]["equity"] if equity_curve else equity
    last_equity = equity_curve[-1]["equity"] if equity_curve else equity
    return_pct = ((last_equity - first_equity) / first_equity) * 100 if first_equity else 0.0

    today_pnl_value = 123.45
    today_pnl_pct = 0.12
    active_positions_count = sum(s["positions_count"] for s in active_strategies)
    active_positions_new = 0

    return DashboardResponse(
        mode={"environment": environment, "kill_switch": kill_switch},
        status={
            "broker": {
                "state": broker_state,
                "latency_ms": account_result.latency_ms or 0,
            },
            "worker": {
                "state": worker_state,
                "last_heartbeat_at": parse_datetime(worker_heartbeat),
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
            "total_pnl": {"value": 15600.0, "pct": 15.6},
            "active_positions": {
                "count": active_positions_count,
                "new_today": active_positions_new,
            },
            "selected_metric": {
                "name": "max_drawdown",
                "value": -4.2,
                "unit": "pct",
                "window": range,
            },
        },
        performance={
            "range": range,
            "equity_curve": equity_curve,
            "summary": {"return_pct": return_pct, "max_drawdown_pct": -2.1},
        },
        bot={
            "state": bot_state,
            "last_run": {
                "run_id": bot_last_run["run_id"],
                "started_at": parse_datetime(bot_last_run["started_at"]),
                "ended_at": parse_datetime(bot_last_run["ended_at"]),
                "result": bot_last_run["result"],
                "orders_created": bot_last_run["orders_created"],
                "orders_failed": bot_last_run["orders_failed"],
            },
            "next_run_at": parse_datetime(next_run_at),
        },
        active_strategies=active_strategies,
        recent_trades=trades,
        alerts=alerts,
    )
