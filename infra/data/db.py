from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import asyncpg


class DBProvider:
    """DataProvider backed by the market_prices PostgreSQL table.

    Used in the web backend where the DB pool is already available.
    Requires the table schema:
        market_prices(symbol TEXT, price_date DATE, adj_close FLOAT)
    """

    def __init__(self, pool: "asyncpg.Pool") -> None:
        self._pool = pool

    def get_prices(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        """Synchronous wrapper — runs the async query in the current event loop or a new one."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Inside an async context (e.g. called from FastAPI route via run_in_executor)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, self._fetch(tickers, start, end))
                return future.result()
        else:
            return asyncio.run(self._fetch(tickers, start, end))

    async def get_prices_async(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        """Native async version for use in async contexts."""
        return await self._fetch(tickers, start, end)

    async def _fetch(self, tickers: list[str], start: str, end: str) -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame()

        rows = await self._pool.fetch(
            """
            SELECT symbol, price_date, adj_close
            FROM market_prices
            WHERE symbol = ANY($1::text[])
              AND price_date >= $2::date
              AND price_date <= $3::date
            ORDER BY price_date
            """,
            tickers,
            start,
            end,
        )

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame([dict(r) for r in rows])
        df["price_date"] = pd.to_datetime(df["price_date"])
        wide = df.pivot(index="price_date", columns="symbol", values="adj_close")
        wide.index.name = "date"
        wide.columns.name = None
        return wide.sort_index()
