import argparse
import asyncio
import os
import pathlib
import sys
from datetime import date
from typing import Dict, Iterable, List

import asyncpg
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]


def normalize_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+asyncpg://"):
        return "postgresql://" + dsn[len("postgresql+asyncpg://") :]
    if dsn.startswith("postgres+asyncpg://"):
        return "postgresql://" + dsn[len("postgres+asyncpg://") :]
    return dsn


def load_env() -> None:
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Yahoo Finance data into Supabase")
    parser.add_argument("--symbols", type=str, default="", help="Comma-separated symbols")
    parser.add_argument("--preset", type=str, default="", help="Preset universe id (US_TOP_10, US_CORE_20, etc)")
    parser.add_argument("--start", type=str, default="2005-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, default="", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--batch-size", type=int, default=500, help="Rows per batch insert")
    return parser.parse_args()


def resolve_symbols(symbols_arg: str, preset: str) -> List[str]:
    symbols = [s.strip().upper() for s in symbols_arg.split(",") if s.strip()]
    if symbols:
        return symbols
    if preset:
        try:
            from app.universes.presets import UNIVERSE_PRESETS

            preset_data = UNIVERSE_PRESETS.get(preset)
            if not preset_data:
                raise ValueError(f"Unknown preset: {preset}")
            return preset_data["tickers"]
        except Exception as exc:
            raise ValueError(f"Failed to load preset: {exc}") from exc
    raise ValueError("Provide --symbols or --preset")


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    columns = []
    for col in df.columns:
        col_name = str(col).strip().lower().replace(" ", "_")
        if col_name == "adj_close":
            columns.append("adj_close")
        else:
            columns.append(col_name)
    df = df.copy()
    df.columns = columns
    return df


def fetch_yahoo(symbols: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
    df = yf.download(
        tickers=" ".join(symbols),
        start=start,
        end=end,
        auto_adjust=False,
        actions=False,
        progress=False,
        group_by="ticker",
    )
    data: Dict[str, pd.DataFrame] = {}
    if len(symbols) == 1:
        symbol = symbols[0]
        data[symbol] = _standardize_columns(df)
        return data

    # MultiIndex columns: (symbol, field)
    if isinstance(df.columns, pd.MultiIndex):
        for symbol in symbols:
            if symbol not in df.columns.levels[0]:
                continue
            sub = df[symbol]
            data[symbol] = _standardize_columns(sub)
    else:
        # Fallback to flat columns
        for symbol in symbols:
            data[symbol] = _standardize_columns(df)
    return data


def iter_rows(symbol: str, df: pd.DataFrame) -> Iterable[tuple]:
    for idx, row in df.iterrows():
        if pd.isna(idx):
            continue
        price_date = idx.date() if hasattr(idx, "date") else date.fromisoformat(str(idx))
        values = {
            "open": row.get("open"),
            "high": row.get("high"),
            "low": row.get("low"),
            "close": row.get("close"),
            "adj_close": row.get("adj_close") or row.get("adj_close".replace("_", " ")),
            "volume": row.get("volume"),
        }
        if all(pd.isna(v) for v in values.values()):
            continue
        yield (
            symbol,
            price_date,
            None if pd.isna(values["open"]) else float(values["open"]),
            None if pd.isna(values["high"]) else float(values["high"]),
            None if pd.isna(values["low"]) else float(values["low"]),
            None if pd.isna(values["close"]) else float(values["close"]),
            None if pd.isna(values["adj_close"]) else float(values["adj_close"]),
            None if pd.isna(values["volume"]) else int(values["volume"]),
        )


async def upsert_rows(conn: asyncpg.Connection, rows: List[tuple]) -> None:
    if not rows:
        return
    query = """
        insert into market_prices (
            symbol,
            price_date,
            open,
            high,
            low,
            close,
            adj_close,
            volume
        )
        values ($1,$2,$3,$4,$5,$6,$7,$8)
        on conflict (symbol, price_date)
        do update set
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            close = excluded.close,
            adj_close = excluded.adj_close,
            volume = excluded.volume,
            updated_at = now();
    """
    await conn.executemany(query, rows)


async def main() -> None:
    load_env()
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is not set", file=sys.stderr)
        sys.exit(1)

    args = parse_args()
    symbols = resolve_symbols(args.symbols, args.preset)
    start = args.start
    end = args.end or date.today().isoformat()

    yahoo_symbols = [s.replace(".", "-") for s in symbols]
    symbol_map = {yahoo: original for yahoo, original in zip(yahoo_symbols, symbols)}

    print(f"Fetching Yahoo Finance data: {len(symbols)} symbols, {start} -> {end}")
    data = fetch_yahoo(yahoo_symbols, start, end)

    dsn = normalize_dsn(dsn)
    conn = await asyncpg.connect(dsn)
    try:
        for yahoo_symbol, df in data.items():
            symbol = symbol_map.get(yahoo_symbol, yahoo_symbol)
            rows = list(iter_rows(symbol, df))
            print(f"{symbol}: {len(rows)} rows")
            for i in range(0, len(rows), args.batch_size):
                batch = rows[i : i + args.batch_size]
                await upsert_rows(conn, batch)
    finally:
        await conn.close()

    print("Ingestion completed.")


if __name__ == "__main__":
    asyncio.run(main())
