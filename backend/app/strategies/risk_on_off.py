from __future__ import annotations

from typing import Dict, List

import pandas as pd

from app.strategies.base import Strategy, StrategyContext


def _price_matrix(prices: pd.DataFrame, universe: List[str], ctx: StrategyContext) -> pd.DataFrame:
    cache_key = "price_matrix"
    cached = ctx.state.get(cache_key)
    if cached is not None:
        return cached
    df = prices.reset_index().pivot(index="date", columns="symbol", values="adj_close")
    df = df.sort_index()
    df = df[[s for s in universe if s in df.columns]]
    ctx.state[cache_key] = df
    return df


class RiskOnOffStrategy(Strategy):
    """Risk-on / risk-off regime rotation.

    Strengths: attempts to sidestep drawdowns.
    Weaknesses: whipsaws in sideways markets.
    Failure: false regime signals.
    """

    name = "Risk-On / Risk-Off"

    def required_columns(self) -> List[str]:
        return ["adj_close"]

    def compute_target_weights(
        self,
        prices: pd.DataFrame,
        ctx: StrategyContext,
        universe: List[str],
        dt: pd.Timestamp,
    ) -> Dict[str, float]:
        params = ctx.resolved_params()
        benchmark_symbol = str(params.get("benchmark_symbol", "SPY")).upper()
        sma_window = int(params.get("sma_window", 200))
        lookback = int(params.get("lookback_days", 126))
        top_k = int(params.get("top_k", 10))

        price_mat = _price_matrix(prices, universe, ctx)
        if dt not in price_mat.index:
            return {}
        idx = price_mat.index.get_loc(dt)
        if idx < sma_window:
            return {}

        benchmark_series = prices.xs(benchmark_symbol, level=1)["adj_close"]
        benchmark_series = benchmark_series.sort_index()
        if dt not in benchmark_series.index:
            return {}

        sma = benchmark_series.rolling(sma_window).mean()
        risk_on = benchmark_series.loc[dt] > sma.loc[dt]
        if not risk_on:
            return {}

        if idx < lookback:
            return {}
        returns = price_mat.pct_change(periods=lookback).iloc[idx]
        returns = returns.dropna()
        if returns.empty:
            return {}
        top = returns.sort_values(ascending=False).index[:top_k].tolist()
        if not top:
            return {}
        weight = 1.0 / len(top)
        return {symbol: weight for symbol in top}
