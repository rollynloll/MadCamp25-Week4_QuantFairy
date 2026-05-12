from __future__ import annotations

from typing import Dict, List

import pandas as pd

from engine.strategies.base import Strategy, StrategyContext


def _price_matrix(prices: pd.DataFrame, universe: List[str], ctx: StrategyContext) -> pd.DataFrame:
    # MultiIndex prices를 wide 형식으로 변환하고 ctx.state에 캐싱한다.
    cache_key = "price_matrix"
    cached = ctx.state.get(cache_key)
    if cached is not None:
        return cached
    df = prices.reset_index().pivot(index="date", columns="symbol", values="adj_close")
    df = df.sort_index()
    df = df[[s for s in universe if s in df.columns]]
    ctx.state[cache_key] = df
    return df


class RiskOnOffStrategy(Strategy):
    # 시장 레짐(국면) 기반 위험 자산 로테이션 전략.
    # 두 단계로 작동한다:
    #
    # 1단계 - 레짐 판단:
    #   벤치마크(기본 SPY)가 SMA(sma_window일) 위에 있으면 "위험 선호(Risk-on)"
    #   SMA 아래이면 "위험 회피(Risk-off)" → 전량 현금
    #
    # 2단계 - 위험 선호 국면에서 종목 선택:
    #   lookback일 수익률 상위 top_k 종목에 균등 비중 투자 (모멘텀 선택)
    #
    # 핵심 아이디어: 시장이 좋을 때만 투자하고, 투자 시에도 강한 종목을 선택한다
    # SMA200 전략(레짐만)과 MomentumTopN(종목 선택만)을 결합한 형태
    # 강점: 큰 하락장 방어 + 상승장에서도 강한 종목 선택
    # 약점: 횡보장에서 잦은 전환(Whipsaw), 레짐 신호가 늦을 수 있음

    name = "Risk-On / Risk-Off"

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
        benchmark_symbol = str(params.get("benchmark_symbol", "SPY")).upper()
        sma_window = int(params.get("sma_window", 200))    # 레짐 판단 이동평균 기간
        lookback = int(params.get("lookback_days", 126))   # 모멘텀 수익률 계산 기간
        top_k = int(params.get("top_k", 10))               # 선택할 상위 종목 수

        price_mat = _price_matrix(prices, universe, ctx)
        if dt not in price_mat.index:
            return {}
        idx = price_mat.index.get_loc(dt)

        # SMA 계산을 위해 최소 sma_window일 데이터 필요
        if idx < sma_window:
            return {}

        # --- 1단계: 레짐 판단 ---
        # 벤치마크 심볼의 가격을 MultiIndex에서 직접 추출
        benchmark_series = prices.xs(benchmark_symbol, level=1)["adj_close"]
        benchmark_series = benchmark_series.sort_index()
        if dt not in benchmark_series.index:
            return {}

        sma = benchmark_series.rolling(sma_window).mean()
        risk_on = benchmark_series.loc[dt] > sma.loc[dt]

        # 위험 회피 국면이면 즉시 현금 (빈 딕셔너리)
        if not risk_on:
            return {}

        # --- 2단계: 위험 선호 국면에서 모멘텀 상위 종목 선택 ---
        if idx < lookback:
            return {}

        # lookback일 수익률로 종목 순위 산정
        returns = price_mat.pct_change(periods=lookback).iloc[idx]
        returns = returns.dropna()
        if returns.empty:
            return {}

        # 수익률 상위 top_k 종목에 균등 비중 배분
        top = returns.sort_values(ascending=False).index[:top_k].tolist()
        if not top:
            return {}
        weight = 1.0 / len(top)
        return {symbol: weight for symbol in top}
