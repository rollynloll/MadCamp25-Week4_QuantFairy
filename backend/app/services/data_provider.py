from __future__ import annotations

from datetime import date, datetime, timedelta
import time
from typing import Dict, List

from app.core.config import get_settings
from app.storage.supabase_client import get_supabase_client


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
    tickers: List[str],
    period_start: str,
    period_end: str,
    price_field: str = "adj_close",
) -> Dict[str, Dict[str, float]]:
    settings = get_settings()
    supabase = get_supabase_client(settings)
    if supabase is not None:
        return _load_from_supabase(
            supabase, tickers, period_start, period_end, price_field
        )

    return _load_mock_prices(tickers, period_start, period_end)


def _load_mock_prices(
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


def _load_from_supabase(
    supabase,
    tickers: List[str],
    period_start: str,
    period_end: str,
    price_field: str,
) -> Dict[str, Dict[str, float]]:
    field = price_field if price_field in {"adj_close", "close"} else "adj_close"
    result: Dict[str, Dict[str, float]] = {}

    def _execute_with_retry(query, attempts: int = 3) -> object:
        last_exc: Exception | None = None
        for attempt in range(attempts):
            try:
                return query.execute()
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < attempts - 1:
                    time.sleep(0.5 * (2 ** attempt))
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Supabase query failed")

    for ticker in tickers:
        query = (
            supabase.table("market_prices")
            .select(f"price_date,{field}")
            .eq("symbol", ticker)
            .gte("price_date", period_start)
            .lte("price_date", period_end)
            .order("price_date", desc=False)
        )

        rows = []
        from_index = 0
        page_size = 1000
        while True:
            page = _execute_with_retry(query.range(from_index, from_index + page_size - 1))
            data = getattr(page, "data", None) or []
            rows.extend(data)
            if len(data) < page_size:
                break
            from_index += page_size

        series: Dict[str, float] = {}
        for row in rows:
            date_str = row.get("price_date")
            value = row.get(field)
            if date_str is None or value is None:
                continue
            series[str(date_str)] = float(value)
        result[ticker] = series

    return result
