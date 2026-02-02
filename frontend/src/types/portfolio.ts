export interface Position {
  symbol: string;
  name: string;
  qty: number;
  side: "short" | "long";
  avgPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPct: number;
  strategy: string;
};

export type StrategyState = "running" | "paused" | "stopped";

export interface Strategy {
  id: string;
  name: string;
  state: StrategyState;
  currentWeight: number;
  targetWeight: number;
  positionsCount: number;
  lastRun: string;
};

export interface SectorAllocationItem {
  sector: string;
  percent: number;
  value: number;
};

export interface EquityPoint {
  date: string;
  value: number;
};

export interface DrawdownPoint {
  date: string;
  value: number;
};

export type OrderStatus = "filled" | "partial" | "cancelled" | "pending"; 
export interface Order {
  id: number;
  time: string;
  type: "BUY" | "SELL";
  symbol: string;
  qty: number;
  status: OrderStatus;
  strategy: string;
};

export type AlertLevel = "warning" | "error";

export interface AlertItem {
  id: number;
  time: string;
  level: AlertLevel;
  message: string;
  strategy: string;
};
export interface BotRun {
  id: number;
  time: string;
  status: "success" | "failed";
  duration: string;
  trades: number;
};

export type Env = "paper" | "live";
export type Range = "1W" | "1M" | "3M" | "1Y" | "ALL";

export type PortfolioSummaryResponse = {
  env: Env;
  as_of: string;
  mode: { environment: Env; kill_switch: boolean };
  status: {
    broker: { state: "up" | "down"; latency_ms?: number };
    worker: { state: "running" | "stopped" | "unknown"; last_heartbeat_at?: string };
    data: { state: "ok" | "lagging" | "down"; lag_seconds?: number };
  };
  account: {
    equity: number;
    cash: number;
    buying_power: number;
    today_pnl: { value: number; pct: number };
    open_positions: { count: number; long: number; short: number };
  };
  exposure: {
    net_pct: number;
    gross_pct: number;
    cash_pct: number;
    top5_concentration_pct: number;
  };
};

export type PortfolioPerformanceResponse = {
  env: Env;
  range: Range;
  benchmark?: string;
  as_of: string;
  equity_curve: { t: string; equity: number }[];
  benchmark_curve?: { t: string; price: number }[];
};

export type PortfolioDrawdownResponse = {
  env: Env;
  range: Range;
  as_of: string;
  drawdown_curve: { t: string; drawdown_pct: number }[];
  summary: { current_drawdown_pct: number; max_drawdown_pct: number };
};

export type PortfolioKpiResponse = {
  env: Env;
  range: Range;
  as_of: string;
  kpi: {
    period_return_pct: number;
    cagr_pct: number;
    volatility_pct: number;
    sharpe: number;
    max_drawdown_pct: number;
    win_rate_pct: number;
  };
  notes?: { risk_free_rate_pct?: number; method?: string };
};

export type PortfolioPositionsResponse = {
  env: Env;
  as_of: string;
  items: Array<{
    symbol: string;
    qty: number;
    side: "long" | "short";
    avg_entry_price: number;
    current_price: number;
    market_value: number;
    unrealized_pnl: { value: number; pct: number };
    strategy?: { user_strategy_id: string; name: string };
  }>;
};

export type PortfolioAllocationResponse = {
  env: Env;
  as_of: string;
  by_sector: Array<{ sector: string; value: number; pct: number; pnl_value?: number }>;
  by_strategy: Array<{ user_strategy_id: string; name: string; value: number; pct: number; pnl_value?: number }>;
  exposure: {
    net_pct: number;
    gross_pct: number;
    cash_pct: number;
    top5_concentration_pct: number;
  };
};

export type PortfolioActivityResponse = {
  env: Env;
  items: Array<{
    type: "order" | "trade" | "alert" | "bot_run";
    id: string;
    t: string;
    data: any;
  }>;
  next_cursor?: string;
};

export type PortfolioAttributionResponse = {
  env: Env;
  range?: Range;
  by: "strategy" | "sector";
  as_of: string;
  items: Array<{
    key: string;
    label: string;
    exposure_pct: number;
    unrealized_pnl_value: number;
    period_contribution_pct?: number;
  }>;
};

export type PortfolioRebalanceRequest = {
  mode: "dry_run" | "execute";
  target_source: "combined" | "strategy";
  strategy_ids?: string[];
  target_weights?: Record<string, number>;
  target_cash_pct?: number;
  overrides?: { cash_buffer?: number };
};

export type PortfolioRebalanceResponse = {
  env: Env;
  mode: "dry_run" | "execute";
  rebalance_id: string;
  status: "preview" | "submitted";
  orders: Array<{
    symbol: string;
    side: "buy" | "sell";
    qty: number;
    notional: number;
    estimated_price: number;
  }>;
};

export type UserStrategyListItem = {
  user_strategy_id: string;
  name: string;
  public_strategy_id?: string;
  state: "running" | "paused" | "stopped";
  positions_count: number;
  today_pnl?: { value: number; pct: number };
  last_run_at?: string;
  params?: Record<string, any>;
  risk_limits?: Record<string, any>;
};

export type UserStrategiesResponse = {
  env: Env;
  items: UserStrategyListItem[];
};

export type UserStrategyDetailResponse = {
  env: Env;
  user_strategy_id: string;
  name: string;
  state: "running" | "paused" | "stopped";
  public_strategy: {
    public_strategy_id: string;
    name: string;
    one_liner?: string;
    param_schema?: Record<
      string,
      { type: "int" | "float" | "string" | "bool"; default?: any; min?: number; max?: number }
    >;
  };
  params: Record<string, any>;
  risk_limits: Record<string, any>;
};
