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


class VolatilityAdjustedMomentumStrategy(Strategy):
    """Volatility-adjusted momentum.

    Strengths: reduces momentum crash risk.
    Weaknesses: can be slow in strong trends.
    Failure: regime shifts with rising volatility.
    """

    name = "Volatility-Adjusted Momentum"

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
        lookback = int(params.get("lookback_days", 252))
        vol_window = int(params.get("vol_window", 60))
        top_k = int(params.get("top_k", 10))

        price_mat = _price_matrix(prices, universe, ctx)
        if dt not in price_mat.index:
            return {}
        idx = price_mat.index.get_loc(dt)
        if idx < max(lookback, vol_window):
            return {}

        returns = price_mat.pct_change(periods=lookback).iloc[idx]
        vol = price_mat.pct_change().rolling(vol_window).std().iloc[idx]
        score = returns / vol.replace(0, pd.NA)
        score = score.dropna()
        if score.empty:
            return {}

        top = score.sort_values(ascending=False).index[:top_k].tolist()
        if not top:
            return {}
        weight = 1.0 / len(top)
        return {symbol: weight for symbol in top}
