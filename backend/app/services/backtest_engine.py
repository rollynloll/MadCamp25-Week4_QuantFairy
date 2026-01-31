from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from app.services.data_provider import load_price_series, parse_date, trading_days
from app.services.metrics import compute_drawdown, compute_metrics, compute_returns


@dataclass
class StrategyContext:
    strategy_id: str
    params: Dict[str, Any]
    label: str


def _is_rebalance_day(date_index: int, rebalance: str) -> bool:
    if rebalance == "daily":
        return True
    if rebalance == "weekly":
        return date_index % 5 == 0
    if rebalance == "monthly":
        return date_index % 21 == 0
    return False


def _momentum_weights(
    prices: Dict[str, Dict[str, float]],
    dates: List[str],
    index: int,
    lookback: int,
    top_k: int,
) -> Dict[str, float]:
    if index - lookback < 0:
        return {}
    returns = []
    for ticker, series in prices.items():
        start = series.get(dates[index - lookback])
        end = series.get(dates[index])
        if start and end:
            returns.append((ticker, (end / start) - 1))
    returns.sort(key=lambda x: x[1], reverse=True)
    selected = [t for t, _ in returns[:top_k]]
    if not selected:
        return {}
    weight = 1 / len(selected)
    return {ticker: weight for ticker in selected}


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(abs(w) for w in weights.values())
    if total == 0:
        return weights
    return {k: v / total for k, v in weights.items()}


def _apply_constraints(weights: Dict[str, float], constraints: Dict[str, Any]) -> Dict[str, float]:
    if constraints.get("max_weight_per_symbol") is not None:
        max_w = constraints["max_weight_per_symbol"]
        weights = {k: min(v, max_w) for k, v in weights.items()}
    if constraints.get("min_trade_weight") is not None:
        min_w = constraints["min_trade_weight"]
        weights = {k: v for k, v in weights.items() if abs(v) >= min_w}
    if constraints.get("max_positions") is not None:
        max_pos = constraints["max_positions"]
        sorted_items = sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True)
        weights = dict(sorted_items[:max_pos])
    buffer_pct = constraints.get("cash_buffer_pct")
    if constraints.get("normalize_weights", True):
        weights = _normalize_weights(weights)
        if buffer_pct is not None:
            scale = max(0.0, 1 - buffer_pct)
            weights = {k: v * scale for k, v in weights.items()}
    elif buffer_pct is not None:
        weights = {k: v * (1 - buffer_pct) for k, v in weights.items()}
    return weights


def _mix_weights(
    strategy_weights: Dict[str, Dict[str, float]],
    mix_weights: Dict[str, float],
    constraints: Dict[str, Any],
) -> Dict[str, float]:
    combined: Dict[str, float] = {}
    for strat_id, weights in strategy_weights.items():
        factor = mix_weights.get(strat_id, 0.0)
        for ticker, w in weights.items():
            combined[ticker] = combined.get(ticker, 0.0) + factor * w
    return _apply_constraints(combined, constraints)


def _simulate_portfolio(
    prices: Dict[str, Dict[str, float]],
    dates: List[str],
    rebalance: str,
    fee_bps: float,
    slippage_bps: float,
    weight_fn,
    initial_cash: float,
) -> Tuple[List[Dict[str, float]], float, List[int]]:
    equity = initial_cash
    equity_curve: List[Dict[str, float]] = []
    weights: Dict[str, float] = {}
    turnovers: List[float] = []
    positions_counts: List[int] = []

    for idx, date in enumerate(dates):
        if _is_rebalance_day(idx, rebalance):
            new_weights = weight_fn(idx, date)
            new_weights = _normalize_weights(new_weights)
            turnover = sum(abs(new_weights.get(k, 0.0) - weights.get(k, 0.0)) for k in set(new_weights) | set(weights))
            cost = turnover * (fee_bps + slippage_bps) / 10000
            equity *= 1 - cost
            weights = new_weights
            turnovers.append(turnover)
        else:
            turnovers.append(0.0)

        # compute daily return
        daily_ret = 0.0
        for ticker, w in weights.items():
            series = prices.get(ticker, {})
            prev_price = series.get(dates[idx - 1]) if idx > 0 else None
            price = series.get(date)
            if prev_price and price:
                daily_ret += w * (price / prev_price - 1)
        equity *= (1 + daily_ret)
        positions_counts.append(len([w for w in weights.values() if w != 0]))
        equity_curve.append({"date": date, "equity": equity})

    turnover_pct = sum(turnovers) / max(len(turnovers), 1) * 100
    return equity_curve, turnover_pct, positions_counts


def run_single_backtest(
    spec: Dict[str, Any],
    strategy_ctx: StrategyContext,
    universe: List[str],
    benchmark_curve: List[Dict[str, float]] | None = None,
) -> Dict[str, Any]:
    prices = load_price_series(
        universe,
        spec["period_start"],
        spec["period_end"],
        spec.get("price_field", "adj_close"),
    )
    dates = list(next(iter(prices.values())).keys()) if prices else []
    if not dates:
        empty_curve: List[Dict[str, float]] = []
        return {
            "equity_curve": empty_curve,
            "returns": [],
            "drawdown": [],
            "metrics": compute_metrics(empty_curve, benchmark_curve=benchmark_curve),
            "positions_summary": {"avg_positions": 0, "max_positions": 0},
        }

    params = strategy_ctx.params
    lookback = int(params.get("lookback", 60))
    top_k = int(params.get("top_k", 10))

    def weight_fn(idx: int, date: str) -> Dict[str, float]:
        return _momentum_weights(prices, dates, idx, lookback, top_k)

    equity_curve, turnover_pct, positions_counts = _simulate_portfolio(
        prices,
        dates,
        spec["rebalance"],
        spec["fee_bps"],
        spec["slippage_bps"],
        weight_fn,
        spec.get("initial_cash", 1.0),
    )

    returns = compute_returns(equity_curve)
    drawdown = compute_drawdown(equity_curve)
    metrics = compute_metrics(
        equity_curve, benchmark_curve=benchmark_curve, turnover_pct=turnover_pct
    )
    positions_summary = {
        "avg_positions": sum(positions_counts) / len(positions_counts),
        "max_positions": max(positions_counts),
    }

    return {
        "equity_curve": equity_curve,
        "returns": returns,
        "drawdown": drawdown,
        "metrics": metrics,
        "positions_summary": positions_summary,
    }


def run_ensemble_backtest(
    spec: Dict[str, Any],
    strategies: List[StrategyContext],
    universe: List[str],
    ensemble: Dict[str, Any],
    benchmark_curve: List[Dict[str, float]] | None = None,
) -> Dict[str, Any]:
    prices = load_price_series(
        universe,
        spec["period_start"],
        spec["period_end"],
        spec.get("price_field", "adj_close"),
    )
    dates = list(next(iter(prices.values())).keys()) if prices else []
    if not dates:
        empty_curve: List[Dict[str, float]] = []
        return {
            "equity_curve": empty_curve,
            "returns": [],
            "drawdown": [],
            "metrics": compute_metrics(empty_curve, benchmark_curve=benchmark_curve),
            "positions_summary": {"avg_positions": 0, "max_positions": 0},
        }

    strategy_weight_maps: Dict[str, Dict[str, float]] = {}

    def make_weight_fn(ctx: StrategyContext):
        lookback = int(ctx.params.get("lookback", 60))
        top_k = int(ctx.params.get("top_k", 10))

        def _fn(idx: int, date: str) -> Dict[str, float]:
            return _momentum_weights(prices, dates, idx, lookback, top_k)

        return _fn

    weight_functions = {ctx.strategy_id: make_weight_fn(ctx) for ctx in strategies}

    mix_weights = ensemble.get("weights", {})
    constraints = ensemble.get("constraints", {}) or {}

    def mixed_weight_fn(idx: int, date: str) -> Dict[str, float]:
        strategy_weights: Dict[str, Dict[str, float]] = {}
        for ctx in strategies:
            strategy_weights[ctx.strategy_id] = weight_functions[ctx.strategy_id](idx, date)
        return _mix_weights(strategy_weights, mix_weights, constraints)

    equity_curve, turnover_pct, positions_counts = _simulate_portfolio(
        prices,
        dates,
        spec["rebalance"],
        spec["fee_bps"],
        spec["slippage_bps"],
        mixed_weight_fn,
        spec.get("initial_cash", 1.0),
    )

    results = {
        "equity_curve": equity_curve,
        "returns": compute_returns(equity_curve),
        "drawdown": compute_drawdown(equity_curve),
        "metrics": compute_metrics(
            equity_curve, benchmark_curve=benchmark_curve, turnover_pct=turnover_pct
        ),
        "positions_summary": {
            "avg_positions": sum(positions_counts) / len(positions_counts),
            "max_positions": max(positions_counts),
        },
    }

    return results
