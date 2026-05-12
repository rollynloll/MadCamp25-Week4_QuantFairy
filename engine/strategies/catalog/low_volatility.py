from __future__ import annotations

from typing import Dict, List

import pandas as pd

from engine.strategies.base import Strategy, StrategyContext


def _price_matrix(prices: pd.DataFrame, universe: List[str], ctx: StrategyContext) -> pd.DataFrame:
    # MultiIndex(date, symbol) 형식의 prices를 wide 형식(행=날짜, 열=심볼)으로 변환한다.
    # 변환 결과를 ctx.state에 캐싱하여 같은 ctx로 여러 날짜를 계산할 때 반복 변환을 방지한다.
    # ctx.state는 전략 실행 세션 동안 유지되는 딕셔너리이다.
    cache_key = "price_matrix"
    cached = ctx.state.get(cache_key)
    if cached is not None:
        return cached
    df = prices.reset_index().pivot(index="date", columns="symbol", values="adj_close")
    df = df.sort_index()
    # universe에 있는 심볼만 유지하고 순서도 universe 순서로 맞춘다
    df = df[[s for s in universe if s in df.columns]]
    ctx.state[cache_key] = df
    return df


class LowVolatilityStrategy(Strategy):
    # 저변동성 선택 전략: 유니버스에서 지난 N일 변동성이 가장 낮은 top_k 종목에 투자한다.
    # 방어적인 성격의 전략으로 큰 하락을 피하는 데 중점을 둔다.
    #
    # 비중 계산 방식 (weighting 파라미터):
    #   "inverse_vol" (기본): 변동성의 역수에 비례하여 비중 배분
    #                          → 변동성이 낮을수록 더 많은 비중을 받는다
    #   "equal"             : 선택된 모든 종목에 균등 비중 배분
    #
    # 강점: 하락장에서 상대적으로 선방, 낮은 MDD(최대낙폭)
    # 약점: 급등장에서 수익률 뒤처짐, 빠른 모멘텀 장세에 적합하지 않음

    name = "Low Volatility"

    def required_columns(self) -> List[str]:
        return ["adj_close"]

    def compute_target_weights(
        self,
        prices: pd.DataFrame,
        ctx: StrategyContext,
        universe: List[str],
        dt: pd.Timestamp,
    ) -> Dict[str, float]:
        params = ctx.resolved_params()
        lookback = int(params.get("lookback_days", 60))         # 변동성 계산 기간 (거래일 수)
        top_k = int(params.get("top_k", 10))                   # 선택할 저변동성 종목 수
        weighting = str(params.get("weighting", "inverse_vol")) # 비중 계산 방식

        price_mat = _price_matrix(prices, universe, ctx)

        # 현재 날짜가 가격 행렬에 없으면 투자 불가
        if dt not in price_mat.index:
            return {}
        idx = price_mat.index.get_loc(dt)

        # 워밍업 기간: lookback일 미만의 데이터로는 변동성 계산 불가
        if idx < lookback:
            return {}

        # lookback 기간의 가격 창(window)에서 일간 수익률의 표준편차를 변동성으로 사용
        window = price_mat.iloc[idx - lookback : idx + 1]
        returns = window.pct_change()
        vol = returns.std()
        vol = vol.dropna()   # 데이터 부족 심볼 제거
        if vol.empty:
            return {}

        # 변동성 오름차순 정렬 후 상위 top_k 선택 (가장 낮은 변동성 = 인덱스 앞쪽)
        selected = vol.sort_values().index[:top_k].tolist()
        if not selected:
            return {}

        if weighting == "equal":
            weight = 1.0 / len(selected)
            return {symbol: weight for symbol in selected}

        # 역변동성 비중: 각 심볼의 비중 = (1/변동성) / 전체 역변동성 합
        # 변동성이 낮은 종목일수록 더 큰 비중을 받는다
        inv = 1.0 / vol[selected]
        inv = inv.replace([pd.NA, pd.NaT], 0).fillna(0)
        if inv.sum() <= 0:
            weight = 1.0 / len(selected)
            return {symbol: weight for symbol in selected}
        weights = inv / inv.sum()
        return {symbol: float(weights.loc[symbol]) for symbol in selected}
