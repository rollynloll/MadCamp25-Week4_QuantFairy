from __future__ import annotations

from typing import Iterable, List

import pandas as pd

from engine.strategies.base import Strategy, StrategyContext, StrategySignal


class MomentumTopNStrategy(Strategy):
    # 횡단면 모멘텀 전략: 전체 유니버스에서 지난 N일(기본 252 거래일 ≈ 1년) 수익률이
    # 가장 높은 상위 top_n개 종목에 균등 비중으로 투자한다.
    #
    # 핵심 아이디어: "최근 1년 수익률이 좋은 종목은 계속 좋을 가능성이 높다" (모멘텀 팩터)
    # 강점: 강한 추세 시장에서 우수한 성과
    # 약점: 모멘텀 크래시(급격한 추세 전환)에 취약, 거래 비용이 높을 수 있음

    name = "Momentum Top-N (12M)"

    def required_columns(self) -> List[str]:
        return ["adj_close"]

    def generate_signals(
        self, prices: pd.DataFrame, ctx: StrategyContext, universe: List[str]
    ) -> Iterable[StrategySignal]:
        # prices: MultiIndex(date, symbol) DataFrame, adj_close 컬럼
        # 전체 기간을 순회하며 리밸런싱 날짜마다 신호를 yield한다.

        lookback = int(ctx.params.get("lookback_days", 252))   # 수익률 계산 기간 (거래일 수)
        top_n = int(ctx.params.get("top_n", 10))               # 투자할 상위 종목 수
        rebalance = ctx.params.get("rebalance", "monthly")     # 리밸런싱 주기

        # MultiIndex에서 날짜 레벨을 추출하여 정렬
        dates = sorted(prices.index.get_level_values(0).unique())

        for idx, dt in enumerate(dates):
            # 워밍업 기간: lookback일 이전은 수익률 계산 불가이므로 건너뜀
            if idx < lookback:
                continue

            # 월간 리밸런싱: 매월 첫 번째 거래일과 같은 날짜(일)에만 신호를 발생시킨다.
            # 예: 첫 거래일이 3일이면 매월 3일(또는 가장 가까운 거래일)에 리밸런싱
            if rebalance == "monthly" and dt.day != dates[0].day:
                continue

            # 각 종목의 lookback 기간 수익률 계산
            returns = {}
            for symbol in universe:
                # 해당 심볼의 가격 시계열 추출 (NaN 제거)
                series = prices.xs(symbol, level=1)["adj_close"].dropna()
                if len(series) <= idx:
                    continue
                start_price = series.iloc[idx - lookback]
                end_price = series.iloc[idx]
                returns[symbol] = (end_price / start_price) - 1

            if not returns:
                continue

            # 수익률 내림차순 정렬 후 상위 top_n 선택
            top = sorted(returns.items(), key=lambda x: x[1], reverse=True)[:top_n]

            # 선택된 종목에 균등 비중 배분 (1/N)
            weight = 1.0 / len(top)
            yield StrategySignal(
                date=str(dt.date()),
                target_weights={s: weight for s, _ in top},
            )
