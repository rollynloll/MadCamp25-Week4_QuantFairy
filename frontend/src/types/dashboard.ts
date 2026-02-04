export type Range = "1D" | "1W" | "1M" | "3M" | "1Y" | "ALL";

export type ModeEnvironment = "paper" | "live";

export type BrokerState = "connected" | "degraded" | "down";
export type WorkerState = "running" | "stopped" | "error";
export type DataState = "ok" | "lagging" | "down";

export type BotState = "running" | "stopped" | "error" | "queued";
export type BotRunResult = "success" | "failed" | "partial";

export type StrategyState = "running" | "paused" | "idle" | "error";
export type AlertSeverity = "info" | "warning" | "critical";
export type TradeSide = "buy" | "sell";

export interface DashboardResponse {
  mode: {
    environment: ModeEnvironment;
    kill_switch: boolean;
  };
  status: {
    broker: { state: BrokerState; latency_ms: number };
    worker: { state: WorkerState; last_heartbeat_at: string };
    data: { state: DataState; lag_seconds: number };
  };
  account: {
    equity: number;
    cash: number;
    today_pnl: { value: number; pct: number };
    active_positions: { count: number; new_today: number };
  };
  kpi: {
    today_pnl: { value: number; pct: number };
    total_pnl: { value: number; pct: number };
    active_positions: { count: number; new_today: number };
    selected_metric: {
      name: string;
      value: number;
      unit: "pct" | "usd" | "count" | string;
      window: Range;
    };
  };
  performance: {
    range: Range;
    equity_curve: { t: string; equity: number }[];
    summary: { return_pct: number; max_drawdown_pct: number };
  };
  bot: {
    state: BotState;
    last_run: {
      run_id: string;
      started_at: string;
      ended_at: string;
      result: BotRunResult;
      orders_created: number;
      orders_failed: number;
    };
    next_run_at: string;
  };
  active_strategies: {
    strategy_id: string;
    name: string;
    state: StrategyState;
    positions_count: number;
    managed_value: number;
    pnl_today: { value: number; pct: number };
  }[];
  recent_trades: {
    fill_id: string;
    filled_at: string;
    symbol: string;
    side: TradeSide;
    qty: number;
    price: number;
    strategy_id: string;
    strategy_name: string;
  }[];
  alerts: {
    alert_id: string;
    severity: AlertSeverity;
    type: string;
    title: string;
    message: string;
    occurred_at: string;
    link?: { page: string; tab?: string };
  }[];
}
