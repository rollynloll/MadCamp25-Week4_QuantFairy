import type {
  ApiEquityPoint,
  ApiResultItem,
  ApiReturnPoint,
  BacktestMetric,
  BacktestResultsResponse,
  MonthlyReturn
} from "@/types/backtest";
import type {
  PortfolioChangePoint,
  PortfolioHoldingsSeries
} from "@/components/backtest/PortfolioChangeChart";
import { CASH_COLOR, HOLDINGS_COLORS } from "@/constants/backtestConstants";

export function formatNumber(value?: number, digits = 1) {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits
  }).format(value);
}

export function formatPct(value?: number, digits = 1) {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, digits)}%`;
}

export function getStrategyResults(payload?: BacktestResultsResponse | null): ApiResultItem[] {
  if (!payload) return [];
  if (payload.mode === "ensemble") {
    if (payload.components?.length) return payload.components;
    return payload.ensemble_result ? [payload.ensemble_result] : [];
  }
  return payload.results ?? [];
}

export type EquitySeries = {
  key: string;
  name: string;
  data?: ApiEquityPoint[];
  stroke: string;
  dashed?: boolean;
};

export type EquityCurvePoint = Record<string, number | string>;

export function buildEquityData(series: EquitySeries[]): EquityCurvePoint[] {
  const map = new Map<string, Record<string, number | string>>();
  for (const item of series) {
    if (!item.data) continue;
    for (const point of item.data) {
      const existing = map.get(point.date) ?? { date: point.date };
      existing[item.key] = point.equity;
      map.set(point.date, existing);
    }
  }
  return Array.from(map.values()).sort((a, b) =>
    String(a.date).localeCompare(String(b.date))
  );
}

export function toMonthlyReturns(series?: ApiReturnPoint[]): MonthlyReturn[] {
  if (!series || series.length === 0) return [];
  const bucket = new Map<string, number>();
  for (const p of series) {
    const key = p.date.slice(0, 7);
    const prev = bucket.get(key) ?? 1;
    bucket.set(key, prev * (1 + p.ret));
  }
  return Array.from(bucket.entries()).map(([month, compounded]) => ({
    month,
    return: +(100 * (compounded - 1)).toFixed(2),
  }));
}

type HoldingsSnapshot = { month: string; weights: Record<string, number> };

export function buildMonthlyHoldingsAll(
  holdings?: HoldingsSnapshot[]
): { data: PortfolioChangePoint[]; series: PortfolioHoldingsSeries[] } {
  if (!holdings || holdings.length === 0) return { data: [], series: [] };

  const totals = new Map<string, number>();
  for (const snapshot of holdings) {
    for (const [symbol, weight] of Object.entries(snapshot.weights || {})) {
      if (weight <= 0) continue;
      totals.set(symbol, (totals.get(symbol) ?? 0) + weight);
    }
  }

  const symbols = Array.from(totals.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([symbol]) => symbol);

  const colorForIndex = (index: number) =>
    HOLDINGS_COLORS[index % HOLDINGS_COLORS.length];

  const series: PortfolioHoldingsSeries[] = symbols.map((symbol, index) => ({
    key: symbol,
    name: symbol,
    color: colorForIndex(index)
  }));
  series.push({ key: "cash", name: "Cash", color: CASH_COLOR });

  const data = holdings.map((snapshot) => {
    const row: PortfolioChangePoint = { month: snapshot.month, cash: 0 };
    let totalLong = 0;
    let topSymbol = "CASH";
    let topWeight = -Infinity;
    for (const symbol of symbols) {
      const weight = Math.max(0, snapshot.weights?.[symbol] ?? 0);
      if (weight > topWeight) {
        topWeight = weight;
        topSymbol = symbol;
      }
      totalLong += weight;
      row[symbol] = +(weight * 100).toFixed(2);
    }
    const cash = Math.max(0, 1 - totalLong);
    row.cash = +(cash * 100).toFixed(2);
    row.top_symbol = topWeight > 0 ? topSymbol : "CASH";
    return row;
  });

  return { data, series };
}

export function buildMetricsFromResult(
  result?: ApiResultItem,
  tr?: (en: string, ko: string) => string
): BacktestMetric[] {
  const m = result?.metrics ?? {};
  const t = tr || ((en: string) => en);

  return [
    { label: t("Total Return", "총 수익률"), value: formatPct(m.total_return_pct), isPositive: (m.total_return_pct ?? 0) >= 0 },
    { label: t("CAGR", "연평균 수익률"), value: formatPct(m.cagr_pct), isPositive: (m.cagr_pct ?? 0) >= 0 },
    { label: t("Sharpe", "샤프 지수"), value: formatNumber(m.sharpe, 2), isPositive: (m.sharpe ?? 0) >= 0 },
    { label: t("Max Drawdown", "최대 낙폭"), value: formatPct(m.max_drawdown_pct), isPositive: (m.max_drawdown_pct ?? 0) >= 0 },
    { label: t("Volatility", "변동성"), value: formatPct(m.volatility_pct), isPositive: (m.volatility_pct ?? 0) >= 0 },
  ];
}
