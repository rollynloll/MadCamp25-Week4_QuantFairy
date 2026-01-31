from __future__ import annotations

from typing import Dict, Type

from app.strategies.base import Strategy
from app.strategies.momentum_topn_v1.strategy import MomentumTopNStrategy
from app.strategies.trend_sma200_v1.strategy import TrendSMA200Strategy
from app.strategies.rsi_mean_reversion_v1.strategy import RSIMeanReversionStrategy


_REGISTRY: Dict[str, Type[Strategy]] = {
    "strategies.momentum_topn_v1:MomentumTopNStrategy": MomentumTopNStrategy,
    "strategies.trend_sma200_v1:TrendSMA200Strategy": TrendSMA200Strategy,
    "strategies.rsi_mean_reversion_v1:RSIMeanReversionStrategy": RSIMeanReversionStrategy,
}


def get_strategy(entrypoint: str) -> Strategy:
    """Instantiate strategy by entrypoint string."""
    if entrypoint not in _REGISTRY:
        raise ValueError(f"Unknown entrypoint: {entrypoint}")
    return _REGISTRY[entrypoint]()
