from __future__ import annotations

from typing import Any

from app.alpaca.client import AlpacaClient
from app.core.ttl_cache import TTLCache


ACCOUNT_CACHE_TTL = 10.0
POSITIONS_CACHE_TTL = 10.0
HISTORY_CACHE_TTL = 15.0

ALPACA_CACHE = TTLCache(default_ttl=10.0, maxsize=256)


def _cache_key(prefix: str, env: str, *parts: str) -> str:
    suffix = ":".join(parts) if parts else ""
    return f"{prefix}:{env}:{suffix}"


def get_account_cached(client: AlpacaClient):
    key = _cache_key("alpaca:account", client.environment)
    cached = ALPACA_CACHE.get(key)
    if cached is not None:
        return cached
    result = client.get_account()
    if result.account is not None:
        ALPACA_CACHE.set(key, result, ttl=ACCOUNT_CACHE_TTL)
    return result


def get_positions_cached(client: AlpacaClient):
    key = _cache_key("alpaca:positions", client.environment)
    cached = ALPACA_CACHE.get(key)
    if cached is not None:
        return cached
    result = client.get_positions()
    if result is not None:
        ALPACA_CACHE.set(key, result, ttl=POSITIONS_CACHE_TTL)
    return result


def get_history_cached(client: AlpacaClient, period: str | None, timeframe: str | None):
    key = _cache_key(
        "alpaca:history",
        client.environment,
        period or "default",
        timeframe or "default",
    )
    cached = ALPACA_CACHE.get(key)
    if cached is not None:
        return cached
    result = client.get_portfolio_history(period=period, timeframe=timeframe)
    if result is not None:
        ALPACA_CACHE.set(key, result, ttl=HISTORY_CACHE_TTL)
    return result
