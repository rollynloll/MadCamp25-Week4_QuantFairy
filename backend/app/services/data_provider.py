from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, List


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def trading_days(start: date, end: date) -> List[date]:
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def _base_price(ticker: str) -> float:
    seed = sum(ord(c) for c in ticker)
    return 50 + (seed % 200)


def load_price_series(
    tickers: List[str], period_start: str, period_end: str
) -> Dict[str, Dict[str, float]]:
    start = parse_date(period_start)
    end = parse_date(period_end)
    days = trading_days(start, end)

    series: Dict[str, Dict[str, float]] = {}
    for ticker in tickers:
        base = _base_price(ticker)
        ticker_series: Dict[str, float] = {}
        for i, d in enumerate(days):
            drift = 1 + 0.0008 * i
            seasonal = 0.01 * ((i % 10) - 5) / 10
            price = base * drift * (1 + seasonal)
            ticker_series[d.isoformat()] = round(price, 4)
        series[ticker] = ticker_series
    return series
