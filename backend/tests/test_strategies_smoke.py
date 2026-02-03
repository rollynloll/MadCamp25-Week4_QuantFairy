from __future__ import annotations

import pandas as pd

from app.strategies.base import StrategyContext
from app.strategies.low_volatility import LowVolatilityStrategy
from app.strategies.momentum_topn_v1.strategy import MomentumTopNStrategy
from app.strategies.rsi_mean_reversion_v1.strategy import RSIMeanReversionStrategy
from app.strategies.trend_sma200_v1.strategy import TrendSMA200Strategy
from app.strategies.vol_adj_momentum import VolatilityAdjustedMomentumStrategy
from app.strategies.risk_on_off import RiskOnOffStrategy


def _make_prices() -> pd.DataFrame:
    symbols = ["SPY", "AAPL", "MSFT", "QQQ"]
    dates = pd.date_range("2022-01-01", periods=260, freq="B")
    rows = []
    for symbol in symbols:
        base = 100 + (hash(symbol) % 20)
        for idx, dt in enumerate(dates):
            price = base + idx * 0.1 + (idx % 5) * 0.05
            rows.append({"date": dt, "symbol": symbol, "adj_close": price})
    df = pd.DataFrame(rows)
    return df.set_index(["date", "symbol"]).sort_index()


def _make_ctx(params: dict | None = None) -> StrategyContext:
    return StrategyContext(
        my_strategy_id="test",
        user_id="test",
        params=params or {},
        code_version="test",
    )


def test_existing_strategies_smoke() -> None:
    prices = _make_prices()
    universe = ["SPY", "AAPL", "MSFT", "QQQ"]

    momentum = MomentumTopNStrategy()
    rsi = RSIMeanReversionStrategy()
    trend = TrendSMA200Strategy()

    list(momentum.generate_signals(prices, _make_ctx({"rebalance": "monthly"}), universe))
    list(rsi.generate_signals(prices, _make_ctx({"symbol": "SPY"}), universe))
    list(trend.generate_signals(prices, _make_ctx({"benchmark_symbol": "SPY"}), universe))


def test_new_strategies_smoke() -> None:
    prices = _make_prices()
    universe = ["SPY", "AAPL", "MSFT", "QQQ"]
    dt = prices.index.get_level_values(0).unique()[-1]

    low_vol = LowVolatilityStrategy()
    vol_adj = VolatilityAdjustedMomentumStrategy()
    risk_on_off = RiskOnOffStrategy()

    low_vol.compute_target_weights(prices, _make_ctx(), universe, dt)
    vol_adj.compute_target_weights(prices, _make_ctx(), universe, dt)
    risk_on_off.compute_target_weights(prices, _make_ctx({"benchmark_symbol": "SPY"}), universe, dt)
