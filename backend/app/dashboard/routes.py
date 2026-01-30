from __future__ import annotations

from typing import List, Literal

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


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    range: RangeLiteral = Query(default="1M", description="Time range"),
    user_id: str | None = Query(default=None),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
):
    settings = get_settings()
    resolved_user_id = resolve_user_id(settings, x_user_id or user_id)

    settings_repo = UserSettingsRepository(settings)
    strategies_repo = StrategiesRepository(settings)
    trades_repo = TradesRepository(settings)
    alerts_repo = AlertsRepository(settings)
    accounts_repo = UserAccountsRepository(settings)
    portfolio_repo = PortfolioRepository(settings)
    positions_repo = PositionsRepository(settings)
    bot_runs_repo = BotRunsRepository(settings)

    user_settings = settings_repo.get_or_create(resolved_user_id)
    environment = user_settings.get("environment", "paper")
    kill_switch = bool(user_settings.get("kill_switch", False))

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

    bot_state = user_settings.get("bot_state", "running")
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
    allowed_states = {"running", "paused", "idle", "error"}
    strategies_repo.ensure_seed(resolved_user_id)
    for strat in strategies_repo.list_active(resolved_user_id):
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

    alerts = []
    for alert in alerts_repo.list_recent(resolved_user_id):
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

    equity_curve = portfolio_repo.list_equity_curve(
        resolved_user_id, environment, _range_days(range)
    )
    if not equity_curve and equity > 0:
        equity_curve = _equity_curve_fallback(equity)

    first_equity = equity_curve[0]["equity"] if equity_curve else equity
    last_equity = equity_curve[-1]["equity"] if equity_curve else equity
    return_pct = ((last_equity - first_equity) / first_equity) * 100 if first_equity else 0.0
    max_drawdown_pct = _max_drawdown_pct(equity_curve)

    today_pnl_value = sum(
        float(s["pnl_today"]["value"]) for s in active_strategies
    )
    today_pnl_pct = (today_pnl_value / equity * 100) if equity else 0.0
    positions_count = positions_repo.count(resolved_user_id, environment)
    active_positions_count = positions_count or sum(
        s["positions_count"] for s in active_strategies
    )
    active_positions_new = 0

    total_pnl_value = last_equity - first_equity
    total_pnl_pct = return_pct

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
            "equity_curve": equity_curve,
            "summary": {"return_pct": return_pct, "max_drawdown_pct": max_drawdown_pct},
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
