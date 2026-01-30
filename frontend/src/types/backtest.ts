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