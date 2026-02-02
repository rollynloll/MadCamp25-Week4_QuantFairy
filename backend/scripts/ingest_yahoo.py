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
    parser.add_argument("--symbols-file", type=str, default="", help="Path to symbols list (comma/newline separated)")
    parser.add_argument("--preset", type=str, default="", help="Preset universe id (US_TOP_10, US_CORE_20, etc)")
    parser.add_argument("--start", type=str, default="2005-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", type=str, default="", help="End date YYYY-MM-DD (default: today)")
    parser.add_argument("--years", type=int, default=0, help="Lookback years (overrides --start if set)")
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Only fetch missing earlier data based on existing min(date) per symbol",
    )
    parser.add_argument("--batch-size", type=int, default=500, help="Rows per batch insert")
    parser.add_argument("--chunk-size", type=int, default=50, help="Symbols per Yahoo download batch")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of symbols (for testing)")
    return parser.parse_args()


def _load_symbols_from_file(path: str) -> List[str]:
    if not path:
        return []
    text = pathlib.Path(path).read_text(encoding="utf-8")
    raw = text.replace("\n", ",").replace("\r", ",")
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def resolve_symbols(symbols_arg: str, symbols_file: str, preset: str) -> List[str]:
    symbols = []
    if symbols_file:
        symbols = _load_symbols_from_file(symbols_file)
    if not symbols:
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
        if isinstance(col, tuple):
            col_value = col[0]
        else:
            col_value = col
        col_name = str(col_value).strip().lower().replace(" ", "_")
        if col_name == "adj_close":
            columns.append("adj_close")
        else:
            columns.append(col_name)
    df = df.copy()
    df.columns = columns
    if "adj_close" not in df.columns and "close" in df.columns:
        df["adj_close"] = df["close"]
    return df


def _split_by_symbol(df: pd.DataFrame, symbols: List[str]) -> Dict[str, pd.DataFrame]:
    if not isinstance(df.columns, pd.MultiIndex):
        if len(symbols) == 1:
            return {symbols[0]: _standardize_columns(df)}
        return {symbol: _standardize_columns(df) for symbol in symbols}

    level_matches = []
    for level_idx in range(df.columns.nlevels):
        level_values = set(map(str, df.columns.get_level_values(level_idx)))
        level_matches.append(sum(1 for symbol in symbols if symbol in level_values))
    ticker_level = level_matches.index(max(level_matches)) if level_matches else 0

    data: Dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        if symbol not in df.columns.get_level_values(ticker_level):
            continue
        sub = df.xs(symbol, level=ticker_level, axis=1)
        data[symbol] = _standardize_columns(sub)
    return data


def fetch_yahoo(symbols: List[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
    df = yf.download(
        tickers=" ".join(symbols),
        start=start,
        end=end,
        auto_adjust=False,
        actions=False,
        progress=False,
        group_by="ticker",
        threads=False,
    )
    return _split_by_symbol(df, symbols)


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


async def fetch_min_dates(
    conn: asyncpg.Connection, symbols: List[str]
) -> Dict[str, date]:
    if not symbols:
        return {}
    rows = await conn.fetch(
        "select symbol, min(price_date) as min_date from market_prices where symbol = any($1) group by symbol",
        symbols,
    )
    return {row["symbol"]: row["min_date"] for row in rows if row["min_date"]}


async def main() -> None:
    load_env()
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is not set", file=sys.stderr)
        sys.exit(1)

    args = parse_args()
    symbols = resolve_symbols(args.symbols, args.symbols_file, args.preset)
    if args.limit and args.limit > 0:
        symbols = symbols[: args.limit]
    start = args.start
    end = args.end or date.today().isoformat()
    if args.years and args.years > 0:
        today = date.today()
        try:
            start = today.replace(year=today.year - args.years).isoformat()
        except ValueError:
            start = today.replace(year=today.year - args.years, day=28).isoformat()

    yahoo_symbols = [s.replace(".", "-") for s in symbols]
    symbol_map = {yahoo: original for yahoo, original in zip(yahoo_symbols, symbols)}

    print(f"Fetching Yahoo Finance data: {len(symbols)} symbols, {start} -> {end}")
    dsn = normalize_dsn(dsn)
    conn = await asyncpg.connect(dsn)
    try:
        if args.backfill:
            min_dates = await fetch_min_dates(conn, symbols)
            target_start = date.fromisoformat(start)
            for symbol in symbols:
                min_date = min_dates.get(symbol)
                if min_date and min_date <= target_start:
                    print(f"{symbol}: already has data back to {min_date}, skip")
                    continue
                range_end = min_date.isoformat() if min_date else end
                yahoo_symbol = symbol.replace(".", "-")
                data = fetch_yahoo([yahoo_symbol], start, range_end)
                df = data.get(yahoo_symbol)
                if df is None:
                    print(f"{symbol}: no data")
                    continue
                rows = list(iter_rows(symbol, df))
                print(f"{symbol}: {len(rows)} rows ({start} -> {range_end})")
                for j in range(0, len(rows), args.batch_size):
                    batch = rows[j : j + args.batch_size]
                    await upsert_rows(conn, batch)
        else:
            for i in range(0, len(yahoo_symbols), args.chunk_size):
                chunk = yahoo_symbols[i : i + args.chunk_size]
                data = fetch_yahoo(chunk, start, end)
                for yahoo_symbol, df in data.items():
                    symbol = symbol_map.get(yahoo_symbol, yahoo_symbol)
                    rows = list(iter_rows(symbol, df))
                    print(f"{symbol}: {len(rows)} rows")
                    for j in range(0, len(rows), args.batch_size):
                        batch = rows[j : j + args.batch_size]
                        await upsert_rows(conn, batch)
    finally:
        await conn.close()

    print("Ingestion completed.")


if __name__ == "__main__":
    asyncio.run(main())
