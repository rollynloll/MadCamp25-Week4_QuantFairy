from __future__ import annotations

from typing import Dict, List

import pandas as pd

from engine.strategies.base import Strategy, StrategyContext


def _price_matrix(prices: pd.DataFrame, universe: List[str], ctx: StrategyContext) -> pd.DataFrame:
    # MultiIndex prices를 wide 형식으로 변환하고 ctx.state에 캐싱한다.
    # 동일 ctx에서 여러 날짜를 계산할 때 반복 변환 없이 캐시를 재사용한다.
    cache_key = "price_matrix"
    cached = ctx.state.get(cache_key)
    if cached is not None:
        return cached
    df = prices.reset_index().pivot(index="date", columns="symbol", values="adj_close")
    df = df.sort_index()
    df = df[[s for s in universe if s in df.columns]]
    ctx.state[cache_key] = df
    return df


class VolatilityAdjustedMomentumStrategy(Strategy):
    # 변동성 조정 모멘텀 전략: 단순 수익률 대신 "수익률 / 변동성" 점수로 종목을 선별한다.
    # 이는 샤프 비율과 유사한 개념으로, 수익률이 높더라도 변동성이 크면 점수가 낮아진다.
    #
    # 점수 = lookback일 수익률 / vol_window일 변동성
    # 상위 top_k 종목에 균등 비중 투자
    #
    # 핵심 아이디어: 순수 모멘텀보다 리스크 대비 수익이 좋은 종목을 선택한다
    # 강점: 모멘텀 크래시(고변동성 종목의 급락) 위험을 줄인다
    # 약점: 강한 추세가 있어도 변동성이 높으면 제외될 수 있다

    name = "Volatility-Adjusted Momentum"

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
        lookback = int(params.get("lookback_days", 252))  # 수익률 계산 기간
        vol_window = int(params.get("vol_window", 60))    # 변동성 계산 기간 (더 짧게 설정)
        top_k = int(params.get("top_k", 10))              # 선택할 상위 종목 수

        price_mat = _price_matrix(prices, universe, ctx)
        if dt not in price_mat.index:
            return {}
        idx = price_mat.index.get_loc(dt)

        # 두 계산 기간 중 더 긴 것보다 데이터가 충분해야 한다
        if idx < max(lookback, vol_window):
            return {}

        # lookback일 전 대비 현재 수익률 (각 심볼별, 현재 날짜 행만 추출)
        returns = price_mat.pct_change(periods=lookback).iloc[idx]

        # vol_window 기간 rolling 표준편차의 현재 날짜 값 (일간 변동성)
        vol = price_mat.pct_change().rolling(vol_window).std().iloc[idx]

        # 점수 = 수익률 / 변동성. vol=0인 경우 NA 처리하여 점수 계산에서 제외
        score = returns / vol.replace(0, pd.NA)
        score = score.dropna()
        if score.empty:
            return {}

        # 점수 내림차순으로 상위 top_k 선택
        top = score.sort_values(ascending=False).index[:top_k].tolist()
        if not top:
            return {}
        weight = 1.0 / len(top)
        return {symbol: weight for symbol in top}
