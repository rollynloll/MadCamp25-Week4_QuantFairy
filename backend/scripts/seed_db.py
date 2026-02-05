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
                "backtest_runs",
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

        public_seeds = [
            {
                "public_strategy_id": "momentum_top10_12m_v1",
                "name": "Momentum Top-10 (12M)",
                "one_liner": "Top-N by 12M return, monthly rebalance",
                "one_liner_ko": "12개월 수익률 상위 N개를 매수하고 월간 리밸런싱",
                "category": "momentum",
                "tags": ["momentum", "cross-sectional"],
                "risk_level": "mid",
                "version": "1.0.0",
                "author_name": "QuantFairy",
                "author_type": "official",
                "rules": {
                    "signal_definition": "Rank by 12M return",
                    "entry_rules": "Buy top-N",
                    "exit_rules": "Sell at rebalance",
                    "rebalance_rule": "Monthly",
                    "position_sizing": "Equal weight",
                },
                "requirements": {
                    "universe": {"min_symbols": 20, "max_symbols": 500, "supports_custom_tickers": True},
                    "data": {"required_fields": ["adj_close"], "warmup_lookback_days": 252},
                },
                "param_schema": {
                    "type": "object",
                    "properties": {
                        "lookback_days": {"type": "integer", "minimum": 60, "maximum": 504, "default": 252},
                        "top_n": {"type": "integer", "minimum": 5, "maximum": 50, "default": 10},
                        "rebalance": {"type": "string", "enum": ["monthly"], "default": "monthly"},
                    },
                    "required": ["lookback_days", "top_n"],
                },
                "default_params": {"lookback_days": 252, "top_n": 10, "rebalance": "monthly"},
                "supported_assets": ["US_Equity"],
                "supported_timeframes": ["1D"],
                "full_description": (
                    "This strategy ranks the universe by 12-month total return and buys the top N names. "
                    "It rebalances monthly and equal-weights positions, replacing laggards with new leaders. "
                    "It is designed for diversified large-cap universes and can be vulnerable during sharp momentum reversals."
                ),
                "full_description_ko": (
                    "이 전략은 12개월 누적 수익률로 종목을 순위화해 상위 N개를 매수합니다. "
                    "매달 리밸런싱하며 동일 비중으로 보유하고, 성과가 떨어진 종목은 새로운 상위 종목으로 교체합니다. "
                    "대형주 분산 유니버스에 적합하지만 모멘텀 급반전 구간에서는 손실이 커질 수 있습니다."
                ),
                "thesis": (
                    "Persistent relative strength can be harvested by periodically rotating into recent winners while keeping turnover manageable."
                ),
                "thesis_ko": "최근 강세 종목의 상대적 강도를 활용하되, 월 단위 교체로 과도한 회전율을 줄입니다.",
                "known_failure_modes": ["Sideways markets", "Regime shifts"],
                "risk_disclaimer": "Backtests are illustrative and not investment advice.",
                "sample_backtest_spec": {
                    "period_start": "2010-01-01",
                    "period_end": "2024-12-31",
                    "timeframe": "1D",
                    "universe_used": "US_CORE_20",
                    "initial_cash": 100000,
                    "fee_bps": 1,
                    "slippage_bps": 2,
                },
                "entrypoint": "strategies.momentum_topn_v1:MomentumTopNStrategy",
                "code_version": "seed",
                "sample_metrics": {
                    "pnl_amount": 15600.0,
                    "pnl_pct": 15.6,
                    "sharpe": 1.4,
                    "max_drawdown_pct": -4.2,
                    "win_rate_pct": 58.2,
                },
                "sample_trade_stats": {"trades_count": 120, "avg_hold_hours": 36},
                "updated_at": iso(now_kst()),
            },
            {
                "public_strategy_id": "trend_sma200_v1",
                "name": "Trend SMA200",
                "one_liner": "Risk-on above 200D SMA, else cash",
                "one_liner_ko": "벤치마크가 200일 이동평균 위이면 위험자산, 아래면 현금",
                "category": "trend",
                "tags": ["trend", "sma"],
                "risk_level": "low",
                "version": "1.0.0",
                "author_name": "QuantFairy",
                "author_type": "official",
                "rules": {
                    "signal_definition": "Price above SMA200",
                    "entry_rules": "Risk-on",
                    "exit_rules": "Risk-off to cash",
                    "rebalance_rule": "Daily",
                    "position_sizing": "All-in",
                },
                "requirements": {
                    "universe": {"min_symbols": 1, "max_symbols": 1, "supports_custom_tickers": False},
                    "data": {"required_fields": ["adj_close"], "warmup_lookback_days": 200},
                },
                "param_schema": {
                    "type": "object",
                    "properties": {
                        "benchmark_symbol": {"type": "string", "default": "SPY"},
                        "sma_window": {"type": "integer", "minimum": 100, "maximum": 300, "default": 200},
                    },
                    "required": ["benchmark_symbol", "sma_window"],
                },
                "default_params": {"benchmark_symbol": "SPY", "sma_window": 200},
                "supported_assets": ["US_Equity"],
                "supported_timeframes": ["1D"],
                "full_description": (
                    "A simple trend filter on the benchmark: if price is above the 200-day moving average, "
                    "the strategy stays invested; if below, it shifts to cash. The signal is checked daily "
                    "to reduce drawdowns in prolonged bear markets. It can underperform in sideways markets due to whipsaws."
                ),
                "full_description_ko": (
                    "벤치마크가 200일 이동평균 위에 있으면 위험자산을 보유하고, 아래로 내려가면 현금으로 전환하는 단순 추세 필터입니다. "
                    "일별로 신호를 확인해 하락장 손실을 줄이는 데 도움이 될 수 있습니다. "
                    "횡보장에서는 잦은 신호 전환으로 성과가 약해질 수 있습니다."
                ),
                "thesis": "Long-term moving averages help separate trending regimes from risk-off periods.",
                "thesis_ko": "장기 이동평균을 통해 추세 구간과 위험 구간을 구분합니다.",
                "known_failure_modes": ["Whipsaws in choppy regimes"],
                "risk_disclaimer": "Backtests are illustrative and not investment advice.",
                "sample_backtest_spec": {
                    "period_start": "2008-01-01",
                    "period_end": "2024-12-31",
                    "timeframe": "1D",
                    "universe_used": "SPY",
                    "initial_cash": 100000,
                    "fee_bps": 1,
                    "slippage_bps": 2,
                },
                "entrypoint": "strategies.trend_sma200_v1:TrendSMA200Strategy",
                "code_version": "seed",
                "sample_metrics": {
                    "pnl_amount": 8200.0,
                    "pnl_pct": 8.2,
                    "sharpe": 0.9,
                    "max_drawdown_pct": -8.8,
                    "win_rate_pct": 52.1,
                },
                "sample_trade_stats": {"trades_count": 40, "avg_hold_hours": 240},
                "updated_at": iso(now_kst()),
            },
            {
                "public_strategy_id": "rsi_mean_reversion_v1",
                "name": "RSI Mean Reversion",
                "one_liner": "Buy RSI < 30, exit RSI > 50",
                "one_liner_ko": "RSI가 30 아래면 매수, 50 위면 청산",
                "category": "mean_reversion",
                "tags": ["rsi", "mean_reversion"],
                "risk_level": "mid",
                "version": "1.0.0",
                "author_name": "QuantFairy",
                "author_type": "official",
                "rules": {
                    "signal_definition": "RSI threshold",
                    "entry_rules": "RSI < 30 buy",
                    "exit_rules": "RSI > 50 sell",
                    "rebalance_rule": "Daily",
                },
                "requirements": {
                    "universe": {"min_symbols": 1, "max_symbols": 1, "supports_custom_tickers": True},
                    "data": {"required_fields": ["adj_close"], "warmup_lookback_days": 30},
                },
                "param_schema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "default": "SPY"},
                        "rsi_window": {"type": "integer", "minimum": 7, "maximum": 30, "default": 14},
                        "entry_rsi": {"type": "number", "minimum": 10, "maximum": 40, "default": 30},
                        "exit_rsi": {"type": "number", "minimum": 40, "maximum": 70, "default": 50},
                    },
                    "required": ["symbol", "rsi_window", "entry_rsi", "exit_rsi"],
                },
                "default_params": {"symbol": "SPY", "rsi_window": 14, "entry_rsi": 30, "exit_rsi": 50},
                "supported_assets": ["US_Equity"],
                "supported_timeframes": ["1D"],
                "full_description": (
                    "This mean reversion strategy uses RSI on a single benchmark (default SPY). "
                    "It buys when RSI falls below the entry threshold and exits when RSI rebounds above the exit level. "
                    "It tends to work best in range-bound markets and can struggle during strong trends."
                ),
                "full_description_ko": (
                    "단일 벤치마크(기본 SPY)에 RSI를 적용하는 평균회귀 전략입니다. "
                    "RSI가 진입 기준 아래로 내려가면 매수하고, 반등해 종료 기준을 넘으면 매도합니다. "
                    "횡보장에서 유리하지만 강한 추세에서는 손실이 커질 수 있습니다."
                ),
                "thesis": "Short-term oversold conditions often revert toward the mean.",
                "thesis_ko": "단기 과매도 구간은 평균으로 되돌아갈 가능성이 높습니다.",
                "known_failure_modes": ["Strong trend markets"],
                "risk_disclaimer": "Backtests are illustrative and not investment advice.",
                "sample_backtest_spec": {
                    "period_start": "2015-01-01",
                    "period_end": "2024-12-31",
                    "timeframe": "1D",
                    "universe_used": "SPY",
                    "initial_cash": 100000,
                    "fee_bps": 1,
                    "slippage_bps": 2,
                },
                "entrypoint": "strategies.rsi_mean_reversion_v1:RSIMeanReversionStrategy",
                "code_version": "seed",
                "sample_metrics": {
                    "pnl_amount": 6400.0,
                    "pnl_pct": 6.4,
                    "sharpe": 0.7,
                    "max_drawdown_pct": -10.2,
                    "win_rate_pct": 49.5,
                },
                "sample_trade_stats": {"trades_count": 60, "avg_hold_hours": 72},
                "updated_at": iso(now_kst()),
            },
        ]

        for seed in public_seeds:
            await upsert(
                conn,
                "public_strategies",
                seed,
                ["public_strategy_id"],
                [
                    "name",
                    "one_liner",
                    "one_liner_ko",
                    "category",
                    "tags",
                    "risk_level",
                    "version",
                    "author_name",
                    "author_type",
                    "full_description",
                    "full_description_ko",
                    "thesis",
                    "thesis_ko",
                    "rules",
                    "requirements",
                    "param_schema",
                    "default_params",
                    "supported_assets",
                    "supported_timeframes",
                    "known_failure_modes",
                    "risk_disclaimer",
                    "sample_backtest_spec",
                    "sample_metrics",
                    "sample_trade_stats",
                    "entrypoint",
                    "code_version",
                    "updated_at",
                ],
            )

        await upsert(
            conn,
            "user_strategies",
            {
                "strategy_id": "strat_momentum_top10",
                "user_id": user_id,
                "source_public_strategy_id": "momentum_top10_12m_v1",
                "public_version_snapshot": "1.0.0",
                "entrypoint_snapshot": "strategies.momentum_topn_v1:MomentumTopNStrategy",
                "code_version_snapshot": "seed",
                "name": "Momentum Breakout",
                "state": "running",
                "description": "Top-10 momentum breakout strategy",
                "params": {"lookback_days": 252, "top_n": 10, "rebalance": "monthly"},
                "risk_limits": {"max_position_pct": 20},
                "positions_count": 2,
                "pnl_today_value": 1240.2,
                "pnl_today_pct": 1.24,
                "updated_at": iso(now_kst()),
            },
            ["strategy_id"],
            [
                "user_id",
                "source_public_strategy_id",
                "public_version_snapshot",
                "entrypoint_snapshot",
                "code_version_snapshot",
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
                "source_public_strategy_id": None,
                "public_version_snapshot": None,
                "entrypoint_snapshot": None,
                "code_version_snapshot": None,
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
                "source_public_strategy_id",
                "public_version_snapshot",
                "entrypoint_snapshot",
                "code_version_snapshot",
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
        alter table if exists backtest_runs drop constraint if exists backtest_runs_user_id_fkey;

        alter table if exists user_strategies
          add constraint user_strategies_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        alter table if exists user_strategies
          add column if not exists source_public_strategy_id text;
        alter table if exists user_strategies
          add column if not exists public_version_snapshot text;
        alter table if exists user_strategies
          add column if not exists entrypoint_snapshot text;
        alter table if exists user_strategies
          add column if not exists code_version_snapshot text;
        alter table if exists user_strategies
          add column if not exists note text;
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
        alter table if exists backtest_runs
          add constraint backtest_runs_user_id_fkey
          foreign key (user_id) references app_users(id) on delete cascade;
        """
    )


if __name__ == "__main__":
    asyncio.run(main())
