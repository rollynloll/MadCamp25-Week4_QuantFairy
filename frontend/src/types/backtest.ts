export interface EquityPoint {
  date: string;
  value: number;
  benchmark: number;
}

export interface MonthlyReturn {
  month: string;
  return: number;
}

export interface BacktestMetric {
  label: string;
  value: string;
  isPositive: boolean;
}

export interface BacktestConfigData {
  strategy: string;
  initialCapital: string;
  commission: string;
  slippage: string;
}

export interface BacktestCreateRequest {
  mode: "single" | "batch" | "ensemble";
  spec: BacktestSpec;
  strategies: StrategyRef[];
  benchmarks?: BenchmarkRef[];
  ensemble?: {
    mixing: "weighted_sum";
    weights: Record<string, number>;
    constraints?: {
      normalize_weights?: boolean;
      max_weight_per_symbol?: number | null;
      max_positions?: number | null;
      cash_buffer_pct?: number | null;
      min_trade_weight?: number | null;
    };
  };
}


export interface BacktestJob {
  backtest_id: string;
  mode: "single" | "batch" | "ensemble";
  status: "queued" | "running" | "done" | "failed" | "canceled";
  progress?: number;
  progress_stage?: string;
  progress_message?: string;
  progress_detail?: Record<string, unknown> | null;
  eta_seconds?: number;
  started_at?: string | null;
  progress_log?: {
    at: string;
    stage: string;
    message: string;
    progress?: number;
    eta_seconds?: number;
    detail?: Record<string, unknown> | null;
  }[];
  error?: {
    code: string;
    message: string;
    detail?: string;
    details?: { field: string; reason: string }[];
  };
  spec: BacktestSpec;
  strategies?: StrategyRef[];
  benchmarks?: BenchmarkRef[];
  created_at?: string;
  updated_at?: string;
}

export interface BacktestSpec {
  period_start: string;
  period_end: string;
  timeframe: string;
  initial_cash: number;
  fee_bps: number;
  slippage_bps: number;
  rebalance?: string;
  universe?: { type: "PRESET" | "CUSTOM"; preset_id?: string; tickers?: string[] };
  price_field?: "adj_close" | "close";
  currency?: string;
}

export interface StrategyRef {
  type: "public" | "my";
  id: string;
  params_override?: Record<string, unknown>;
  label?: string;
}

export interface BenchmarkRef {
  symbol: string;
  label?: string;
  initial_cash?: number;
  fee_bps?: number;
  slippage_bps?: number;
}

export interface ApiMetrics {
  total_return_pct?: number;
  cagr_pct?: number;
  volatility_pct?: number;
  sharpe?: number;
  sortino?: number;
  max_drawdown_pct?: number;
  calmar?: number;
  alpha_pct?: number;
  beta?: number;
  tracking_error_pct?: number;
  information_ratio?: number;
  turnover_pct?: number;
}

export interface ApiEquityPoint {
  date: string;
  equity: number;
}

export interface ApiReturnPoint {
  date: string;
  ret: number;
}

export interface ApiDrawdownPoint {
  date: string;
  dd_pct: number;
}

export interface ApiResultItem {
  label: string;
  strategy_ref?: StrategyRef;
  metrics: ApiMetrics;
  equity_curve?: ApiEquityPoint[];
  returns?: ApiReturnPoint[];
  drawdown?: ApiDrawdownPoint[];
  holdings_history?: { month: string; weights: Record<string, number> }[];
}

export interface BenchmarkItem {
  symbol: string;
  metrics?: ApiMetrics;
  equity_curve?: ApiEquityPoint[];
  returns?: ApiReturnPoint[];
  drawdown?: ApiDrawdownPoint[];
}

export interface BacktestResultsResponse {
  backtest_id: string;
  status: "queued" | "running" | "done" | "failed" | "canceled";
  mode: "single" | "batch" | "ensemble";
  spec: BacktestSpec;
  benchmarks?: BenchmarkItem[] | { items: BenchmarkItem[] };
  results?: ApiResultItem[];
  ensemble_result?: ApiResultItem;
  components?: ApiResultItem[];
  comparison_table?: Record<string, unknown>[];
}
