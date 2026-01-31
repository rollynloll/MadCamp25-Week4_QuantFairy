from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from app.strategies.base import Strategy, StrategyContext, StrategySignal


class TrendSMA200Strategy(Strategy):
    """Risk-on if price > SMA200 else cash."""

    name = "Trend SMA200"

    def required_columns(self) -> List[str]:
        return ["adj_close"]

    def generate_signals(
        self, prices: pd.DataFrame, ctx: StrategyContext, universe: List[str]
    ) -> Iterable[StrategySignal]:
        symbol = ctx.params.get("benchmark_symbol", "SPY")
        window = int(ctx.params.get("sma_window", 200))

        series = prices.xs(symbol, level=1)["adj_close"].dropna()
        sma = series.rolling(window).mean()

        for dt in series.index:
            if pd.isna(sma.loc[dt]):
                continue
            risk_on = series.loc[dt] > sma.loc[dt]
            weights = {symbol: 1.0} if risk_on else {}
            yield StrategySignal(date=str(dt.date()), target_weights=weights)
