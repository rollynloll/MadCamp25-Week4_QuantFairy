export type RuleParamType = "number" | "select" | "slider" | "checkbox";

export interface RuleParam {
  id: string;
  label: string;
  type: RuleParamType;
  value: number | string | boolean;
  min?: number;
  max?: number;
  step?: number;
  options?: string[];
}

export interface Rule {
  id: string;
  name: string;
  conditions: string[];
  action: string;
  params: RuleParam[];
}

export interface BuilderBlock {
  id: string;
  title: string;
  description: string;
  rules: Rule[];
}

export interface StrategyKpi {
  label: string;
  value: string;
}

export interface BacktestMetric {
  label: string;
  value: string;
}

export interface TradeLogRow {
  id: string;
  time: string;
  symbol: string;
  side: "BUY" | "SELL";
  qty: number;
  price: number;
  pnl: number;
}
