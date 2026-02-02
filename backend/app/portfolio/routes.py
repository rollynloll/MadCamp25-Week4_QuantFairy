from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Query

from app.alpaca.client import AlpacaClient
from app.core.config import get_settings
from app.core.errors import APIError
from app.core.time import now_kst
from app.schemas.portfolio import (
    ActivityItem,
    PortfolioActivityResponse,
    PortfolioAllocationResponse,
    PortfolioAttributionResponse,
    PortfolioDrawdownResponse,
    PortfolioKpiResponse,
    PortfolioPerformanceResponse,
    PortfolioPositionsResponse,
    PortfolioRebalanceRequest,
    PortfolioRebalanceResponse,
    PortfolioSummaryResponse,
    RangeLiteral,
    StrategyStateRequest,
    StrategyStateResponse,
    UpdateUserStrategyRequest,
    UpdateUserStrategyResponse,
    UserStrategiesResponse,
    UserStrategyDetailResponse,
)
from app.schemas.trading import KillSwitchRequest, KillSwitchResponse
from app.storage.my_strategies_repo import MyStrategiesRepository
from app.storage.strategies_repo import StrategiesRepository
from app.storage.user_settings_repo import UserSettingsRepository


router = APIRouter()

EnvLiteral = Literal["paper", "live"]
SideLiteral = Literal["all", "long", "short"]
SortLiteral = Literal["pnl", "pnl_pct", "value", "symbol"]
OrderLiteral = Literal["asc", "desc"]
AttributionByLiteral = Literal["strategy", "sector"]


def _resolve_user_id() -> str:
    settings = get_settings()
    return settings.default_user_id or "demo_user"


def _range_days(range_value: RangeLiteral) -> int:
    return {
        "1W": 7,
        "1M": 30,
        "3M": 90,
        "1Y": 365,
        "ALL": 730,
    }[range_value]


def _range_to_alpaca_period(range_value: RangeLiteral) -> str:
    return {
        "1W": "1W",
        "1M": "1M",
        "3M": "3M",
        "1Y": "1A",
        "ALL": "ALL",
    }[range_value]


def _get_field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_pct(value: Any) -> float:
    pct = _to_float(value)
    if abs(pct) <= 1:
        return pct * 100
    return pct


def _format_timestamp(ts: Any) -> str:
    if isinstance(ts, datetime):
        return ts.date().isoformat()
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    return str(ts)


def _require_account(client: AlpacaClient):
    result = client.get_account()
    if result.account is None:
        raise APIError(
            "ALPACA_UNAVAILABLE",
            "Alpaca account not available",
            result.error or "Missing Alpaca credentials",
            status_code=503,
        )
    return result.account, result.latency_ms or 0


def _normalize_positions(raw_positions: Any) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for pos in raw_positions or []:
        symbol = str(_get_field(pos, "symbol", "")).upper()
        if not symbol:
            continue
        side_raw = str(_get_field(pos, "side", "long")).lower()
        side = "short" if "short" in side_raw else "long"
        qty = _to_float(_get_field(pos, "qty", 0))
        avg_entry_price = _to_float(_get_field(pos, "avg_entry_price", 0))
        current_price = _to_float(_get_field(pos, "current_price", 0))
        market_value = _to_float(
            _get_field(pos, "market_value", current_price * qty)
        )
        unrealized_pl = _to_float(_get_field(pos, "unrealized_pl", 0))
        unrealized_plpc = _to_pct(_get_field(pos, "unrealized_plpc", 0))
        strategy_id = (
            _get_field(pos, "strategy_id")
            or _get_field(pos, "user_strategy_id")
            or "unassigned"
        )
        strategy_name = _get_field(pos, "strategy_name") or "Unassigned"
        items.append(
            {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "avg_entry_price": avg_entry_price,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": {
                    "value": unrealized_pl,
                    "pct": unrealized_plpc,
                },
                "strategy": {
                    "user_strategy_id": str(strategy_id),
                    "name": str(strategy_name),
                },
            }
        )
    return items


def _positions_exposure(
    positions: List[Dict[str, Any]],
    equity: float,
    cash: float,
) -> Dict[str, float]:
    long_value = 0.0
    short_value = 0.0
    abs_values: List[float] = []
    for pos in positions:
        value = abs(_to_float(pos.get("market_value", 0.0)))
        abs_values.append(value)
        if pos.get("side") == "short":
            short_value += value
        else:
            long_value += value

    net_pct = ((long_value - short_value) / equity * 100) if equity else 0.0
    gross_pct = ((long_value + short_value) / equity * 100) if equity else 0.0
    cash_pct = (cash / equity * 100) if equity else 0.0
    top5 = sum(sorted(abs_values, reverse=True)[:5])
    top5_pct = (top5 / equity * 100) if equity else 0.0
    return {
        "net_pct": round(net_pct, 2),
        "gross_pct": round(gross_pct, 2),
        "cash_pct": round(cash_pct, 2),
        "top5_concentration_pct": round(top5_pct, 2),
    }


def _history_to_equity_points(history: Any) -> List[Dict[str, Any]]:
    if history is None:
        return []
    timestamps = _get_field(history, "timestamp") or _get_field(history, "timestamps")
    equity = _get_field(history, "equity")
    if not timestamps or not equity:
        return []
    points: List[Dict[str, Any]] = []
    for ts, value in zip(timestamps, equity):
        points.append({"t": _format_timestamp(ts), "equity": _to_float(value)})
    return points


def _compute_returns(equity_curve: List[Dict[str, Any]]) -> List[float]:
    returns: List[float] = []
    prev = None
    for point in equity_curve:
        equity = _to_float(point.get("equity", 0.0))
        if prev is None:
            prev = equity
            continue
        ret = (equity / prev - 1.0) if prev else 0.0
        returns.append(ret)
        prev = equity
    return returns


def _drawdown_curve(equity_curve: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    drawdown: List[Dict[str, Any]] = []
    peak = None
    for point in equity_curve:
        equity = _to_float(point.get("equity", 0.0))
        if peak is None or equity > peak:
            peak = equity
        dd = (equity - peak) / peak * 100 if peak else 0.0
        drawdown.append({"t": point.get("t"), "drawdown_pct": round(dd, 2)})
    return drawdown


def _kpi_from_equity(equity_curve: List[Dict[str, Any]]) -> Dict[str, float]:
    if len(equity_curve) < 2:
        return {
            "period_return_pct": 0.0,
            "cagr_pct": 0.0,
            "volatility_pct": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "win_rate_pct": 0.0,
        }

    first = _to_float(equity_curve[0].get("equity", 0.0))
    last = _to_float(equity_curve[-1].get("equity", 0.0))
    period_return_pct = ((last / first - 1.0) * 100) if first else 0.0

    returns = _compute_returns(equity_curve)
    mean = sum(returns) / len(returns) if returns else 0.0
    variance = sum((r - mean) ** 2 for r in returns) / len(returns) if returns else 0.0
    std = math.sqrt(variance) if variance else 0.0

    volatility_pct = std * math.sqrt(252) * 100 if std else 0.0
    sharpe = (mean / std * math.sqrt(252)) if std else 0.0

    periods = max(len(returns), 1)
    cagr_pct = ((last / first) ** (252 / periods) - 1) * 100 if first else 0.0

    drawdown = _drawdown_curve(equity_curve)
    max_drawdown_pct = min((d["drawdown_pct"] for d in drawdown), default=0.0)

    win_rate_pct = (
        sum(1 for r in returns if r > 0) / len(returns) * 100 if returns else 0.0
    )

    return {
        "period_return_pct": round(period_return_pct, 2),
        "cagr_pct": round(cagr_pct, 2),
        "volatility_pct": round(volatility_pct, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "win_rate_pct": round(win_rate_pct, 2),
    }


def _load_alpaca_positions(client: AlpacaClient) -> List[Dict[str, Any]]:
    raw_positions = client.get_positions()
    if raw_positions is None:
        return []
    return _normalize_positions(raw_positions)


@router.get(
    "/portfolio/summary",
    response_model=PortfolioSummaryResponse,
    summary="Portfolio summary",
)
async def get_portfolio_summary(
    env: EnvLiteral = Query(..., description="paper or live"),
):
    settings = get_settings()
    client = AlpacaClient(settings, env)
    account, latency_ms = _require_account(client)
    raw_positions = client.get_positions() or []
    positions = _normalize_positions(raw_positions)
    settings_repo = UserSettingsRepository(settings)
    user_settings = settings_repo.get_or_create(_resolve_user_id())

    today_pnl_value = 0.0
    for pos in raw_positions:
        today_pnl_value += _to_float(_get_field(pos, "unrealized_intraday_pl", 0))
    today_pnl_pct = (today_pnl_value / account.equity * 100) if account.equity else 0.0

    long_count = len([p for p in positions if p.get("side") == "long"])
    short_count = len([p for p in positions if p.get("side") == "short"])

    exposure = _positions_exposure(positions, account.equity, account.cash)

    now = now_kst().isoformat()
    return {
        "env": env,
        "as_of": now,
        "mode": {
            "environment": env,
            "kill_switch": bool(user_settings.get("kill_switch", False)),
        },
        "status": {
            "broker": {"state": "up", "latency_ms": latency_ms},
            "worker": {"state": "running", "last_heartbeat_at": now},
        },
        "account": {
            "equity": account.equity,
            "cash": account.cash,
            "buying_power": account.buying_power,
            "today_pnl": {
                "value": round(today_pnl_value, 2),
                "pct": round(today_pnl_pct, 2),
            },
            "open_positions": {
                "count": len(positions),
                "long": long_count,
                "short": short_count,
            },
        },
        "exposure": exposure,
    }


@router.get(
    "/portfolio/performance",
    response_model=PortfolioPerformanceResponse,
    summary="Portfolio performance time series",
)
async def get_portfolio_performance(
    env: EnvLiteral = Query(..., description="paper or live"),
    range: RangeLiteral = Query(..., description="1W|1M|3M|1Y|ALL"),
    benchmark: str = Query(default="SPY"),
    downsample: Optional[str] = Query(default=None),
):
    _ = downsample
    settings = get_settings()
    client = AlpacaClient(settings, env)
    _require_account(client)

    history = client.get_portfolio_history(
        period=_range_to_alpaca_period(range),
        timeframe="1D",
    )
    if history is None:
        raise APIError(
            "ALPACA_UNAVAILABLE",
            "Portfolio history not available",
            "Check Alpaca credentials or account permissions",
            status_code=503,
        )

    equity_curve = _history_to_equity_points(history)
    return {
        "env": env,
        "range": range,
        "benchmark": benchmark,
        "as_of": now_kst().isoformat(),
        "equity_curve": equity_curve,
        "benchmark_curve": [],
    }


@router.get(
    "/portfolio/drawdown",
    response_model=PortfolioDrawdownResponse,
    summary="Portfolio drawdown",
)
async def get_portfolio_drawdown(
    env: EnvLiteral = Query(..., description="paper or live"),
    range: RangeLiteral = Query(..., description="1W|1M|3M|1Y|ALL"),
):
    settings = get_settings()
    client = AlpacaClient(settings, env)
    _require_account(client)

    history = client.get_portfolio_history(
        period=_range_to_alpaca_period(range),
        timeframe="1D",
    )
    if history is None:
        raise APIError(
            "ALPACA_UNAVAILABLE",
            "Portfolio history not available",
            "Check Alpaca credentials or account permissions",
            status_code=503,
        )

    equity_curve = _history_to_equity_points(history)
    drawdown_curve = _drawdown_curve(equity_curve)
    current_dd = drawdown_curve[-1]["drawdown_pct"] if drawdown_curve else 0.0
    max_dd = min((d["drawdown_pct"] for d in drawdown_curve), default=0.0)

    return {
        "env": env,
        "range": range,
        "drawdown_curve": drawdown_curve,
        "summary": {
            "current_drawdown_pct": round(current_dd, 2),
            "max_drawdown_pct": round(max_dd, 2),
        },
    }


@router.get(
    "/portfolio/kpi",
    response_model=PortfolioKpiResponse,
    summary="Portfolio KPI metrics",
)
async def get_portfolio_kpi(
    env: EnvLiteral = Query(..., description="paper or live"),
    range: RangeLiteral = Query(..., description="1W|1M|3M|1Y|ALL"),
):
    settings = get_settings()
    client = AlpacaClient(settings, env)
    _require_account(client)

    history = client.get_portfolio_history(
        period=_range_to_alpaca_period(range),
        timeframe="1D",
    )
    if history is None:
        raise APIError(
            "ALPACA_UNAVAILABLE",
            "Portfolio history not available",
            "Check Alpaca credentials or account permissions",
            status_code=503,
        )

    equity_curve = _history_to_equity_points(history)
    return {
        "env": env,
        "range": range,
        "kpi": _kpi_from_equity(equity_curve),
    }


@router.get(
    "/portfolio/positions",
    response_model=PortfolioPositionsResponse,
    summary="List open positions",
)
async def get_portfolio_positions(
    env: EnvLiteral = Query(..., description="paper or live"),
    q: Optional[str] = Query(default=None, description="Symbol search"),
    side: SideLiteral = Query(default="all"),
    strategy_id: Optional[str] = Query(default=None),
    sort: Optional[SortLiteral] = Query(default=None),
    order: OrderLiteral = Query(default="desc"),
):
    settings = get_settings()
    client = AlpacaClient(settings, env)
    _require_account(client)

    items = _load_alpaca_positions(client)
    if q:
        q_lower = q.lower()
        items = [item for item in items if q_lower in item["symbol"].lower()]
    if side != "all":
        items = [item for item in items if item["side"] == side]
    if strategy_id:
        items = [
            item
            for item in items
            if item["strategy"]["user_strategy_id"] == strategy_id
        ]

    if sort:
        if sort == "symbol":
            key_fn = lambda item: item["symbol"]
        elif sort == "value":
            key_fn = lambda item: item["market_value"]
        elif sort == "pnl":
            key_fn = lambda item: item["unrealized_pnl"]["value"]
        else:
            key_fn = lambda item: item["unrealized_pnl"]["pct"]
        items = sorted(items, key=key_fn, reverse=(order == "desc"))

    return {"env": env, "items": items}


@router.get(
    "/portfolio/allocation",
    response_model=PortfolioAllocationResponse,
    summary="Allocation & exposure",
)
async def get_portfolio_allocation(
    env: EnvLiteral = Query(..., description="paper or live"),
):
    settings = get_settings()
    client = AlpacaClient(settings, env)
    account, _ = _require_account(client)
    positions = _load_alpaca_positions(client)

    exposure = _positions_exposure(positions, account.equity, account.cash)
    return {
        "env": env,
        "by_sector": [],
        "by_strategy": [],
        "exposure": exposure,
    }


@router.get(
    "/portfolio/attribution",
    response_model=PortfolioAttributionResponse,
    summary="Performance attribution",
)
async def get_portfolio_attribution(
    env: EnvLiteral = Query(..., description="paper or live"),
    by: AttributionByLiteral = Query(..., description="strategy or sector"),
    range: Optional[RangeLiteral] = Query(default=None),
):
    settings = get_settings()
    client = AlpacaClient(settings, env)
    account, _ = _require_account(client)
    positions = _load_alpaca_positions(client)

    items: List[Dict[str, Any]] = []
    if by == "strategy":
        grouped: Dict[str, Dict[str, Any]] = {}
        for pos in positions:
            key = pos["strategy"]["user_strategy_id"]
            group = grouped.setdefault(
                key,
                {
                    "key": key,
                    "label": pos["strategy"]["name"],
                    "value": 0.0,
                    "pnl": 0.0,
                },
            )
            group["value"] += abs(_to_float(pos.get("market_value", 0.0)))
            group["pnl"] += _to_float(pos["unrealized_pnl"]["value"])
        for group in grouped.values():
            exposure_pct = (group["value"] / account.equity * 100) if account.equity else 0.0
            contribution_pct = (
                group["pnl"] / account.equity * 100 if account.equity else 0.0
            )
            items.append(
                {
                    "key": group["key"],
                    "label": group["label"],
                    "exposure_pct": round(exposure_pct, 2),
                    "unrealized_pnl_value": round(group["pnl"], 2),
                    "period_contribution_pct": round(contribution_pct, 2),
                }
            )
    return {"env": env, "range": range, "by": by, "items": items}


@router.get(
    "/user-strategies",
    response_model=UserStrategiesResponse,
    summary="List user strategies",
)
async def list_user_strategies(
    env: EnvLiteral = Query(..., description="paper or live"),
):
    settings = get_settings()
    user_id = _resolve_user_id()
    repo = MyStrategiesRepository(settings)
    rows = repo.list(user_id, filters={}, sort="updated_at", order="desc", limit=50, cursor_value=None)

    items = []
    for row in rows:
        risk = row.get("risk_limits") or {}
        items.append(
            {
                "user_strategy_id": row.get("strategy_id") or row.get("user_strategy_id"),
                "name": row.get("name", ""),
                "public_strategy_id": row.get("source_public_strategy_id", ""),
                "state": row.get("state", "idle"),
                "positions_count": int(row.get("positions_count", 0)),
                "today_pnl": {
                    "value": float(row.get("pnl_today_value", 0) or 0),
                    "pct": float(row.get("pnl_today_pct", 0) or 0),
                },
                "last_run_at": row.get("last_run_at") or row.get("updated_at") or now_kst().isoformat(),
                "params": row.get("params") or {},
                "risk_limits": {
                    "max_weight_per_asset": float(risk.get("max_weight_per_asset", 0) or 0),
                    "cash_buffer": float(risk.get("cash_buffer", 0) or 0),
                    "max_turnover_pct": risk.get("max_turnover_pct"),
                },
            }
        )
    return {"env": env, "items": items}


@router.get(
    "/user-strategies/{user_strategy_id}",
    response_model=UserStrategyDetailResponse,
    summary="User strategy detail",
)
async def get_user_strategy(
    user_strategy_id: str,
    env: EnvLiteral = Query(..., description="paper or live"),
):
    settings = get_settings()
    user_id = _resolve_user_id()
    repo = MyStrategiesRepository(settings)
    row = repo.get(user_id, user_strategy_id)
    if not row:
        raise APIError("NOT_FOUND", "User strategy not found", status_code=404)

    risk = row.get("risk_limits") or {}
    now = now_kst().isoformat()
    return {
        "env": env,
        "user_strategy_id": row.get("strategy_id") or user_strategy_id,
        "name": row.get("name", ""),
        "state": row.get("state", "idle"),
        "public_strategy": {
            "public_strategy_id": row.get("source_public_strategy_id", ""),
            "name": row.get("name", ""),
            "one_liner": row.get("one_liner", ""),
            "param_schema": row.get("param_schema", {}) or {},
        },
        "params": row.get("params") or {},
        "risk_limits": {
            "max_weight_per_asset": float(risk.get("max_weight_per_asset", 0) or 0),
            "cash_buffer": float(risk.get("cash_buffer", 0) or 0),
            "max_turnover_pct": risk.get("max_turnover_pct"),
        },
        "recent_runs": [
            {"run_id": "br_100", "started_at": now, "status": "success", "orders_created": 0}
        ],
    }


@router.patch(
    "/user-strategies/{user_strategy_id}",
    response_model=UpdateUserStrategyResponse,
    summary="Update user strategy",
)
async def update_user_strategy(
    user_strategy_id: str,
    payload: UpdateUserStrategyRequest,
    env: EnvLiteral = Query(..., description="paper or live"),
):
    _ = env
    settings = get_settings()
    user_id = _resolve_user_id()
    repo = MyStrategiesRepository(settings)
    existing = repo.get(user_id, user_strategy_id)
    if not existing:
        raise APIError("NOT_FOUND", "User strategy not found", status_code=404)
    if payload.name is None and payload.params is None and payload.risk_limits is None:
        raise APIError("VALIDATION_ERROR", "No fields to update", status_code=422)

    update_payload: Dict[str, Any] = {}
    if payload.name is not None:
        update_payload["name"] = payload.name
    if payload.params is not None:
        update_payload["params"] = payload.params
    if payload.risk_limits is not None:
        update_payload["risk_limits"] = payload.risk_limits.model_dump()

    updated = repo.update(user_id, user_strategy_id, update_payload)
    if updated is None:
        raise APIError(
            "DATA_SOURCE_UNAVAILABLE",
            "Failed to update user strategy",
            status_code=503,
        )

    return {
        "ok": True,
        "user_strategy_id": user_strategy_id,
        "updated_at": updated.get("updated_at") or now_kst().isoformat(),
    }


@router.post(
    "/user-strategies/{user_strategy_id}/state",
    response_model=StrategyStateResponse,
    summary="Update strategy state",
)
async def set_user_strategy_state(
    user_strategy_id: str,
    payload: StrategyStateRequest,
    env: EnvLiteral = Query(..., description="paper or live"),
):
    _ = env
    settings = get_settings()
    user_id = _resolve_user_id()
    repo = StrategiesRepository(settings)
    state_map = {"start": "running", "pause": "paused", "stop": "stopped"}
    new_state = state_map[payload.action]
    updated = repo.update_state(user_id, user_strategy_id, new_state)
    if updated is None:
        raise APIError(
            "DATA_SOURCE_UNAVAILABLE",
            "Failed to update strategy state",
            status_code=503,
        )
    return {"ok": True, "user_strategy_id": user_strategy_id, "state": new_state}


@router.post(
    "/bot/kill-switch",
    response_model=KillSwitchResponse,
    summary="Toggle kill switch",
)
async def set_kill_switch(
    payload: KillSwitchRequest,
    env: EnvLiteral = Query(..., description="paper or live"),
):
    _ = env
    settings = get_settings()
    user_id = _resolve_user_id()
    repo = UserSettingsRepository(settings)
    repo.update(user_id, {"kill_switch": payload.enabled, "kill_switch_reason": payload.reason})
    return KillSwitchResponse(enabled=payload.enabled)


@router.post(
    "/portfolio/rebalance",
    response_model=PortfolioRebalanceResponse,
    summary="Manual rebalance",
)
async def rebalance_portfolio(
    payload: PortfolioRebalanceRequest,
    env: EnvLiteral = Query(..., description="paper or live"),
):
    if payload.target_source == "strategy" and not payload.strategy_ids:
        raise APIError(
            "VALIDATION_ERROR",
            "strategy_ids required when target_source='strategy'",
            status_code=422,
        )
    rebalance_id = f"rb_{now_kst().strftime('%Y%m%d_%H%M%S')}"
    orders = [
        {
            "symbol": "AAPL",
            "side": "buy",
            "qty": 3.0,
            "notional": 585.6,
            "estimated_price": 195.2,
        },
        {
            "symbol": "MSFT",
            "side": "sell",
            "qty": 1.0,
            "notional": 368.5,
            "estimated_price": 368.5,
        },
    ]
    status = "preview" if payload.mode == "dry_run" else "submitted"
    return {
        "env": env,
        "mode": payload.mode,
        "rebalance_id": rebalance_id,
        "status": status,
        "orders": orders,
    }


@router.get(
    "/portfolio/activity",
    response_model=PortfolioActivityResponse,
    summary="Portfolio activity feed",
)
async def get_portfolio_activity(
    env: EnvLiteral = Query(..., description="paper or live"),
    types: Optional[str] = Query(default=None, description="orders,trades,alerts,bot_runs"),
    limit: int = Query(default=50, ge=1, le=200),
    cursor: Optional[str] = Query(default=None),
    symbol: Optional[str] = Query(default=None),
    user_strategy_id: Optional[str] = Query(default=None),
):
    _ = cursor
    now = now_kst()
    items: List[ActivityItem] = [
        {
            "type": "order",
            "id": "ord_1",
            "t": (now - timedelta(minutes=2)).isoformat(),
            "data": {
                "symbol": "AAPL",
                "side": "buy",
                "qty": 3,
                "status": "submitted",
                "user_strategy_id": "us_123",
            },
        },
        {
            "type": "alert",
            "id": "al_9",
            "t": (now - timedelta(minutes=1)).isoformat(),
            "data": {
                "severity": "warning",
                "title": "Broker latency high",
                "message": "latency_ms=850",
            },
        },
        {
            "type": "bot_run",
            "id": "run_44",
            "t": now.isoformat(),
            "data": {"state": "running", "orders_created": 2},
        },
    ]

    if types:
        allowed = {t.strip() for t in types.split(",") if t.strip()}
        map_type = {"orders": "order", "trades": "trade", "alerts": "alert", "bot_runs": "bot_run"}
        allowed_internal = {map_type.get(t, t) for t in allowed}
        items = [item for item in items if item["type"] in allowed_internal]

    if symbol:
        items = [
            item
            for item in items
            if item.get("data", {}).get("symbol", "") == symbol
        ]
    if user_strategy_id:
        items = [
            item
            for item in items
            if item.get("data", {}).get("user_strategy_id", "") == user_strategy_id
        ]

    items = items[:limit]
    next_cursor = None
    if len(items) == limit:
        last = items[-1]
        next_cursor = f"{last['t']}|{last['id']}"

    return {"env": env, "items": items, "next_cursor": next_cursor}
