from __future__ import annotations

import os
from typing import AsyncGenerator

import asyncpg


_pool: asyncpg.Pool | None = None


def _get_dsn() -> str:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set")
    return dsn


async def init_db() -> None:
    global _pool
    if _pool is not None:
        return
    dsn = _get_dsn()
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10)


async def close_db() -> None:
    global _pool
    if _pool is None:
        return
    await _pool.close()
    _pool = None


async def get_db_pool() -> asyncpg.Pool:
    if _pool is None:
        await init_db()
    assert _pool is not None
    return _pool


async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        yield conn
