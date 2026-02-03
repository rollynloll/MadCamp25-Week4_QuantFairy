from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Query

from app.alpaca.client import AlpacaAccount, AlpacaClient
from app.core.config import get_settings
from app.core.errors import APIError
from app.core.ttl_cache import TTLCache
from app.core.time import now_kst
from app.schemas.portfolio import (
    ActivityItem,
    PortfolioActivityResponse,
    PortfolioAllocationResponse,
    PortfolioAttributionResponse,
    PortfolioDrawdownResponse,
    PortfolioKpiResponse,
    PortfolioOverviewResponse,
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
from app.storage.positions_repo import PositionsRepository
from app.storage.strategies_repo import StrategiesRepository
from app.storage.user_settings_repo import UserSettingsRepository


router = APIRouter()

EnvLiteral = Literal["paper", "live"]
SideLiteral = Literal["all", "long", "short"]
SortLiteral = Literal["pnl", "pnl_pct", "value", "symbol"]
OrderLiteral = Literal["asc", "desc"]
AttributionByLiteral = Literal["strategy", "sector"]

ACCOUNT_CACHE_TTL = 10.0
POSITIONS_CACHE_TTL = 10.0
HISTORY_CACHE_TTL = 15.0
ALPACA_CACHE = TTLCache(default_ttl=10.0, maxsize=256)


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


def _cache_key(prefix: str, env: str, *parts: str) -> str:
    suffix = ":".join(parts) if parts else ""
    return f"{prefix}:{env}:{suffix}"


def _get_account_cached(client: AlpacaClient):
    key = _cache_key("alpaca:account", client.environment)
    cached = ALPACA_CACHE.get(key)
    if cached is not None:
        return cached
    result = client.get_account()
    if result.account is not None:
        ALPACA_CACHE.set(key, result, ttl=ACCOUNT_CACHE_TTL)
    return result


def _get_positions_cached(client: AlpacaClient):
    key = _cache_key("alpaca:positions", client.environment)
    cached = ALPACA_CACHE.get(key)
    if cached is not None:
        return cached
    result = client.get_positions()
    if result is not None:
        ALPACA_CACHE.set(key, result, ttl=POSITIONS_CACHE_TTL)
    return result


def _get_history_cached(client: AlpacaClient, period: str | None, timeframe: str | None):
    key = _cache_key(
        "alpaca:history",
        client.environment,
        period or "default",
        timeframe or "default",
    )
    cached = ALPACA_CACHE.get(key)
    if cached is not None:
        return cached
    result = client.get_portfolio_history(period=period, timeframe=timeframe)
    if result is not None:
        ALPACA_CACHE.set(key, result, ttl=HISTORY_CACHE_TTL)
    return result


def _require_account(client: AlpacaClient):
    result = _get_account_cached(client)
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


def _normalize_position_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in rows:
        symbol = str(row.get("symbol") or row.get("ticker") or "").upper()
        if not symbol:
            continue
        qty = _to_float(row.get("qty", row.get("quantity", 0)))
        side = str(row.get("side") or "").lower()
        if side not in {"long", "short"}:
            side = "short" if qty < 0 else "long"
        qty = abs(qty)
        avg_entry_price = _to_float(
            row.get("avg_entry_price", row.get("avg_price", row.get("average_price", 0)))
        )
        current_price = _to_float(
            row.get("current_price", row.get("price", row.get("last_price", 0)))
        )
        market_value = _to_float(
            row.get("market_value", current_price * qty)
        )
        pnl_value = _to_float(
            row.get(
                "unrealized_pnl",
                row.get("unrealized_pl", row.get("pnl_value", 0)),
            )
        )
        pnl_pct = _to_pct(
            row.get(
                "unrealized_pnl_pct",
                row.get("unrealized_plpc", row.get("pnl_pct", 0)),
            )
        )
        strategy_id = (
            row.get("strategy_id")
            or row.get("user_strategy_id")
            or row.get("my_strategy_id")
            or "unassigned"
        )
        strategy_name = (
            row.get("strategy_name")
            or row.get("strategy_label")
            or row.get("strategy")
            or "Unassigned"
        )
        items.append(
            {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "avg_entry_price": avg_entry_price,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": {"value": pnl_value, "pct": pnl_pct},
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


def _aggregate_position_values(
    positions: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}
    for pos in positions:
        if pos.get("side") == "short":
            raise APIError(
                "SHORT_POSITIONS_NOT_SUPPORTED",
                "Rebalance does not support short positions yet",
                status_code=422,
            )
        strategy_id = pos["strategy"]["user_strategy_id"]
        group = grouped.setdefault(
            strategy_id,
            {"value": 0.0, "positions": []},
        )
        value = abs(_to_float(pos.get("market_value", 0.0)))
        group["value"] += value
        group["positions"].append({**pos, "abs_value": value})
    return grouped


def _build_rebalance_orders(
    *,
    equity: float,
    positions: List[Dict[str, Any]],
    target_weights: Dict[str, float],
    target_cash_pct: float,
    min_notional: float = 1.0,
) -> List[Dict[str, Any]]:
    if equity <= 0:
        return []
    grouped = _aggregate_position_values(positions)
    cleaned_weights: Dict[str, float] = {}
    for key, raw in target_weights.items():
        try:
            weight = float(raw)
        except (TypeError, ValueError):
            continue
        if weight < 0:
            raise APIError(
                "VALIDATION_ERROR",
                f"Negative weight not allowed: {key}",
                status_code=422,
            )
        cleaned_weights[str(key)] = weight

    investable_pct = max(0.0, 100.0 - target_cash_pct)
    total_target = sum(cleaned_weights.values())
    if total_target <= 0:
        return []
    scale = 1.0
    if total_target > investable_pct and investable_pct > 0:
        scale = investable_pct / total_target

    symbol_deltas: Dict[str, Dict[str, Any]] = {}
    for strategy_id, weight_pct in cleaned_weights.items():
        if weight_pct <= 0:
            continue
        current = grouped.get(strategy_id)
        current_value = current["value"] if current else 0.0
        if current_value <= 0:
            raise APIError(
                "VALIDATION_ERROR",
                f"No positions for strategy {strategy_id}",
                status_code=422,
            )
        target_value = equity * (weight_pct * scale / 100.0)
        for pos in current["positions"]:
            abs_value = pos["abs_value"]
            if abs_value <= 0:
                continue
            price = _to_float(pos.get("current_price", 0.0))
            if price <= 0:
                continue
            target_pos_value = target_value * abs_value / current_value
            delta_value = target_pos_value - abs_value
            if abs(delta_value) < min_notional:
                continue
            entry = symbol_deltas.setdefault(
                pos["symbol"],
                {"symbol": pos["symbol"], "delta_value": 0.0, "price": price},
            )
            entry["delta_value"] += delta_value

    orders: List[Dict[str, Any]] = []
    for entry in symbol_deltas.values():
        delta = entry["delta_value"]
        if abs(delta) < min_notional:
            continue
        side = "buy" if delta > 0 else "sell"
        price = entry["price"]
        qty = abs(delta) / price if price > 0 else 0.0
        if qty <= 0:
            continue
        orders.append(
            {
                "symbol": entry["symbol"],
                "side": side,
                "qty": qty,
                "notional": abs(delta),
                "estimated_price": price,
            }
        )
    return orders


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
    raw_positions = _get_positions_cached(client)
    if raw_positions is None:
        return []
    return _normalize_positions(raw_positions)


def _build_summary_response(
    *,
    env: EnvLiteral,
    account: AlpacaAccount,
    latency_ms: int,
    raw_positions: List[Any],
    positions: List[Dict[str, Any]],
    user_settings: Dict[str, Any],
) -> Dict[str, Any]:
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


def _build_allocation_response(
    *,
    env: EnvLiteral,
    account: AlpacaAccount,
    positions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    exposure = _positions_exposure(positions, account.equity, account.cash)
    return {
        "env": env,
        "by_sector": [],
        "by_strategy": [],
        "exposure": exposure,
    }


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
    raw_positions = _get_positions_cached(client) or []
    positions = _normalize_positions(raw_positions)
    settings_repo = UserSettingsRepository(settings)
    user_settings = settings_repo.get_or_create(_resolve_user_id())
    return _build_summary_response(
        env=env,
        account=account,
        latency_ms=latency_ms,
        raw_positions=raw_positions,
        positions=positions,
        user_settings=user_settings,
    )


@router.get(
    "/portfolio/overview",
    response_model=PortfolioOverviewResponse,
    summary="Portfolio overview",
)
async def get_portfolio_overview(
    env: EnvLiteral = Query(..., description="paper or live"),
):
    settings = get_settings()
    client = AlpacaClient(settings, env)
    account, latency_ms = _require_account(client)
    raw_positions = _get_positions_cached(client) or []
    positions = _normalize_positions(raw_positions)
    settings_repo = UserSettingsRepository(settings)
    user_settings = settings_repo.get_or_create(_resolve_user_id())

    summary = _build_summary_response(
        env=env,
        account=account,
        latency_ms=latency_ms,
        raw_positions=raw_positions,
        positions=positions,
        user_settings=user_settings,
    )
    allocation = _build_allocation_response(
        env=env,
        account=account,
        positions=positions,
    )
    return {"env": env, "as_of": summary["as_of"], "summary": summary, "allocation": allocation}


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

    history = _get_history_cached(
        client,
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

    history = _get_history_cached(
        client,
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

    history = _get_history_cached(
        client,
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
    user_id = _resolve_user_id()
    repo = PositionsRepository(settings)
    rows = repo.list(
        user_id,
        env,
        q=q,
        side=side,
        strategy_id=strategy_id,
        sort=sort,
        order=order,
        limit=200,
    )
    items = _normalize_position_rows(rows)
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
    return _build_allocation_response(env=env, account=account, positions=positions)


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
        if row.get("environment") and row.get("environment") != env:
            continue
        risk = row.get("risk_limits") or {}
        state = row.get("state", "stopped")
        if state not in {"running", "paused", "stopped"}:
            state = "stopped"
        items.append(
            {
                "user_strategy_id": row.get("strategy_id") or row.get("user_strategy_id"),
                "name": row.get("name", ""),
                "public_strategy_id": row.get("source_public_strategy_id", ""),
                "state": state,
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
    state = row.get("state", "stopped")
    if state not in {"running", "paused", "stopped"}:
        state = "stopped"
    return {
        "env": env,
        "user_strategy_id": row.get("strategy_id") or user_strategy_id,
        "name": row.get("name", ""),
        "state": state,
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
    if not payload.target_weights:
        raise APIError(
            "VALIDATION_ERROR",
            "target_weights required",
            status_code=422,
        )

    settings = get_settings()
    if env == "live" and not settings.allow_live_trading:
        raise APIError(
            "LIVE_TRADING_DISABLED",
            "Live trading is disabled",
            "Set ALLOW_LIVE_TRADING=true to enable",
            status_code=403,
        )

    user_id = _resolve_user_id()
    settings_repo = UserSettingsRepository(settings)
    user_settings = settings_repo.get_or_create(user_id)
    if user_settings.get("kill_switch", False):
        raise APIError(
            "KILL_SWITCH_ON",
            "Kill switch is enabled",
            "Disable kill switch to rebalance",
            status_code=403,
        )

    client = AlpacaClient(settings, env)
    account, _ = _require_account(client)

    positions_repo = PositionsRepository(settings)
    rows = positions_repo.list(user_id, env, limit=500)
    positions = _normalize_position_rows(rows)

    target_weights = payload.target_weights or {}
    if payload.strategy_ids:
        target_weights = {
            key: val for key, val in target_weights.items() if key in payload.strategy_ids
        }
    if not target_weights:
        raise APIError(
            "VALIDATION_ERROR",
            "No target weights for selected strategies",
            status_code=422,
        )

    target_cash_pct = (
        payload.target_cash_pct
        if payload.target_cash_pct is not None
        else (account.cash / account.equity * 100 if account.equity else 0.0)
    )

    orders = _build_rebalance_orders(
        equity=account.equity,
        positions=positions,
        target_weights=target_weights,
        target_cash_pct=target_cash_pct,
    )

    if payload.mode == "execute":
        for order in orders:
            client.submit_market_order(
                symbol=order["symbol"],
                side=order["side"],
                qty=order["qty"],
                time_in_force="day",
            )

    rebalance_id = f"rb_{now_kst().strftime('%Y%m%d_%H%M%S')}"
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
