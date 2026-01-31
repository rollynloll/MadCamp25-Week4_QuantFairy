from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd
from jsonschema import Draft7Validator

from app.core.errors import APIError
from app.services.data_provider import load_price_series
from app.services.metrics import compute_drawdown, compute_metrics, compute_returns
from app.strategies.base import StrategyContext
from app.strategies.registry import get_strategy
from app.universes.presets import UNIVERSE_PRESETS


@dataclass
class BacktestRunResult:
    metrics: Dict[str, float]
    equity_curve: List[Dict[str, float]]
    trade_stats: Dict[str, float]
    benchmark: Dict[str, object] | None


def resolve_universe(params: Dict, benchmark_symbol: str | None) -> List[str]:
    universe = params.get("universe")
    if isinstance(universe, list) and universe:
        return [str(s).upper() for s in universe]

    preset = params.get("universe_preset")
    if isinstance(preset, str) and preset in UNIVERSE_PRESETS:
        return UNIVERSE_PRESETS[preset]["tickers"]

    symbol = params.get("symbol")
    if symbol:
        return [str(symbol).upper()]

    if benchmark_symbol:
        return [str(benchmark_symbol).upper()]

    return UNIVERSE_PRESETS.get("US_CORE_20", {}).get("tickers", [])


def validate_params(param_schema: Dict, params: Dict) -> None:
    if not param_schema:
        return
    validator = Draft7Validator(param_schema)
    errors = []
    for error in validator.iter_errors(params):
        field = ".".join([str(p) for p in error.path])
        errors.append({"field": field, "reason": error.message})
    if errors:
        raise APIError("VALIDATION_ERROR", "Invalid params", details=errors, status_code=422)


def build_price_frame(price_series: Dict[str, Dict[str, float]]) -> pd.DataFrame:
    rows = []
    for symbol, series in price_series.items():
        for date, price in series.items():
            rows.append({"date": date, "symbol": symbol, "adj_close": price})
    if not rows:
        return pd.DataFrame(columns=["date", "symbol", "adj_close"]).set_index(["date", "symbol"])
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index(["date", "symbol"]).sort_index()
    return df


def _compute_benchmark_curve(
    price_series: Dict[str, Dict[str, float]],
    symbol: str,
    initial_cash: float,
) -> List[Dict[str, float]]:
    series = price_series.get(symbol, {})
    if not series:
        return []
    dates = sorted(series.keys())
    equity = initial_cash
    curve: List[Dict[str, float]] = []
    prev_price = None
    for date in dates:
        price = series.get(date)
        if prev_price is not None and price:
            equity *= price / prev_price
        curve.append({"date": date, "equity": equity})
        prev_price = price
    return curve


def run_backtest(
    *,
    my_strategy_id: str,
    user_id: str,
    params: Dict,
    entrypoint: str,
    code_version: str,
    start_date: str,
    end_date: str,
    benchmark_symbol: str | None,
    initial_cash: float,
    fee_bps: float,
    slippage_bps: float,
) -> BacktestRunResult:
    universe = resolve_universe(params, benchmark_symbol)
    if not universe:
        raise APIError("VALIDATION_ERROR", "Universe is empty", status_code=422)

    symbols = list({*universe, *( [benchmark_symbol] if benchmark_symbol else [] )})
    price_series = load_price_series(symbols, start_date, end_date, "adj_close")
    if not price_series or all(not series for series in price_series.values()):
        raise APIError(
            "DATA_NOT_FOUND",
            "No market prices found",
            detail=f"{start_date} to {end_date}",
            status_code=404,
        )
    target_symbol = params.get("symbol")
    if target_symbol and not price_series.get(str(target_symbol).upper(), {}):
        raise APIError(
            "DATA_NOT_FOUND",
            f"No prices for symbol {target_symbol}",
            detail=f"{start_date} to {end_date}",
            status_code=404,
        )
    prices_df = build_price_frame(price_series)
    if prices_df.empty:
        raise APIError(
            "DATA_NOT_FOUND",
            "No market prices found",
            detail=f"{start_date} to {end_date}",
            status_code=404,
        )

    strategy = get_strategy(entrypoint)
    ctx = StrategyContext(
        my_strategy_id=my_strategy_id,
        user_id=user_id,
        params=params,
        code_version=code_version or "unknown",
    )

    signals = list(strategy.generate_signals(prices_df, ctx, universe))
    weights: Dict[str, float] = {}
    equity = initial_cash
    equity_curve: List[Dict[str, float]] = []
    turnover_days: List[str] = []

    price_matrix = prices_df.reset_index().pivot(index="date", columns="symbol", values="adj_close")
    dates = list(price_matrix.index)
    signal_map = {pd.to_datetime(s.date): s.target_weights for s in signals}

    prev_prices = None
    for dt in dates:
        if dt in signal_map:
            new_weights = signal_map[dt]
            turnover = sum(abs(new_weights.get(k, 0.0) - weights.get(k, 0.0)) for k in set(new_weights) | set(weights))
            cost = turnover * (fee_bps + slippage_bps) / 10000
            equity *= 1 - cost
            weights = new_weights
            if turnover > 0:
                turnover_days.append(str(dt.date()))

        if prev_prices is not None:
            daily_ret = 0.0
            for symbol, w in weights.items():
                if symbol not in price_matrix.columns:
                    continue
                prev_price = prev_prices.get(symbol)
                price = price_matrix.loc[dt].get(symbol)
                if prev_price and price:
                    daily_ret += w * (price / prev_price - 1)
            equity *= (1 + daily_ret)

        equity_curve.append({"date": str(dt.date()), "equity": equity})
        prev_prices = price_matrix.loc[dt]

    returns = compute_returns(equity_curve)
    drawdown = compute_drawdown(equity_curve)

    benchmark_curve = None
    benchmark_payload = None
    if benchmark_symbol:
        benchmark_curve = _compute_benchmark_curve(price_series, benchmark_symbol, initial_cash)
        benchmark_payload = {
            "symbol": benchmark_symbol,
            "metrics": compute_metrics(benchmark_curve),
            "equity_curve": benchmark_curve,
            "returns": compute_returns(benchmark_curve),
            "drawdown": compute_drawdown(benchmark_curve),
        }

    metrics = compute_metrics(equity_curve, benchmark_curve=benchmark_curve)

    avg_hold_days = 0.0
    if len(turnover_days) > 1:
        hold_spans = []
        for i in range(1, len(turnover_days)):
            delta = pd.to_datetime(turnover_days[i]) - pd.to_datetime(turnover_days[i - 1])
            hold_spans.append(delta.days)
        avg_hold_days = sum(hold_spans) / len(hold_spans)

    trade_stats = {
        "trades_count": len(turnover_days),
        "avg_hold_days": avg_hold_days,
    }

    return BacktestRunResult(
        metrics=metrics,
        equity_curve=equity_curve,
        trade_stats=trade_stats,
        benchmark=benchmark_payload,
    )
