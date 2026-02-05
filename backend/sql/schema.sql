-- Application users (independent from auth for now)
create table if not exists app_users (
  id uuid primary key,
  auth_user_id uuid unique references auth.users(id) on delete set null,
  display_name text,
  email text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_app_users_auth_user_id on app_users(auth_user_id);

-- Public Strategies API v1
create table if not exists public_strategies (
  public_strategy_id text primary key,
  name text not null,
  one_liner text,
  one_liner_ko text,
  category text,
  tags jsonb not null default '[]'::jsonb,
  risk_level text not null default 'mid',
  version text not null default '1.0.0',
  author_name text not null default '',
  author_type text not null default 'official',
  sample_metrics jsonb not null default '{}'::jsonb,
  sample_trade_stats jsonb not null default '{}'::jsonb,
  adds_count int not null default 0,
  likes_count int not null default 0,
  runs_count int not null default 0,
  supported_assets jsonb not null default '[]'::jsonb,
  supported_timeframes jsonb not null default '[]'::jsonb,
  full_description text,
  full_description_ko text,
  thesis text,
  thesis_ko text,
  rules jsonb not null default '{}'::jsonb,
  param_schema jsonb not null default '{}'::jsonb,
  default_params jsonb not null default '{}'::jsonb,
  recommended_presets jsonb not null default '[]'::jsonb,
  requirements jsonb not null default '{}'::jsonb,
  sample_backtest_spec jsonb not null default '{}'::jsonb,
  sample_performance jsonb not null default '{}'::jsonb,
  known_failure_modes jsonb not null default '[]'::jsonb,
  risk_disclaimer text,
  entrypoint text,
  code_version text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Migrations for existing public_strategies
alter table if exists public_strategies add column if not exists entrypoint text;
alter table if exists public_strategies add column if not exists code_version text;
alter table if exists public_strategies add column if not exists one_liner_ko text;
alter table if exists public_strategies add column if not exists full_description_ko text;
alter table if exists public_strategies add column if not exists thesis_ko text;

create index if not exists idx_public_strategies_updated_at on public_strategies(updated_at);
create index if not exists idx_public_strategies_adds_count on public_strategies(adds_count);
create index if not exists idx_public_strategies_name on public_strategies(name);

-- User strategies (instances)
create table if not exists user_strategies (
  strategy_id text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  source_public_strategy_id text references public_strategies(public_strategy_id) on delete set null,
  public_version_snapshot text,
  entrypoint_snapshot text,
  code_version_snapshot text,
  name text not null,
  state text not null default 'idle',
  description text,
  params jsonb not null default '{}'::jsonb,
  risk_limits jsonb not null default '{}'::jsonb,
  positions_count int not null default 0,
  pnl_today_value numeric not null default 0,
  pnl_today_pct numeric not null default 0,
  note text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Migrations for existing user_strategies (adds new columns)
alter table if exists user_strategies add column if not exists source_public_strategy_id text;
alter table if exists user_strategies add column if not exists public_version_snapshot text;
alter table if exists user_strategies add column if not exists entrypoint_snapshot text;
alter table if exists user_strategies add column if not exists code_version_snapshot text;
alter table if exists user_strategies add column if not exists note text;

create index if not exists idx_user_strategies_user_id on user_strategies(user_id);
create index if not exists idx_user_strategies_user_state on user_strategies(user_id, state);
create index if not exists idx_user_strategies_source_public_id on user_strategies(source_public_strategy_id);

-- User settings
create table if not exists user_settings (
  user_id uuid primary key references app_users(id) on delete cascade,
  environment text not null default 'paper',
  kill_switch boolean not null default false,
  kill_switch_reason text,
  bot_state text not null default 'running',
  next_run_at timestamptz,
  updated_at timestamptz not null default now()
);

-- User accounts (latest broker snapshot)
create table if not exists user_accounts (
  account_id text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  broker text not null default 'alpaca',
  environment text not null default 'paper',
  equity numeric not null default 0,
  cash numeric not null default 0,
  buying_power numeric not null default 0,
  currency text not null default 'USD',
  updated_at timestamptz not null default now()
);

create index if not exists idx_user_accounts_user_env on user_accounts(user_id, environment);

-- Portfolio snapshots
create table if not exists portfolio_snapshots (
  snapshot_id bigserial primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  environment text not null default 'paper',
  as_of timestamptz not null,
  equity numeric not null default 0,
  cash numeric not null default 0,
  created_at timestamptz not null default now()
);

create index if not exists idx_portfolio_snapshots_user_env_asof on portfolio_snapshots(user_id, environment, as_of);

-- Positions
create table if not exists positions (
  position_id bigserial primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  environment text not null default 'paper',
  symbol text not null,
  qty numeric not null default 0,
  avg_entry_price numeric not null default 0,
  unrealized_pnl numeric not null default 0,
  strategy_id text references user_strategies(strategy_id),
  updated_at timestamptz not null default now()
);

create index if not exists idx_positions_user_env on positions(user_id, environment);
create index if not exists idx_positions_user_symbol on positions(user_id, symbol);

-- Trades (fills)
create table if not exists trades (
  fill_id text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  environment text not null default 'paper',
  filled_at timestamptz not null,
  symbol text not null,
  side text not null,
  qty numeric not null,
  price numeric not null,
  strategy_id text,
  strategy_name text
);

create index if not exists idx_trades_user_env_filled on trades(user_id, environment, filled_at desc);

-- Alerts
create table if not exists alerts (
  alert_id text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  severity text not null,
  type text not null,
  title text not null,
  message text,
  occurred_at timestamptz not null,
  link jsonb
);

create index if not exists idx_alerts_user_occured on alerts(user_id, occurred_at desc);

-- Orders
create table if not exists orders (
  order_id text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  environment text not null default 'paper',
  symbol text not null,
  side text not null,
  qty numeric not null,
  type text not null,
  status text not null,
  submitted_at timestamptz,
  filled_at timestamptz,
  strategy_id text
);

create index if not exists idx_orders_user_env_submitted on orders(user_id, environment, submitted_at desc);

alter table if exists orders add column if not exists rebalance_run_id text;
alter table if exists orders add column if not exists source text not null default 'rebalance';
alter table if exists orders add column if not exists requested_notional numeric;
alter table if exists orders add column if not exists estimated_price numeric;
create index if not exists idx_orders_rebalance_run_id on orders(rebalance_run_id);

-- Rebalance targets (latest target allocation saved from Portfolio)
create table if not exists rebalance_targets (
  target_id bigserial primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  environment text not null default 'paper',
  strategy_id text not null references user_strategies(strategy_id) on delete cascade,
  target_weight_pct numeric not null default 0,
  target_cash_pct numeric not null default 0,
  updated_at timestamptz not null default now()
);

create unique index if not exists uq_rebalance_targets_user_env_strategy
  on rebalance_targets(user_id, environment, strategy_id);
create index if not exists idx_rebalance_targets_user_env
  on rebalance_targets(user_id, environment, updated_at desc);

-- Rebalance runs (one row per save/execute action)
create table if not exists rebalance_runs (
  run_id text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  environment text not null default 'paper',
  mode text not null,
  status text not null,
  target_source text not null,
  strategy_ids jsonb not null default '[]'::jsonb,
  target_weights jsonb not null default '{}'::jsonb,
  target_cash_pct numeric,
  allow_new_positions boolean not null default false,
  orders_preview jsonb not null default '[]'::jsonb,
  submitted jsonb not null default '[]'::jsonb,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  finished_at timestamptz
);

create index if not exists idx_rebalance_runs_user_env_created
  on rebalance_runs(user_id, environment, created_at desc);

-- Bot runs
create table if not exists bot_runs (
  run_id text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  started_at timestamptz,
  ended_at timestamptz,
  result text,
  orders_created int not null default 0,
  orders_failed int not null default 0,
  detail jsonb
);

-- Backtest runs
create table if not exists backtest_runs (
  run_id text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  my_strategy_id text not null references user_strategies(strategy_id) on delete cascade,
  public_strategy_id text references public_strategies(public_strategy_id) on delete set null,
  entrypoint text,
  code_version text,
  public_version_snapshot text,
  params jsonb not null default '{}'::jsonb,
  start_date date not null,
  end_date date not null,
  benchmark_symbol text,
  initial_cash numeric not null,
  fee_bps numeric not null default 0,
  slippage_bps numeric not null default 0,
  status text not null default 'done',
  metrics jsonb not null default '{}'::jsonb,
  equity_curve jsonb not null default '[]'::jsonb,
  trade_stats jsonb not null default '{}'::jsonb,
  benchmark jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_backtest_runs_user_id on backtest_runs(user_id, created_at desc);
create index if not exists idx_backtest_runs_my_strategy_id on backtest_runs(my_strategy_id, created_at desc);

-- Market prices (Yahoo Finance ingestion)
create table if not exists market_prices (
  symbol text not null,
  price_date date not null,
  open numeric,
  high numeric,
  low numeric,
  close numeric,
  adj_close numeric,
  volume bigint,
  source text default 'yahoo',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (symbol, price_date)
);

create index if not exists idx_market_prices_symbol_date
  on market_prices(symbol, price_date desc);
