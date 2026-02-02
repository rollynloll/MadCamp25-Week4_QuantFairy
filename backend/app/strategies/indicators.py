from __future__ import annotations

from typing import Literal

import pandas as pd


def _validate_series(series: pd.Series, name: str) -> pd.Series:
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
    """Compute RSI with Wilder's smoothing or SMA.

    Returns a Series aligned to `series` index with NaNs for warm-up.
    """

    series = _validate_series(series, "series")
    if window <= 0:
        raise ValueError("window must be > 0")

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    if method == "wilder":
        avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
        avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
    elif method == "sma":
        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()
    else:
        raise ValueError("method must be 'wilder' or 'sma'")

    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_returns(series: pd.Series, window: int) -> pd.Series:
    """Compute simple returns over a rolling window."""

    series = _validate_series(series, "series")
    if window <= 0:
        raise ValueError("window must be > 0")
    return series.pct_change(periods=window)


def compute_volatility(returns: pd.Series, window: int) -> pd.Series:
    """Compute rolling volatility (std of returns)."""

    returns = _validate_series(returns, "returns")
    if window <= 0:
        raise ValueError("window must be > 0")
    return returns.rolling(window).std()
