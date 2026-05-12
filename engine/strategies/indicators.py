from __future__ import annotations

from typing import Literal

import pandas as pd


def _validate_series(series: pd.Series, name: str) -> pd.Series:
    # 입력 Series가 pandas Series인지 확인하고 float 타입으로 변환한다.
    # 빈 Series는 그대로 반환하여 하위 함수에서 빈 결과를 처리할 수 있게 한다.
    if not isinstance(series, pd.Series):
        raise ValueError(f"{name} must be a pandas Series")
    if series.empty:
        return series.astype(float)
    return series.astype(float)


def compute_rsi(
    series: pd.Series,
    window: int,
    method: Literal["wilder", "sma"] = "wilder",
) -> pd.Series:
    # RSI(Relative Strength Index, 상대강도지수)를 계산한다.
    # RSI는 0~100 사이의 값으로, 일반적으로 30 이하면 과매도(매수 신호),
    # 70 이상이면 과매수(매도 신호)로 해석한다.
    #
    # 계산 과정:
    #   1. 전일 대비 가격 변화(delta)를 구한다
    #   2. 상승분(gain)과 하락분(loss)을 분리한다
    #   3. 평균 상승/하락을 지수 이동평균(wilder) 또는 단순 이동평균(sma)으로 구한다
    #   4. RS = 평균 상승 / 평균 하락
    #   5. RSI = 100 - (100 / (1 + RS))
    #
    # wilder 방식: Wilder의 EMA (alpha=1/window). 워밍업 기간(window개) 동안 NaN.
    # sma 방식: 단순 rolling 평균. 더 반응이 빠르지만 표준에서 벗어난다.

    series = _validate_series(series, "series")
    if window <= 0:
        raise ValueError("window must be > 0")

    delta = series.diff()
    gain = delta.clip(lower=0)    # 상승분만 남기고 음수는 0으로
    loss = -delta.clip(upper=0)   # 하락분의 절댓값 (양수로 변환)

    if method == "wilder":
        avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
        avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    elif method == "sma":
        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()
    else:
        raise ValueError("method must be 'wilder' or 'sma'")

    # avg_loss가 0이면 RS = 무한대 → RSI = 100 이 되어야 하므로 0을 NA로 대체
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_returns(series: pd.Series, window: int) -> pd.Series:
    # window일 전 가격 대비 단순 수익률을 계산한다.
    # 예: window=252이면 1년(252 거래일) 수익률 → 모멘텀 전략의 기반 지표
    # 반환값: (현재 가격 / window일 전 가격) - 1
    series = _validate_series(series, "series")
    if window <= 0:
        raise ValueError("window must be > 0")
    return series.pct_change(periods=window)


def compute_volatility(returns: pd.Series, window: int) -> pd.Series:
    # window 기간 동안의 수익률 표준편차(변동성)를 rolling으로 계산한다.
    # 낮은 변동성 전략에서 자산을 선별하거나, 변동성 조정 모멘텀 점수를 구할 때 사용한다.
    # 반환값은 연율화되지 않은 일간 변동성이므로 연율화하려면 sqrt(252)를 곱해야 한다.
    returns = _validate_series(returns, "returns")
    if window <= 0:
        raise ValueError("window must be > 0")
    return returns.rolling(window).std()
