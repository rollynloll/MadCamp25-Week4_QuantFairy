from __future__ import annotations

from typing import Dict, Type

from engine.strategies.base import Strategy
from engine.strategies.catalog.momentum_topn_v1 import MomentumTopNStrategy
from engine.strategies.catalog.trend_sma200_v1 import TrendSMA200Strategy
from engine.strategies.catalog.rsi_mean_reversion_v1 import RSIMeanReversionStrategy
from engine.strategies.catalog.low_volatility import LowVolatilityStrategy
from engine.strategies.catalog.vol_adj_momentum import VolatilityAdjustedMomentumStrategy
from engine.strategies.catalog.risk_on_off import RiskOnOffStrategy


# 전략 entrypoint 문자열 → 전략 클래스 매핑 테이블.
# 새 전략을 추가할 때는 이 딕셔너리에 항목을 추가하면 된다.
_REGISTRY: Dict[str, Type[Strategy]] = {
    "momentum":      MomentumTopNStrategy,
    "trend":         TrendSMA200Strategy,
    "rsi-reversion": RSIMeanReversionStrategy,
    "low-vol":       LowVolatilityStrategy,
    "vol-momentum":  VolatilityAdjustedMomentumStrategy,
    "risk-on-off":   RiskOnOffStrategy,
}


def get_strategy(entrypoint: str) -> Strategy:
    # entrypoint 문자열로 전략 인스턴스를 생성하여 반환한다.
    # 매번 새 인스턴스를 생성하므로 전략 내부 상태가 공유되지 않는다.
    # 알 수 없는 entrypoint는 ValueError를 발생시킨다.
    if entrypoint not in _REGISTRY:
        raise ValueError(f"Unknown entrypoint: {entrypoint}")
    return _REGISTRY[entrypoint]()


def list_entrypoints() -> list[str]:
    # 현재 등록된 모든 전략의 entrypoint 목록을 반환한다.
    # CLI의 --strategy 옵션 자동완성이나 API의 전략 목록 응답에 사용한다.
    return list(_REGISTRY.keys())
