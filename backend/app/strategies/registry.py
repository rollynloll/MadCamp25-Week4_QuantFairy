from __future__ import annotations

from typing import Dict, Type

from engine.strategies.base import Strategy
from engine.strategies.catalog.low_volatility import LowVolatilityStrategy
from engine.strategies.catalog.momentum_topn_v1 import MomentumTopNStrategy
from engine.strategies.catalog.risk_on_off import RiskOnOffStrategy
from engine.strategies.catalog.rsi_mean_reversion_v1 import RSIMeanReversionStrategy
from engine.strategies.catalog.trend_sma200_v1 import TrendSMA200Strategy
from engine.strategies.catalog.vol_adj_momentum import VolatilityAdjustedMomentumStrategy

# 기존 DB에 저장된 entrypoint 키를 그대로 유지한다.
_REGISTRY: Dict[str, Type[Strategy]] = {
    "strategies.momentum_topn_v1:MomentumTopNStrategy": MomentumTopNStrategy,
    "strategies.trend_sma200_v1:TrendSMA200Strategy": TrendSMA200Strategy,
    "strategies.rsi_mean_reversion_v1:RSIMeanReversionStrategy": RSIMeanReversionStrategy,
    "strategies.low_volatility:LowVolatilityStrategy": LowVolatilityStrategy,
    "strategies.vol_adj_momentum:VolatilityAdjustedMomentumStrategy": VolatilityAdjustedMomentumStrategy,
    "strategies.risk_on_off:RiskOnOffStrategy": RiskOnOffStrategy,
}


def get_strategy(entrypoint: str) -> Strategy:
    if entrypoint not in _REGISTRY:
        raise ValueError(f"Unknown entrypoint: {entrypoint}")
    return _REGISTRY[entrypoint]()
