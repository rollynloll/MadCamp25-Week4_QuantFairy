import asyncio
import os
import pathlib
import json
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import asyncpg
from dotenv import load_dotenv


KST = ZoneInfo("Asia/Seoul")


def normalize_dsn(dsn: str) -> str:
    if dsn.startswith("postgresql+asyncpg://"):
        return "postgresql://" + dsn[len("postgresql+asyncpg://") :]
    if dsn.startswith("postgres+asyncpg://"):
        return "postgresql://" + dsn[len("postgres+asyncpg://") :]
    return dsn


def now_kst() -> datetime:
    return datetime.now(tz=KST)


def iso(dt: datetime) -> datetime:
    return dt


def make_equity_curve(days: int = 30, base: float = 100000.0) -> list[dict]:
    points = []
    for i in range(days):
        t = now_kst() - timedelta(days=days - 1 - i)
        equity = base * (1 + 0.002 * i)
        points.append({"as_of": iso(t), "equity": equity, "cash": base * 0.25})
    return points


async def upsert(conn, table: str, data: dict, conflict_cols: list[str], update_cols: list[str]):
    cols = list(data.keys())
    values = [_encode_value(data[c]) for c in cols]
    placeholders = ", ".join(f"${i}" for i in range(1, len(cols) + 1))
    if update_cols:
        set_clause = ", ".join(f"{c}=EXCLUDED.{c}" for c in update_cols)
        query = (
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT ({', '.join(conflict_cols)}) DO UPDATE SET {set_clause}"
        )
    else:
        query = (
            f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
            f"ON CONFLICT ({', '.join(conflict_cols)}) DO NOTHING"
        )
    await conn.execute(query, *values)


async def insert_many(conn, table: str, rows: list[dict]):
    if not rows:
        return
    cols = list(rows[0].keys())
    placeholders = ", ".join(f"${i}" for i in range(1, len(cols) + 1))
    query = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    for row in rows:
        values = [_encode_value(row[c]) for c in cols]
        await conn.execute(query, *values)


def _encode_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return value


async def main() -> None:
    env_path = pathlib.Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL is not set")

    dsn = normalize_dsn(dsn)
    user_id = os.getenv("DEFAULT_USER_ID") or str(uuid.uuid4())
    environment = os.getenv("SEED_ENVIRONMENT", "paper")
    reset = os.getenv("SEED_RESET", "false").lower() in {"1", "true", "yes"}

    conn = await asyncpg.connect(dsn)
    try:
        await _ensure_app_users_schema(conn)
        if reset:
            for table in (
                "bot_runs",
                "orders",
                "alerts",
                "trades",
                "positions",
                "portfolio_snapshots",
                "user_accounts",
                "user_settings",
                "user_strategies",
            ):
                await conn.execute(
                    f"DELETE FROM {table} WHERE user_id = $1", user_id
                )

        await upsert(
            conn,
            "app_users",
            {
                "id": user_id,
                "display_name": "Default User",
                "email": None,
                "created_at": iso(now_kst()),
                "updated_at": iso(now_kst()),
            },
            ["id"],
            ["display_name", "email", "updated_at"],
        )

        await upsert(
            conn,
            "strategy_templates",
            {
                "template_id": "tmpl_momentum_top10",
                "name": "Momentum Breakout",
                "description": "Top-10 momentum breakout strategy",
                "params_schema": {"rebalance": "weekly", "universe": "int"},
                "risk_schema": {"max_position_pct": "number"},
                "is_active": True,
                "updated_at": iso(now_kst()),
            },
            ["template_id"],
            ["name", "description", "params_schema", "risk_schema", "is_active", "updated_at"],
        )

        await upsert(
            conn,
            "strategy_templates",
            {
                "template_id": "tmpl_mean_reversion",
                "name": "Mean Reversion Alpha",
                "description": "Mean reversion on large cap universe",
                "params_schema": {"lookback_days": "int"},
                "risk_schema": {"max_loss_pct": "number"},
                "is_active": True,
                "updated_at": iso(now_kst()),
            },
            ["template_id"],
            ["name", "description", "params_schema", "risk_schema", "is_active", "updated_at"],
        )

        await upsert(
            conn,
            "user_strategies",
            {
                "strategy_id": "strat_momentum_top10",
                "user_id": user_id,
                "template_id": "tmpl_momentum_top10",
                "name": "Momentum Breakout",
                "state": "running",
                "description": "Top-10 momentum breakout strategy",
                "params": {"rebalance": "weekly", "universe": 10},
                "risk_limits": {"max_position_pct": 20},
                "positions_count": 2,
                "pnl_today_value": 1240.2,
                "pnl_today_pct": 1.24,
                "updated_at": iso(now_kst()),
            },
            ["strategy_id"],
            [
                "user_id",
                "template_id",
                "name",
                "state",
                "description",
                "params",
                "risk_limits",
                "positions_count",
                "pnl_today_value",
                "pnl_today_pct",
                "updated_at",
            ],
        )

        await upsert(
            conn,
            "user_strategies",
            {
                "strategy_id": "strat_mean_reversion",
                "user_id": user_id,
                "template_id": "tmpl_mean_reversion",
                "name": "Mean Reversion Alpha",
                "state": "paused",
                "description": "Mean reversion on large cap universe",
                "params": {"lookback_days": 20},
                "risk_limits": {"max_loss_pct": 5},
                "positions_count": 1,
                "pnl_today_value": -120.5,
                "pnl_today_pct": -0.12,
                "updated_at": iso(now_kst()),
            },
            ["strategy_id"],
            [
                "user_id",
                "template_id",
                "name",
                "state",
                "description",
                "params",
                "risk_limits",
                "positions_count",
                "pnl_today_value",
                "pnl_today_pct",
                "updated_at",
            ],
        )

        await upsert(
            conn,
            "user_settings",
            {
                "user_id": user_id,
                "environment": environment,
                "kill_switch": False,
                "kill_switch_reason": None,
                "bot_state": "running",
                "next_run_at": iso(now_kst() + timedelta(hours=1)),
                "updated_at": iso(now_kst()),
            },
            ["user_id"],
            [
                "environment",
                "kill_switch",
                "kill_switch_reason",
                "bot_state",
                "next_run_at",
                "updated_at",
            ],
        )

        await upsert(
            conn,
            "user_accounts",
            {
                "account_id": "alpaca_account",
                "user_id": user_id,
                "broker": "alpaca",
                "environment": environment,
                "equity": 100000.0,
                "cash": 25000.0,
                "buying_power": 75000.0,
                "currency": "USD",
                "updated_at": iso(now_kst()),
            },
            ["account_id"],
            [
                "user_id",
                "broker",
                "environment",
                "equity",
                "cash",
                "buying_power",
                "currency",
                "updated_at",
            ],
        )

        equity_rows = [
            {
                "user_id": user_id,
                "environment": environment,
                **point,
                "created_at": iso(now_kst()),
            }
            for point in make_equity_curve()
        ]
        if reset:
            await conn.execute(
                "DELETE FROM portfolio_snapshots WHERE user_id = $1 AND environment = $2",
                user_id,
                environment,
            )
        await insert_many(conn, "portfolio_snapshots", equity_rows)

        if reset:
            await conn.execute(
                "DELETE FROM positions WHERE user_id = $1 AND environment = $2",
                user_id,
                environment,
            )
        await insert_many(
            conn,
            "positions",
            [
                {
                    "user_id": user_id,
                    "environment": environment,
                    "symbol": "AAPL",
                    "qty": 100,
                    "avg_entry_price": 175.0,
                    "unrealized_pnl": 320.5,
                    "strategy_id": "strat_mean_reversion",
                    "updated_at": iso(now_kst()),
                },
                {
                    "user_id": user_id,
                    "environment": environment,
                    "symbol": "TSLA",
                    "qty": 50,
                    "avg_entry_price": 210.0,
                    "unrealized_pnl": -120.0,
                    "strategy_id": "strat_momentum_top10",
                    "updated_at": iso(now_kst()),
                },
            ],
        )

        await upsert(
            conn,
            "trades",
            {
                "fill_id": "fill_001",
                "user_id": user_id,
                "environment": environment,
                "filled_at": iso(now_kst() - timedelta(minutes=35)),
                "symbol": "AAPL",
                "side": "buy",
                "qty": 100,
                "price": 178.25,
                "strategy_id": "strat_mean_reversion",
                "strategy_name": "Mean Reversion Alpha",
            },
            ["fill_id"],
            ["user_id", "environment", "filled_at", "symbol", "side", "qty", "price", "strategy_id", "strategy_name"],
        )

        await upsert(
            conn,
            "trades",
            {
                "fill_id": "fill_002",
                "user_id": user_id,
                "environment": environment,
                "filled_at": iso(now_kst() - timedelta(minutes=20)),
                "symbol": "TSLA",
                "side": "sell",
                "qty": 50,
                "price": 242.18,
                "strategy_id": "strat_momentum_top10",
                "strategy_name": "Momentum Breakout",
            },
            ["fill_id"],
            ["user_id", "environment", "filled_at", "symbol", "side", "qty", "price", "strategy_id", "strategy_name"],
        )

        await upsert(
            conn,
            "alerts",
            {
                "alert_id": "alert_001",
                "user_id": user_id,
                "severity": "warning",
                "type": "risk_limit_hit",
                "title": "Max per-symbol exposure hit",
                "message": "TSLA order blocked by risk limit",
                "occurred_at": iso(now_kst() - timedelta(minutes=10)),
                "link": {"page": "trading", "tab": "risk"},
            },
            ["alert_id"],
            ["user_id", "severity", "type", "title", "message", "occurred_at", "link"],
        )

        await upsert(
            conn,
            "orders",
            {
                "order_id": "order_001",
                "user_id": user_id,
                "environment": environment,
                "symbol": "AAPL",
                "side": "buy",
                "qty": 100,
                "type": "market",
                "status": "filled",
                "submitted_at": iso(now_kst() - timedelta(minutes=36)),
                "filled_at": iso(now_kst() - timedelta(minutes=35)),
                "strategy_id": "strat_mean_reversion",
            },
            ["order_id"],
            ["user_id", "environment", "symbol", "side", "qty", "type", "status", "submitted_at", "filled_at", "strategy_id"],
        )

        await upsert(
            conn,
            "bot_runs",
            {
                "run_id": "run_seed",
                "user_id": user_id,
                "started_at": iso(now_kst() - timedelta(hours=1)),
                "ended_at": iso(now_kst() - timedelta(hours=1) + timedelta(minutes=2)),
                "result": "success",
                "orders_created": 1,
                "orders_failed": 0,
                "detail": {"note": "seed run"},
            },
            ["run_id"],
            ["user_id", "started_at", "ended_at", "result", "orders_created", "orders_failed", "detail"],
        )

        print("Seed complete")
        print(f"user_id: {user_id}")
        if not os.getenv("DEFAULT_USER_ID"):
            print("Tip: set DEFAULT_USER_ID in .env to reuse this user.")
    finally:
        await conn.close()


async def _ensure_app_users_schema(conn) -> None:
    await conn.execute(
        """
        create table if not exists app_users (
          id uuid primary key,
          auth_user_id uuid unique references auth.users(id) on delete set null,
          display_name text,
          email text,
          created_at timestamptz not null default now(),
          updated_at timestamptz not null default now()
        );
        create index if not exists idx_app_users_auth_user_id on app_users(auth_user_id);

        alter table if exists user_strategies drop constraint if exists user_strategies_user_id_fkey;
        alter table if exists user_settings drop constraint if exists user_settings_user_id_fkey;
        alter table if exists user_accounts drop constraint if exists user_accounts_user_id_fkey;
        alter table if exists portfolio_snapshots drop constraint if exists portfolio_snapshots_user_id_fkey;
        alter table if exists positions drop constraint if exists positions_user_id_fkey;
        alter table if exists trades drop constraint if exists trades_user_id_fkey;
        alter table if exists alerts drop constraint if exists alerts_user_id_fkey;
        alter table if exists orders drop constraint if exists orders_user_id_fkey;
        alter table if exists bot_runs drop constraint if exists bot_runs_user_id_fkey;

        alter table if exists user_strategies
          add constraint user_strategies_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        alter table if exists user_settings
          add constraint user_settings_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        alter table if exists user_settings
          add column if not exists kill_switch_reason text;
        alter table if exists user_accounts
          add constraint user_accounts_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        alter table if exists portfolio_snapshots
          add constraint portfolio_snapshots_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        alter table if exists positions
          add constraint positions_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        alter table if exists trades
          add constraint trades_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        alter table if exists alerts
          add constraint alerts_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        alter table if exists orders
          add constraint orders_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        alter table if exists bot_runs
          add constraint bot_runs_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        """
    )


if __name__ == "__main__":
    asyncio.run(main())
