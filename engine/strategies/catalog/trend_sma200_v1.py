from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from engine.strategies.base import Strategy, StrategyContext, StrategySignal


class TrendSMA200Strategy(Strategy):
    # 200일 이동평균선(SMA200)을 기준으로 위험 자산과 현금을 전환하는 전략.
    # 벤치마크 심볼(기본 SPY)의 가격이 SMA200 위에 있으면 "위험 선호(Risk-on)" → 전량 투자
    # SMA200 아래에 있으면 "위험 회피(Risk-off)" → 전량 현금
    #
    # 핵심 아이디어: 장기 추세가 상승 중일 때만 시장에 참여한다
    # 강점: 큰 하락장(2008, 2020년 3월)을 상당 부분 피할 수 있다
    # 약점: 횡보장에서 잦은 신호 전환(Whipsaw)으로 거래 비용 발생

    name = "Trend SMA200"

    def required_columns(self) -> List[str]:
        return ["adj_close"]

    def generate_signals(
        self, prices: pd.DataFrame, ctx: StrategyContext, universe: List[str]
    ) -> Iterable[StrategySignal]:
        symbol = ctx.params.get("benchmark_symbol", "SPY")   # 추세 판단 기준 심볼
        window = int(ctx.params.get("sma_window", 200))      # 이동평균 기간 (기본 200일)

        # 벤치마크 심볼의 가격 시계열 추출
        series = prices.xs(symbol, level=1)["adj_close"].dropna()

        # rolling(window).mean() : 각 날짜의 과거 window일 단순 이동평균
        sma = series.rolling(window).mean()

        for dt in series.index:
            # SMA 워밍업 기간(200일 미만)은 신호 없음
            if pd.isna(sma.loc[dt]):
                continue

            # 현재 가격이 SMA200 위이면 전량 해당 심볼 투자, 아래이면 현금(빈 딕셔너리)
            risk_on = series.loc[dt] > sma.loc[dt]
            weights = {symbol: 1.0} if risk_on else {}
            yield StrategySignal(date=str(dt.date()), target_weights=weights)
