import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import BacktestHeader from "@/components/backtest/BacktestHeader";
import BacktestConfig from "@/components/backtest/BacktestConfig";
import BacktestMetrics from "@/components/backtest/BacktestMetrics";
import EquityCurveChart from "@/components/backtest/EquityCurveChart";
import MonthlyReturnsChart from "@/components/backtest/MonthlyReturnsChart";
import type { ApiEquityPoint, ApiReturnPoint, BacktestConfigData, BacktestJob, BacktestMetric, BacktestResultsResponse, EquityPoint, MonthlyReturn } from "@/types/backtest";
import { getBacktestJob, getBacktestResults, getBacktests } from "@/api/backtests";


const POLL_MS = 2000;

function formatPct(value?: number, digits = 1) {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

function formatNumber(value?: number) {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  return value.toLocaleString();
}

function pickPrimaryResult(payload: BacktestResultsResponse) {
  if (payload.mode === "ensemble") return payload.ensemble_result;
  return payload.results?.[0];
}

function mergeEquityCurve(strategy?: ApiEquityPoint[], benchmark?: ApiEquityPoint[]): EquityPoint[] {
  if (!strategy) return [];
  const benchMap = new Map<string, number>();
  benchmark?.forEach((p) => benchMap.set(p.date, p.equity));
  return strategy.map((p) => ({
    date: p.date,
    value: p.equity,
    benchmark: benchMap.get(p.date) ?? p.equity,
  }));
}

function toMonthlyReturns(series?: ApiReturnPoint[]): MonthlyReturn[] {
  if (!series || series.length === 0) return [];
  const bucket = new Map<string, number>();
  for (const p of series) {
    const key = p.date.slice(0, 7); // "YYYY-MM"
    const prev = bucket.get(key) ?? 1;
    bucket.set(key, prev * (1 + p.ret));
  }
  return Array.from(bucket.entries()).map(([month, compounded]) => ({
    month,
    return: +(100 * (compounded - 1)).toFixed(2),
  }));
}

function buildMetrics(payload: BacktestResultsResponse): BacktestMetric[] {
  const result = pickPrimaryResult(payload);
  const m = result?.metrics ?? {};
  return [
    { label: "Total Return", value: formatPct(m.total_return_pct), isPositive: (m.total_return_pct ?? 0) >= 0 },
    { label: "CAGR", value: formatPct(m.cagr_pct), isPositive: (m.cagr_pct ?? 0) >= 0 },
    { label: "Sharpe", value: m.sharpe?.toFixed(2) ?? "-", isPositive: (m.sharpe ?? 0) >= 0 },
    { label: "Max Drawdown", value: formatPct(m.max_drawdown_pct), isPositive: (m.max_drawdown_pct ?? 0) >= 0 },
    { label: "Volatility", value: formatPct(m.volatility_pct), isPositive: (m.volatility_pct ?? 0) >= 0 },
  ];
}

function buildConfig(job?: BacktestJob): BacktestConfigData {
  const spec = job?.spec;
  const strategy = job?.strategies?.[0]?.id ?? job?.strategies?.[0]?.label ?? "-";
  const initialCapital = spec?.initial_cash ? `$${formatNumber(spec.initial_cash)}` : "-";
  const commission = spec?.fee_bps !== undefined ? `${spec.fee_bps} bps` : "-";
  const slippage = spec?.slippage_bps !== undefined ? `${spec.slippage_bps} bps` : "-";
  return { strategy, initialCapital, commission, slippage };
}

export default function Backtest() {
  const [searchParams] = useSearchParams();
  const backtestIdParam = searchParams.get("id");
  const [resolvedId, setResolvedId] = useState<string | null>(null);

  const [job, setJob] = useState<BacktestJob | null>(null);
  const [results, setResults] = useState<BacktestResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEmpty, setIsEmpty] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setIsEmpty(false);
    setResolvedId(null);
    setJob(null);
    setResults(null);

    if (backtestIdParam) {
      setResolvedId(backtestIdParam);
      return;
    }

    const resolveLatest = async () => {
      try {
        setLoading(true);
        const list = await getBacktests({ limit: 1, sort: "created_at", order: "desc" });
        if (cancelled) return;
        const latestId = list.items[0]?.backtest_id ?? null;
        if (!latestId) {
          setIsEmpty(true);
          setLoading(false);
          return;
        }
        setResolvedId(latestId);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load backtests");
          setLoading(false);
        }
      }
    };

    resolveLatest();

    return () => {
      cancelled = true;
    };
  }, [backtestIdParam]);

  useEffect(() => {
    if (!resolvedId) return;

    let cancelled = false;
    let timer: number | undefined;

    const poll = async () => {
      try {
        setLoading(true);
        const jobRes = await getBacktestJob(resolvedId);
        if (cancelled) return;
        setJob(jobRes);

        if (jobRes.status === "done") {
          const resultsRes = await getBacktestResults(resolvedId);
          if (cancelled) return;
          setResults(resultsRes);
          setLoading(false);
          return;
        }

        setLoading(false);
        timer = window.setTimeout(poll, POLL_MS);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load backtest");
          setLoading(false);
        }
      }
    };

    poll();

    return () => {
      cancelled = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [resolvedId]);

  if (loading && !results && !isEmpty) {
    return (
      <div className="space-y-6">
        <BacktestHeader />
        <div className="text-sm text-gray-400">Loading backtest...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <BacktestHeader />
        <div className="text-sm text-red-400">{error}</div>
      </div>
    );
  }

  const metrics = results ? buildMetrics(results) : [];
  const config = buildConfig(job ?? undefined);

  const primaryResult = results ? pickPrimaryResult(results) : undefined;
  const benchmark = results?.benchmarks?.[0];

  const equityCurve = mergeEquityCurve(
    primaryResult?.equity_curve,
    benchmark?.equity_curve
  );

  const monthlyReturns = toMonthlyReturns(primaryResult?.returns);

  return (
    <div className="space-y-6">
      <BacktestHeader />
      {isEmpty && (
        <div className="text-sm text-gray-400">
          No backtests yet. Run one to see results.
        </div>
      )}
      <BacktestConfig config={config} />
      <BacktestMetrics metrics={metrics} />
      <EquityCurveChart data={equityCurve} />
      <MonthlyReturnsChart data={monthlyReturns} />
    </div>
  );
}
