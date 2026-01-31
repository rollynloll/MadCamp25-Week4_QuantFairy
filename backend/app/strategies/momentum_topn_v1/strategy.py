from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from app.strategies.base import Strategy, StrategyContext, StrategySignal


class MomentumTopNStrategy(Strategy):
    """Cross-sectional momentum: top-N by 12M return."""

    name = "Momentum Top-N (12M)"

    def required_columns(self) -> List[str]:
        return ["adj_close"]

    def generate_signals(
        self, prices: pd.DataFrame, ctx: StrategyContext, universe: List[str]
    ) -> Iterable[StrategySignal]:
        lookback = int(ctx.params.get("lookback_days", 252))
        top_n = int(ctx.params.get("top_n", 10))
        rebalance = ctx.params.get("rebalance", "monthly")

        dates = sorted(prices.index.get_level_values(0).unique())
        for idx, dt in enumerate(dates):
            if idx < lookback:
                continue
            if rebalance == "monthly" and dt.day != dates[0].day:
                continue

            returns = {}
            for symbol in universe:
                series = prices.xs(symbol, level=1)["adj_close"].dropna()
                if len(series) <= idx:
                    continue
                start = series.iloc[idx - lookback]
                end = series.iloc[idx]
                returns[symbol] = (end / start) - 1

            if not returns:
                continue
            top = sorted(returns.items(), key=lambda x: x[1], reverse=True)[:top_n]
            weight = 1.0 / len(top)
            yield StrategySignal(
                date=str(dt.date()),
                target_weights={s: weight for s, _ in top},
            )
