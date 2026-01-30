import asyncio
import os
import pathlib
import sys

import asyncpg
from dotenv import load_dotenv


def normalize_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+asyncpg://"):
        return "postgresql://" + dsn[len("postgresql+asyncpg://") :]
    if dsn.startswith("postgres+asyncpg://"):
        return "postgresql://" + dsn[len("postgres+asyncpg://") :]
    return dsn


async def main() -> None:
    env_path = pathlib.Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is not set", file=sys.stderr)
        sys.exit(1)

    dsn = normalize_dsn(dsn)
    sql_path = pathlib.Path(__file__).resolve().parents[1] / "sql" / "schema.sql"
    sql = sql_path.read_text(encoding="utf-8")

    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute(sql)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
