from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Query

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


def _dummy_equity_curve(range_value: RangeLiteral) -> List[Dict[str, Any]]:
    now = now_kst().date()
    days = _range_days(range_value)
    step = max(days // 4, 1)
    points = []
    equity = 100000.0
    for offset in range(0, days + 1, step):
        day = now - timedelta(days=days - offset)
        equity += 120.5
        points.append({"t": day.isoformat(), "equity": round(equity, 2)})
        if len(points) >= 5:
            break
    return points


def _dummy_benchmark_curve(range_value: RangeLiteral) -> List[Dict[str, Any]]:
    now = now_kst().date()
    days = _range_days(range_value)
    step = max(days // 4, 1)
    points = []
    price = 480.0
    for offset in range(0, days + 1, step):
        day = now - timedelta(days=days - offset)
        price += 1.1
        points.append({"t": day.isoformat(), "price": round(price, 2)})
        if len(points) >= 5:
            break
    return points


def _dummy_positions() -> List[Dict[str, Any]]:
    return [
        {
            "symbol": "AAPL",
            "qty": 12.0,
            "side": "long",
            "avg_entry_price": 190.1,
            "current_price": 195.2,
            "market_value": 2342.4,
            "unrealized_pnl": {"value": 61.2, "pct": 2.68},
            "strategy": {"user_strategy_id": "us_123", "name": "Momentum Top10"},
        },
        {
            "symbol": "MSFT",
            "qty": 8.0,
            "side": "long",
            "avg_entry_price": 370.0,
            "current_price": 368.5,
            "market_value": 2948.0,
            "unrealized_pnl": {"value": -12.0, "pct": -0.41},
            "strategy": {"user_strategy_id": "us_456", "name": "Low Volatility"},
        },
        {
            "symbol": "TSLA",
            "qty": 4.0,
            "side": "long",
            "avg_entry_price": 210.0,
            "current_price": 225.0,
            "market_value": 900.0,
            "unrealized_pnl": {"value": 60.0, "pct": 7.14},
            "strategy": {"user_strategy_id": "us_123", "name": "Momentum Top10"},
        },
    ]


def _dummy_user_strategies() -> List[Dict[str, Any]]:
    now = now_kst().isoformat()
    return [
        {
            "user_strategy_id": "us_123",
            "name": "Momentum Top10",
            "public_strategy_id": "ps_001",
            "state": "running",
            "positions_count": 8,
            "today_pnl": {"value": 83.2, "pct": 0.08},
            "last_run_at": now,
            "params": {"lookback_days": 63, "top_k": 10},
            "risk_limits": {"max_weight_per_asset": 0.15, "cash_buffer": 0.02},
        },
        {
            "user_strategy_id": "us_456",
            "name": "Low Volatility",
            "public_strategy_id": "ps_010",
            "state": "paused",
            "positions_count": 5,
            "today_pnl": {"value": 12.4, "pct": 0.02},
            "last_run_at": now,
            "params": {"lookback_days": 60, "top_k": 10},
            "risk_limits": {"max_weight_per_asset": 0.2, "cash_buffer": 0.05},
        },
    ]


@router.get(
    "/portfolio/summary",
    response_model=PortfolioSummaryResponse,
    summary="Portfolio summary",
)
async def get_portfolio_summary(
    env: EnvLiteral = Query(..., description="paper or live"),
):
    # TODO: Replace dummy values with real account + broker data.
    settings = get_settings()
    user_id = _resolve_user_id()
    settings_repo = UserSettingsRepository(settings)
    user_settings = settings_repo.get_or_create(user_id)
    now = now_kst().isoformat()
    return {
        "env": env,
        "as_of": now,
        "mode": {"environment": env, "kill_switch": bool(user_settings.get("kill_switch", False))},
        "status": {
            "broker": {"state": "up", "latency_ms": 120},
            "worker": {"state": "running", "last_heartbeat_at": now},
        },
        "account": {
            "equity": 102345.12,
            "cash": 24567.89,
            "buying_power": 49000.0,
            "today_pnl": {"value": 123.45, "pct": 0.12},
            "open_positions": {"count": 8, "long": 8, "short": 0},
        },
        "exposure": {
            "net_pct": 78.2,
            "gross_pct": 78.2,
            "cash_pct": 21.8,
            "top5_concentration_pct": 44.1,
        },
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
    # TODO: Use stored equity curve + market data for benchmark.
    _ = downsample
    now = now_kst().isoformat()
    return {
        "env": env,
        "range": range,
        "benchmark": benchmark,
        "as_of": now,
        "equity_curve": _dummy_equity_curve(range),
        "benchmark_curve": _dummy_benchmark_curve(range),
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
    # TODO: Compute drawdown from equity curve.
    curve = _dummy_equity_curve(range)
    drawdowns = []
    peak = curve[0]["equity"] if curve else 0.0
    max_dd = 0.0
    for point in curve:
        equity = point["equity"]
        if equity > peak:
            peak = equity
        drawdown = ((equity - peak) / peak * 100) if peak else 0.0
        if drawdown < max_dd:
            max_dd = drawdown
        drawdowns.append({"t": point["t"], "drawdown_pct": round(drawdown, 2)})
    current_dd = drawdowns[-1]["drawdown_pct"] if drawdowns else 0.0
    return {
        "env": env,
        "range": range,
        "drawdown_curve": drawdowns,
        "summary": {"current_drawdown_pct": current_dd, "max_drawdown_pct": max_dd},
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
    # TODO: Calculate KPI from returns.
    return {
        "env": env,
        "range": range,
        "kpi": {
            "period_return_pct": 2.34,
            "cagr_pct": 18.2,
            "volatility_pct": 12.4,
            "sharpe": 1.35,
            "max_drawdown_pct": -4.8,
            "win_rate_pct": 54.0,
        },
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
    # TODO: Load positions from broker/storage.
    items = _dummy_positions()
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
    # TODO: Compute allocation by sector and strategy.
    return {
        "env": env,
        "by_sector": [
            {"sector": "Technology", "value": 32000.0, "pct": 31.3, "pnl_value": 420.0},
            {"sector": "Healthcare", "value": 18000.0, "pct": 17.6, "pnl_value": 90.0},
        ],
        "by_strategy": [
            {
                "user_strategy_id": "us_123",
                "name": "Momentum Top10",
                "value": 45000.0,
                "pct": 44.0,
                "pnl_value": 380.0,
            },
            {
                "user_strategy_id": "us_456",
                "name": "Low Volatility",
                "value": 22000.0,
                "pct": 21.5,
                "pnl_value": 120.0,
            },
        ],
        "exposure": {
            "net_pct": 78.2,
            "gross_pct": 78.2,
            "cash_pct": 21.8,
            "top5_concentration_pct": 44.1,
        },
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
    # TODO: Calculate attribution from positions and PnL.
    if by == "strategy":
        items = [
            {
                "key": "us_123",
                "label": "Momentum Top10",
                "exposure_pct": 44.0,
                "unrealized_pnl_value": 380.0,
                "period_contribution_pct": 1.02,
            },
            {
                "key": "us_456",
                "label": "Low Volatility",
                "exposure_pct": 21.5,
                "unrealized_pnl_value": 120.0,
                "period_contribution_pct": 0.42,
            },
        ]
    else:
        items = [
            {
                "key": "Technology",
                "label": "Technology",
                "exposure_pct": 31.3,
                "unrealized_pnl_value": 420.0,
                "period_contribution_pct": 0.95,
            },
            {
                "key": "Healthcare",
                "label": "Healthcare",
                "exposure_pct": 17.6,
                "unrealized_pnl_value": 90.0,
                "period_contribution_pct": 0.21,
            },
        ]

    return {"env": env, "range": range, "by": by, "items": items}


@router.get(
    "/user-strategies",
    response_model=UserStrategiesResponse,
    summary="List user strategies",
)
async def list_user_strategies(
    env: EnvLiteral = Query(..., description="paper or live"),
):
    # TODO: Replace with persistent storage.
    return {"env": env, "items": _dummy_user_strategies()}


@router.get(
    "/user-strategies/{user_strategy_id}",
    response_model=UserStrategyDetailResponse,
    summary="User strategy detail",
)
async def get_user_strategy(
    user_strategy_id: str,
    env: EnvLiteral = Query(..., description="paper or live"),
):
    # TODO: Load from storage.
    strategies = _dummy_user_strategies()
    match = next((s for s in strategies if s["user_strategy_id"] == user_strategy_id), None)
    if match is None:
        raise APIError("NOT_FOUND", "User strategy not found", status_code=404)
    now = now_kst().isoformat()
    return {
        "env": env,
        "user_strategy_id": match["user_strategy_id"],
        "name": match["name"],
        "state": match["state"],
        "public_strategy": {
            "public_strategy_id": match["public_strategy_id"],
            "name": match["name"],
            "one_liner": "Buy top-K strongest performers",
            "param_schema": {
                "lookback_days": {"type": "int", "default": 63, "min": 20, "max": 252},
                "top_k": {"type": "int", "default": 10, "min": 1, "max": 50},
            },
        },
        "params": match["params"],
        "risk_limits": {
            "max_weight_per_asset": match["risk_limits"]["max_weight_per_asset"],
            "cash_buffer": match["risk_limits"]["cash_buffer"],
            "max_turnover_pct": 30,
        },
        "recent_runs": [
            {"run_id": "br_100", "started_at": now, "status": "success", "orders_created": 3}
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
    # TODO: Persist updates to storage.
    _ = env
    strategies = _dummy_user_strategies()
    match = next((s for s in strategies if s["user_strategy_id"] == user_strategy_id), None)
    if match is None:
        raise APIError("NOT_FOUND", "User strategy not found", status_code=404)
    if payload.name is None and payload.params is None and payload.risk_limits is None:
        raise APIError("VALIDATION_ERROR", "No fields to update", status_code=422)
    return {
        "ok": True,
        "user_strategy_id": user_strategy_id,
        "updated_at": now_kst().isoformat(),
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
    # TODO: Persist strategy state in storage.
    _ = env
    state_map = {"start": "running", "pause": "paused", "stop": "stopped"}
    return {
        "ok": True,
        "user_strategy_id": user_strategy_id,
        "state": state_map[payload.action],
    }


@router.post(
    "/bot/kill-switch",
    response_model=KillSwitchResponse,
    summary="Toggle kill switch",
)
async def set_kill_switch(
    payload: KillSwitchRequest,
    env: EnvLiteral = Query(..., description="paper or live"),
):
    # TODO: Update kill switch per environment.
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
    # TODO: Generate orders from live portfolio + targets.
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
    # TODO: Load activity from storage with real pagination.
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
