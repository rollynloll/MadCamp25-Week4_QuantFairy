from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from app.strategies.base import Strategy, StrategyContext, StrategySignal


class RSIMeanReversionStrategy(Strategy):
    """RSI < entry buys, RSI > exit sells."""

    name = "RSI Mean Reversion"

    def required_columns(self) -> List[str]:
        return ["adj_close"]

    def generate_signals(
        self, prices: pd.DataFrame, ctx: StrategyContext, universe: List[str]
    ) -> Iterable[StrategySignal]:
        symbol = ctx.params.get("symbol", "SPY")
        rsi_window = int(ctx.params.get("rsi_window", 14))
        entry = float(ctx.params.get("entry_rsi", 30))
        exit = float(ctx.params.get("exit_rsi", 50))

        series = prices.xs(symbol, level=1)["adj_close"].dropna()
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(rsi_window).mean()
        loss = (-delta.clip(upper=0)).rolling(rsi_window).mean()
        rs = gain / loss.replace(0, pd.NA)
        rsi = 100 - (100 / (1 + rs))

        position = False
        for dt in series.index:
            if pd.isna(rsi.loc[dt]):
                continue
            if not position and rsi.loc[dt] < entry:
                position = True
                yield StrategySignal(date=str(dt.date()), target_weights={symbol: 1.0})
            elif position and rsi.loc[dt] > exit:
                position = False
                yield StrategySignal(date=str(dt.date()), target_weights={})
