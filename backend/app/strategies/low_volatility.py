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


class LowVolatilityStrategy(Strategy):
    """Low volatility selection.

    Strengths: defensive, lower drawdowns.
    Weaknesses: can lag in sharp rallies.
    Failure: fast momentum regimes.
    """

    name = "Low Volatility"

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
        lookback = int(params.get("lookback_days", 60))
        top_k = int(params.get("top_k", 10))
        weighting = str(params.get("weighting", "inverse_vol"))

        price_mat = _price_matrix(prices, universe, ctx)
        if dt not in price_mat.index:
            return {}
        idx = price_mat.index.get_loc(dt)
        if idx < lookback:
            return {}

        window = price_mat.iloc[idx - lookback : idx + 1]
        returns = window.pct_change()
        vol = returns.std()
        vol = vol.dropna()
        if vol.empty:
            return {}

        selected = vol.sort_values().index[:top_k].tolist()
        if not selected:
            return {}

        if weighting == "equal":
            weight = 1.0 / len(selected)
            return {symbol: weight for symbol in selected}

        inv = 1.0 / vol[selected]
        inv = inv.replace([pd.NA, pd.NaT], 0).fillna(0)
        if inv.sum() <= 0:
            weight = 1.0 / len(selected)
            return {symbol: weight for symbol in selected}
        weights = inv / inv.sum()
        return {symbol: float(weights.loc[symbol]) for symbol in selected}
