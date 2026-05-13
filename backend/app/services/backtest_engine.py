from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from app.services.data_provider import load_price_series
from engine.backtest.ensemble import (
    EnsembleStrategyContext,
    SimulationProgressCallback,
    run_ensemble,
    run_single,
)


@dataclass
class StrategyContext:
    strategy_id: str
    params: Dict[str, Any]
    label: str


def run_single_backtest(
    spec: Dict[str, Any],
    strategy_ctx: StrategyContext,
    universe: List[str],
    benchmark_curve: List[Dict[str, float]] | None = None,
    progress_cb: SimulationProgressCallback | None = None,
) -> Dict[str, Any]:
    prices = load_price_series(
        universe,
        spec["period_start"],
        spec["period_end"],
        spec.get("price_field", "adj_close"),
    )
    dates = list(next(iter(prices.values())).keys()) if prices else []
    engine_ctx = EnsembleStrategyContext(
        strategy_id=strategy_ctx.strategy_id,
        params=strategy_ctx.params,
        label=strategy_ctx.label,
    )
    return run_single(prices, dates, spec, engine_ctx, benchmark_curve, progress_cb)


def run_ensemble_backtest(
    spec: Dict[str, Any],
    strategies: List[StrategyContext],
    universe: List[str],
    ensemble: Dict[str, Any],
    benchmark_curve: List[Dict[str, float]] | None = None,
    progress_cb: SimulationProgressCallback | None = None,
) -> Dict[str, Any]:
    prices = load_price_series(
        universe,
        spec["period_start"],
        spec["period_end"],
        spec.get("price_field", "adj_close"),
    )
    dates = list(next(iter(prices.values())).keys()) if prices else []
    engine_ctxs = [
        EnsembleStrategyContext(
            strategy_id=ctx.strategy_id,
            params=ctx.params,
            label=ctx.label,
        )
        for ctx in strategies
    ]
    return run_ensemble(prices, dates, spec, engine_ctxs, ensemble, benchmark_curve, progress_cb)
