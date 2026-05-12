from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Protocol

import pandas as pd

from engine.strategies.spec import StrategySpec


# 전략 실행 컨텍스트. 전략이 의사결정에 필요한 모든 정보를 담는다.
# 가격 데이터 DataFrame 외에 전략에 전달해야 할 파라미터, 상태, 스펙을 하나로 묶은 객체다.
@dataclass
class StrategyContext:
    params: Dict = field(default_factory=dict)         # 런타임 파라미터 (예: {"top_n": 10, "lookback_days": 252})
    state: Dict = field(default_factory=dict)          # 전략이 날짜 간에 유지할 상태 저장소
    spec: StrategySpec | None = field(default=None)    # 전략 전체 스펙 (universe, risk 등 포함)
    # 웹/DB 컨텍스트에서만 사용하는 필드 (CLI에서는 None)
    my_strategy_id: str | None = field(default=None)   # 사용자가 저장한 전략 인스턴스 ID
    user_id: str | None = field(default=None)          # 전략을 실행하는 사용자 ID
    code_version: str | None = field(default=None)     # 전략 코드 해시 (변경 감지용)

    def resolved_params(self) -> Dict:
        # spec.template.params (스펙에 정의된 기본값)과 ctx.params (런타임 오버라이드)를
        # 병합한다. ctx.params가 더 높은 우선순위를 가진다.
        #
        # 예시:
        #   spec.template.params = {"top_n": 10, "lookback_days": 252}
        #   ctx.params           = {"top_n": 5}
        #   resolved             = {"top_n": 5, "lookback_days": 252}  ← top_n이 덮어씌워짐
        spec_params = {}
        if self.spec and self.spec.kind == "template" and self.spec.template:
            spec_params = self.spec.template.params or {}
        return {**spec_params, **(self.params or {})}


# 특정 날짜에 전략이 계산한 목표 포트폴리오 비중을 담는 데이터 클래스.
# runner.py의 시뮬레이션 루프가 이 객체의 리스트를 받아 포지션 변경을 처리한다.
@dataclass
class StrategySignal:
    date: str                          # 리밸런싱 날짜, "YYYY-MM-DD" 형식
    target_weights: Dict[str, float]   # 심볼 → 비중 (예: {"AAPL": 0.3, "MSFT": 0.7})
                                       # 비중의 합이 1.0 이하여야 하며, 나머지는 현금이다


# Strategy는 전략 구현체가 따라야 할 인터페이스(Protocol)다.
# 이 Protocol을 만족하는 클래스는 별도 상속 없이도 전략으로 사용 가능하다.
# runner.py는 이 인터페이스만 알고 구체적인 전략 클래스를 직접 참조하지 않는다.
class Strategy(Protocol):
    name: str   # 전략의 표시 이름 (대시보드, CLI 출력에 사용)

    def required_columns(self) -> List[str]:
        # 이 전략이 가격 DataFrame에서 필요로 하는 컬럼 목록을 반환한다.
        # 현재 모든 전략은 ["adj_close"]만 사용하지만, 향후 거래량 등 추가 가능하다.
        ...

    def generate_signals(
        self,
        prices: pd.DataFrame,
        ctx: StrategyContext,
        universe: List[str],
    ) -> Iterable[StrategySignal]:
        # 전체 백테스트 기간에 대해 리밸런싱 신호를 한 번에 생성한다.
        # prices는 MultiIndex(date, symbol) DataFrame이며, adj_close 컬럼을 가진다.
        # universe는 투자 가능한 심볼 목록이다.
        # 날짜 순서대로 StrategySignal을 yield하는 제너레이터 또는 리스트를 반환해야 한다.
        # MomentumTopN, TrendSMA200, RSIMeanReversion처럼 모든 날짜를 순회하는 전략에 적합하다.
        ...

    def compute_target_weights(
        self,
        prices: pd.DataFrame,
        ctx: StrategyContext,
        universe: List[str],
        dt: pd.Timestamp,
    ) -> Dict[str, float]:
        # 특정 리밸런싱 날짜(dt) 하나에 대해 목표 비중을 계산한다.
        # runner.py가 리밸런싱 스케줄에 따라 각 날짜마다 이 함수를 호출한다.
        # LowVolatility, VolAdjMomentum, RiskOnOff처럼 날짜별로 독립적으로 계산하는
        # 전략에 적합하다. 구현하지 않으면 NotImplementedError를 발생시키고,
        # runner.py는 이 경우 generate_signals로 폴백한다.
        raise NotImplementedError
