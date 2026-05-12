from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from engine.strategies.base import Strategy, StrategyContext, StrategySignal
from engine.strategies.indicators import compute_rsi


class RSIMeanReversionStrategy(Strategy):
    # RSI 기반 평균 회귀 전략. 단일 심볼에 대해 과매도/과매수 구간을 이용한다.
    # RSI < entry_rsi(기본 30) : 과매도 → 전량 매수 (포지션 진입)
    # RSI > exit_rsi (기본 50) : 과매수/중립 → 전량 매도 (포지션 청산)
    #
    # 핵심 아이디어: 가격이 많이 내려간(RSI 30 이하) 종목은 결국 평균으로 회귀한다
    # 강점: 박스권/횡보 시장에서 효과적
    # 약점: 강한 하락 추세에서 신호가 발생해도 계속 하락할 수 있다 (하락 추세 추종 위험)

    name = "RSI Mean Reversion"

    def required_columns(self) -> List[str]:
        return ["adj_close"]

    def generate_signals(
        self, prices: pd.DataFrame, ctx: StrategyContext, universe: List[str]
    ) -> Iterable[StrategySignal]:
        symbol = ctx.params.get("symbol", "SPY")           # 거래 대상 심볼
        rsi_window = int(ctx.params.get("rsi_window", 14)) # RSI 계산 기간 (기본 14일)
        entry = float(ctx.params.get("entry_rsi", 30))     # 매수 진입 RSI 임계값
        exit_ = float(ctx.params.get("exit_rsi", 50))      # 매도 청산 RSI 임계값

        series = prices.xs(symbol, level=1)["adj_close"]

        # Wilder의 지수 이동평균 방식으로 RSI 계산 (기본 표준 방식)
        rsi = compute_rsi(series, rsi_window, method="wilder")

        position = False   # 현재 포지션 보유 여부를 추적하는 상태 변수

        for dt in series.index:
            # RSI 워밍업 기간은 신호 없음
            if pd.isna(rsi.loc[dt]):
                continue

            if not position and rsi.loc[dt] < entry:
                # 포지션이 없고 RSI가 진입 임계값 아래로 내려갔을 때 → 전량 매수
                position = True
                yield StrategySignal(date=str(dt.date()), target_weights={symbol: 1.0})

            elif position and rsi.loc[dt] > exit_:
                # 포지션 보유 중이고 RSI가 청산 임계값 위로 올라갔을 때 → 전량 현금
                # 빈 딕셔너리 = "모든 자산 비중 0" = 전량 현금 의미
                position = False
                yield StrategySignal(date=str(dt.date()), target_weights={})
