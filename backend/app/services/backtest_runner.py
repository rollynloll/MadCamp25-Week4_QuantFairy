from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

import pandas as pd
from jsonschema import Draft7Validator

from app.core.errors import APIError
from app.services.data_provider import load_price_series
from app.strategies.sandbox import PYTHON_ENTRYPOINT, PYTHON_META_KEY, extract_python_body
from app.strategies.registry import get_strategy
from app.universes.presets import UNIVERSE_PRESETS
from engine.backtest import runner as _engine_runner
from engine.errors import DataNotFoundError, DataSourceError, StrategyError
from app.strategies.base import StrategyContext as _EngineCtx


@dataclass
class BacktestRunResult:
    metrics: Dict[str, float]
    equity_curve: List[Dict[str, float]]
    trade_stats: Dict[str, float]
    benchmark: Dict | None
    holdings_history: List[Dict]


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


class _DataProviderAdapter:
    """load_price_series(Supabase/mock) → engine DataProvider 프로토콜 어댑터."""

    def __init__(self, price_field: str = "adj_close"):
        self._price_field = price_field

    def get_prices(self, tickers: List[str], start: str, end: str) -> pd.DataFrame:
        series_dict = load_price_series(tickers, start, end, self._price_field)
        if not series_dict:
            return pd.DataFrame()
        df = pd.DataFrame(series_dict)
        df.index = pd.to_datetime(df.index)
        df.index.name = "date"
        return df.sort_index()


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
    python_body = None
    if entrypoint == PYTHON_ENTRYPOINT or PYTHON_META_KEY in params:
        params, python_body = extract_python_body(params)
        if not python_body:
            raise APIError("VALIDATION_ERROR", "Python strategy spec missing", status_code=422)
        entrypoint = PYTHON_ENTRYPOINT

    if isinstance(params.get("symbol"), str):
        params["symbol"] = params["symbol"].strip().upper()

    benchmark_norm = benchmark_symbol.strip().upper() if benchmark_symbol else None
    if benchmark_norm == "CASH":
        benchmark_norm = None

    universe = resolve_universe(params, benchmark_norm)
    if not universe:
        raise APIError("VALIDATION_ERROR", "Universe is empty", status_code=422)

    ctx = _EngineCtx(
        my_strategy_id=my_strategy_id,
        user_id=user_id,
        params=params,
        code_version=code_version or "unknown",
    )
    ctx.params = ctx.resolved_params()

    strategy = None if python_body else get_strategy(entrypoint)

    try:
        result = _engine_runner.run(
            strategy=strategy,
            data_provider=_DataProviderAdapter(params.get("price_field", "adj_close")),
            ctx=ctx,
            universe=universe,
            start_date=start_date,
            end_date=end_date,
            benchmark_symbol=benchmark_norm,
            initial_cash=initial_cash,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            benchmark_initial_cash=benchmark_initial_cash,
            benchmark_fee_bps=benchmark_fee_bps,
            benchmark_slippage_bps=benchmark_slippage_bps,
            python_body=python_body,
            progress_cb=progress_cb,
        )
    except DataNotFoundError as exc:
        raise APIError("DATA_NOT_FOUND", "No market prices found", detail=str(exc), status_code=404) from exc
    except DataSourceError as exc:
        raise APIError("DATA_SOURCE_UNAVAILABLE", "Failed to load market prices", detail=str(exc), status_code=503) from exc
    except StrategyError as exc:
        raise APIError("STRATEGY_EXECUTION_ERROR", str(exc), status_code=422) from exc

    return BacktestRunResult(
        metrics=result.metrics,
        equity_curve=result.equity_curve,
        trade_stats=result.trade_stats,
        benchmark=result.benchmark,
        holdings_history=result.holdings_history,
    )
