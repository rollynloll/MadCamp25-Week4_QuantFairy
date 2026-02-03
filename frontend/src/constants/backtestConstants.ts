export const POLL_MS = 500;
export const DEFAULT_CONFIG = {
  initial_capital: 100000,
  commission: 0.001,
  slippage: 0.0005
};
export const DEFAULT_PERIOD = {
  start: "2024-01-01",
  end: "2024-12-31"
};
export const DEFAULT_UNIVERSE = { type: "PRESET" as const, preset_id: "US_CORE_20" };
export const DEFAULT_BENCHMARKS = [{ symbol: "CASH" }];
export const BENCHMARK_OPTIONS = [
  { value: "CASH", label: "CASH" },
  { value: "SPY", label: "SPY · S&P 500 ETF" },
  { value: "QQQ", label: "QQQ · Nasdaq 100 ETF" },
  { value: "IWM", label: "IWM · Russell 2000 ETF" }
];
export const DEFAULT_BENCHMARK_CONFIG = {
  initial_capital: 100000,
  commission: 0,
  slippage: 0
};
export const STRATEGY_COLORS = ["#3b82f6", "#22c55e", "#f97316", "#ec4899", "#8b5cf6", "#14b8a6"];
export const BENCHMARK_COLORS = ["#6b7280", "#9ca3af", "#94a3b8", "#64748b"];
export const HOLDINGS_COLORS = [
  "#5a82a8",
  "#4e968f",
  "#9b7a55",
  "#a66d74",
  "#6b80ab",
  "#5b966f",
  "#9b70ad",
  "#7b965b",
  "#a6965b",
  "#668ea8"
];
export const CASH_COLOR = "#5a6675";
