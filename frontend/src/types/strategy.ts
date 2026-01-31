export type RiskLevel = "low" | "mid" | "high";

export interface PublicStrategyAuthor {
  name: string;
  type: string;
}

export interface PublicStrategySampleMetrics {
  pnl_amount: number;
  pnl_pct: number;
  sharpe: number;
  max_drawdown_pct: number;
  win_rate_pct: number;
}

export interface PublicStrategySampleTradeStats {
  trades_count: number;
  avg_hold_hours: number;
}

export interface PublicStrategyPopularity {
  adds_count: number;
  likes_count: number;
  runs_count: number;
}

export interface PublicStrategyListItem {
  public_strategy_id: string;
  name: string;
  one_liner: string;
  category: string;
  tags: string[];
  risk_level: RiskLevel;
  version: string;
  author: PublicStrategyAuthor;
  sample_metrics: PublicStrategySampleMetrics;
  sample_trade_stats: PublicStrategySampleTradeStats;
  popularity: PublicStrategyPopularity;
  supported_assets: string[];
  supported_timeframes: string[];
  updated_at: string;
  created_at: string;
}

export interface PublicStrategyListResponse {
  items: PublicStrategyListItem[];
  next_cursor: string | null;
}

export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

export interface PublicStrategyRecommendedPreset {
  name: string;
  description?: string;
  params: Record<string, JsonValue>;
}

export interface PublicStrategyDetail extends PublicStrategyListItem {
  full_description: string;
  thesis?: string;
  rules?: string[] | string;
  param_schema: Record<string, unknown>;
  default_params: Record<string, JsonValue>;
  recommended_presets: PublicStrategyRecommendedPreset[];
}

export interface PublicStrategyValidationError {
  path: string;
  message: string;
  code?: string;
}

export interface PublicStrategyValidationResponse {
  valid: boolean;
  errors: PublicStrategyValidationError[];
}

export interface MyStrategy {
  my_strategy_id: string;
  name: string;
  source_public_strategy_id: string;
  public_version_snapshot: string;
  params: Record<string, JsonValue>;
  note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface MyStrategyListResponse {
  items: MyStrategy[];
  next_cursor?: string | null;
}
