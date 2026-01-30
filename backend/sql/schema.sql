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

-- Public strategy catalog
create table if not exists strategy_templates (
  template_id text primary key,
  name text not null,
  description text,
  params_schema jsonb not null default '{}'::jsonb,
  risk_schema jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- User strategies (instances)
create table if not exists user_strategies (
  strategy_id text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  template_id text references strategy_templates(template_id),
  name text not null,
  state text not null,
  description text,
  params jsonb not null default '{}'::jsonb,
  risk_limits jsonb not null default '{}'::jsonb,
  positions_count int not null default 0,
  pnl_today_value numeric not null default 0,
  pnl_today_pct numeric not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_user_strategies_user_id on user_strategies(user_id);
create index if not exists idx_user_strategies_user_state on user_strategies(user_id, state);

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
