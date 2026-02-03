from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

import pandas as pd
from jsonschema import Draft7Validator

from app.core.errors import APIError
from app.services.data_provider import load_price_series
from app.strategies.validation import StrategyValidationError, validate_target_weights
from app.services.metrics import compute_drawdown, compute_metrics, compute_returns
from app.strategies.base import StrategyContext, StrategySignal
from app.strategies.registry import get_strategy
from app.universes.presets import UNIVERSE_PRESETS


@dataclass
class BacktestRunResult:
    metrics: Dict[str, float]
    equity_curve: List[Dict[str, float]]
    trade_stats: Dict[str, float]
    benchmark: Dict[str, object] | None
    holdings_history: List[Dict[str, object]]


ProgressCallback = Callable[[str, float | None], None]


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


def _apply_entry_cost(
    initial_cash: float,
    fee_bps: float | None,
    slippage_bps: float | None,
) -> float:
    total_bps = (fee_bps or 0.0) + (slippage_bps or 0.0)
    if total_bps <= 0:
        return initial_cash
    return initial_cash * (1 - total_bps / 10000)


def _compute_benchmark_curve(
    price_series: Dict[str, Dict[str, float]],
    symbol: str,
    initial_cash: float,
    fee_bps: float | None = None,
    slippage_bps: float | None = None,
) -> List[Dict[str, float]]:
    series = price_series.get(symbol, {})
    if not series:
        return []
    dates = sorted(series.keys())
    equity = _apply_entry_cost(initial_cash, fee_bps, slippage_bps)
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
    benchmark_initial_cash: float | None = None,
    benchmark_fee_bps: float | None = None,
    benchmark_slippage_bps: float | None = None,
    progress_cb: ProgressCallback | None = None,
) -> BacktestRunResult:
    params = dict(params or {})
    if isinstance(params.get("symbol"), str):
        params["symbol"] = params["symbol"].strip().upper()
    benchmark_symbol_norm = benchmark_symbol.strip().upper() if benchmark_symbol else None
    if benchmark_symbol_norm == "CASH":
        benchmark_symbol_norm = None
    benchmark_param = params.get("benchmark_symbol")
    if isinstance(benchmark_param, str):
        benchmark_param = benchmark_param.strip().upper()
        params["benchmark_symbol"] = benchmark_param
    universe = resolve_universe(params, benchmark_symbol_norm)
    if not universe:
        raise APIError("VALIDATION_ERROR", "Universe is empty", status_code=422)

    target_symbol = params.get("symbol")
    if isinstance(target_symbol, str):
        target_symbol = target_symbol.strip().upper()
    symbols = list(
        {
            *universe,
            *([benchmark_symbol_norm] if benchmark_symbol_norm else []),
            *([benchmark_param] if benchmark_param else []),
            *([target_symbol] if target_symbol else []),
        }
    )
    if progress_cb:
        progress_cb("load_data", None)
    try:
        price_series = load_price_series(symbols, start_date, end_date, "adj_close")
    except Exception as exc:  # noqa: BLE001
        raise APIError(
            "DATA_SOURCE_UNAVAILABLE",
            "Failed to load market prices",
            detail=str(exc),
            status_code=503,
        ) from exc
    if not price_series or all(not series for series in price_series.values()):
        raise APIError(
            "DATA_NOT_FOUND",
            "No market prices found",
            detail=f"{start_date} to {end_date}",
            status_code=404,
        )
    missing_symbols = [s for s, series in price_series.items() if not series]
    if missing_symbols:
        raise APIError(
            "DATA_NOT_FOUND",
            "No market prices for some symbols",
            details=[{"field": "symbols", "reason": s} for s in missing_symbols],
            status_code=404,
        )
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
    available_symbols = (
        prices_df.index.get_level_values("symbol").unique().tolist()
        if "symbol" in prices_df.index.names
        else []
    )
    if target_symbol and target_symbol not in available_symbols:
        preview = ", ".join(available_symbols[:10])
        raise APIError(
            "DATA_NOT_FOUND",
            "Target symbol not in price data",
            detail=f"{target_symbol} not in prices for {start_date} to {end_date}",
            details=[
                {"field": "symbol", "reason": target_symbol},
                {"field": "available_symbols", "reason": preview or "none"},
            ],
            status_code=404,
        )

    price_matrix = prices_df.reset_index().pivot(index="date", columns="symbol", values="adj_close")
    price_matrix = price_matrix.sort_index()
    dates = list(price_matrix.index)

    strategy = get_strategy(entrypoint)
    ctx = StrategyContext(
        my_strategy_id=my_strategy_id,
        user_id=user_id,
        params=params,
        code_version=code_version or "unknown",
    )
    ctx.params = ctx.resolved_params()

    def _rebalance_dates(dates: List[pd.Timestamp], freq: str) -> List[pd.Timestamp]:
        if not dates:
            return []
        if freq == "daily":
            return dates
        selected: List[pd.Timestamp] = []
        prev_marker = None
        for dt in dates:
            marker = None
            if freq == "weekly":
                marker = dt.isocalendar().week
            elif freq == "monthly":
                marker = (dt.year, dt.month)
            else:
                marker = dt
            if marker != prev_marker:
                selected.append(dt)
                prev_marker = marker
        return selected

    def _validation_universe() -> List[str]:
        allowed = set(universe)
        symbol = ctx.params.get("symbol")
        if isinstance(symbol, str) and symbol:
            allowed.add(symbol.upper())
        benchmark = ctx.params.get("benchmark_symbol")
        if isinstance(benchmark, str) and benchmark:
            allowed.add(benchmark.upper())
        return list(allowed)

    def _risk_settings() -> tuple[bool, float, float]:
        if ctx.spec and ctx.spec.risk:
            return (
                ctx.spec.risk.long_only,
                ctx.spec.risk.cash_buffer,
                ctx.spec.risk.max_weight_per_asset,
            )
        return True, 0.0, 1.0

    try:
        if progress_cb:
            progress_cb("signals", None)
        signals: List[StrategySignal] = []
        used_compute_target = False
        if hasattr(strategy, "compute_target_weights") and callable(
            getattr(strategy, "compute_target_weights")
        ):
            used_compute_target = True
            try:
                freq = ctx.params.get("rebalance", "daily")
                if ctx.spec and ctx.spec.rebalance:
                    freq = ctx.spec.rebalance.freq
                rebalance_dates = _rebalance_dates(list(price_matrix.index), str(freq))
                long_only, cash_buffer, max_weight = _risk_settings()
                universe_for_validation = _validation_universe()
                for dt in rebalance_dates:
                    weights = strategy.compute_target_weights(prices_df, ctx, universe, dt)
                    if weights is None:
                        continue
                    try:
                        weights = validate_target_weights(
                            weights,
                            universe_for_validation,
                            long_only=long_only,
                            cash_buffer=cash_buffer,
                            max_weight_per_asset=max_weight,
                        )
                    except StrategyValidationError as exc:
                        raise APIError("VALIDATION_ERROR", str(exc), status_code=422) from exc
                    signals.append(StrategySignal(date=str(dt.date()), target_weights=weights))
            except NotImplementedError:
                used_compute_target = False
        if not used_compute_target:
            long_only, cash_buffer, max_weight = _risk_settings()
            universe_for_validation = _validation_universe()
            for signal in strategy.generate_signals(prices_df, ctx, universe):
                try:
                    cleaned = validate_target_weights(
                        signal.target_weights,
                        universe_for_validation,
                        long_only=long_only,
                        cash_buffer=cash_buffer,
                        max_weight_per_asset=max_weight,
                    )
                except StrategyValidationError as exc:
                    raise APIError("VALIDATION_ERROR", str(exc), status_code=422) from exc
                signals.append(StrategySignal(date=signal.date, target_weights=cleaned))
    except KeyError as exc:
        missing = str(exc.args[0]) if exc.args else "unknown"
        preview = ", ".join(available_symbols[:10])
        raise APIError(
            "DATA_NOT_FOUND",
            "Price data missing for symbol",
            detail=f"{missing} not found in price frame",
            details=[
                {"field": "symbol", "reason": missing},
                {"field": "available_symbols", "reason": preview or "none"},
            ],
            status_code=404,
        ) from exc
    weights: Dict[str, float] = {}
    equity = initial_cash
    equity_curve: List[Dict[str, float]] = []
    turnover_days: List[str] = []

    # price_matrix and dates already computed above
    signal_map = {pd.to_datetime(s.date): s.target_weights for s in signals}

    prev_prices = None
    holdings_history: List[Dict[str, object]] = []
    total = len(dates)
    stride = max(total // 50, 1)
    if progress_cb and total:
        progress_cb("simulate", 0.0)
    for idx, dt in enumerate(dates, start=1):
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
        if total:
            is_month_end = idx == total or dates[idx].to_period("M") != dt.to_period("M")
            if is_month_end:
                snapshot = {k: v for k, v in weights.items() if v != 0}
                holdings_history.append({"month": dt.strftime("%Y-%m"), "weights": snapshot})
        if progress_cb and total:
            if idx % stride == 0 or idx == total:
                progress_cb("simulate", idx / total)

    if progress_cb:
        progress_cb("metrics", None)
    returns = compute_returns(equity_curve)
    drawdown = compute_drawdown(equity_curve)

    benchmark_curve = None
    benchmark_payload = None
    if benchmark_symbol_norm:
        benchmark_cash = benchmark_initial_cash if benchmark_initial_cash is not None else initial_cash
        benchmark_curve = _compute_benchmark_curve(
            price_series,
            benchmark_symbol_norm,
            benchmark_cash,
            fee_bps=benchmark_fee_bps,
            slippage_bps=benchmark_slippage_bps,
        )
        benchmark_payload = {
            "symbol": benchmark_symbol_norm,
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
        holdings_history=holdings_history,
    )
