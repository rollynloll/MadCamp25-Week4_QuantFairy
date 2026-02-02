import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import BacktestHeader from "@/components/backtest/BacktestHeader";
import BacktestConfig from "@/components/backtest/BacktestConfig";
import BacktestMetrics from "@/components/backtest/BacktestMetrics";
import EquityCurveChart from "@/components/backtest/EquityCurveChart";
import MonthlyReturnsChart from "@/components/backtest/MonthlyReturnsChart";
import type {
  ApiEquityPoint,
  ApiReturnPoint,
  BacktestJob,
  BacktestMetric,
  BacktestResultsResponse,
  EquityPoint,
  MonthlyReturn
} from "@/types/backtest";
import type { MyStrategy } from "@/types/strategy";
import { createBacktest, getBacktestJob, getBacktestResults, getBacktests } from "@/api/backtests";
import { getMyStrategies } from "@/api/strategies";
import { useLanguage } from "@/contexts/LanguageContext";

const POLL_MS = 2000;
const DEFAULT_CONFIG = {
  initial_capital: 100000,
  commission: 0.001,
  slippage: 0.0005
};
const DEFAULT_PERIOD = {
  start: "2024-01-01",
  end: "2024-12-31"
};
const DEFAULT_UNIVERSE = { type: "PRESET" as const, preset_id: "US_CORE_20" };
const DEFAULT_BENCHMARKS = [{ symbol: "CASH" }];

function formatPct(value?: number, digits = 1) {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
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

function buildMetrics(
  payload: BacktestResultsResponse,
  tr: (en: string, ko: string) => string
): BacktestMetric[] {
  const result = pickPrimaryResult(payload);
  const m = result?.metrics ?? {};
  return [
    { label: tr("Total Return", "총 수익률"), value: formatPct(m.total_return_pct), isPositive: (m.total_return_pct ?? 0) >= 0 },
    { label: "CAGR", value: formatPct(m.cagr_pct), isPositive: (m.cagr_pct ?? 0) >= 0 },
    { label: tr("Sharpe", "샤프"), value: m.sharpe?.toFixed(2) ?? "-", isPositive: (m.sharpe ?? 0) >= 0 },
    { label: tr("Max Drawdown", "최대 낙폭"), value: formatPct(m.max_drawdown_pct), isPositive: (m.max_drawdown_pct ?? 0) >= 0 },
    { label: tr("Volatility", "변동성"), value: formatPct(m.volatility_pct), isPositive: (m.volatility_pct ?? 0) >= 0 },
  ];
}

export default function Backtest() {
  const [searchParams] = useSearchParams();
  const backtestIdParam = searchParams.get("id");
  const [resolvedId, setResolvedId] = useState<string | null>(null);
  const { tr } = useLanguage();

  const [job, setJob] = useState<BacktestJob | null>(null);
  const [results, setResults] = useState<BacktestResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEmpty, setIsEmpty] = useState(false);
  const [myStrategies, setMyStrategies] = useState<MyStrategy[]>([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>("");
  const [initialCapitalInput, setInitialCapitalInput] = useState(
    String(DEFAULT_CONFIG.initial_capital)
  );
  const [commissionInput, setCommissionInput] = useState(
    String(DEFAULT_CONFIG.commission)
  );
  const [slippageInput, setSlippageInput] = useState(String(DEFAULT_CONFIG.slippage));
  const [hasEditedConfig, setHasEditedConfig] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [periodStart, setPeriodStart] = useState(DEFAULT_PERIOD.start);
  const [periodEnd, setPeriodEnd] = useState(DEFAULT_PERIOD.end);

  useEffect(() => {
    let cancelled = false;

    const loadMyStrategies = async () => {
      try {
        const res = await getMyStrategies();
        if (!cancelled) {
          setMyStrategies(res.items ?? []);
        }
      } catch {
        if (!cancelled) {
          setMyStrategies([]);
        }
      }
    };

    loadMyStrategies();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (selectedStrategyId || myStrategies.length === 0) return;
    setSelectedStrategyId(myStrategies[0].my_strategy_id);
  }, [myStrategies, selectedStrategyId]);

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
          setError(err instanceof Error ? err.message : tr("Failed to load backtests", "백테스트 목록을 불러오지 못했습니다"));
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
          setError(err instanceof Error ? err.message : tr("Failed to load backtest", "백테스트를 불러오지 못했습니다"));
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

  useEffect(() => {
    if (!job || hasEditedConfig) return;
    setInitialCapitalInput(String(job.spec?.initial_cash ?? DEFAULT_CONFIG.initial_capital));
    setCommissionInput(String(job.spec?.fee_bps ?? DEFAULT_CONFIG.commission));
    setSlippageInput(String(job.spec?.slippage_bps ?? DEFAULT_CONFIG.slippage));
    if (job.spec?.period_start) {
      setPeriodStart(job.spec.period_start);
    }
    if (job.spec?.period_end) {
      setPeriodEnd(job.spec.period_end);
    }
    const jobStrategyId = job.strategies?.find((s) => s.type === "my")?.id;
    if (jobStrategyId) {
      setSelectedStrategyId(jobStrategyId);
    }
  }, [job, hasEditedConfig]);

  if (loading && !results && !isEmpty && !job) {
    return (
      <div className="space-y-6">
        <BacktestHeader
          rangeLabel={`${DEFAULT_PERIOD.start} to ${DEFAULT_PERIOD.end}`}
          startDate={periodStart}
          endDate={periodEnd}
          onStartDateChange={(value) => setPeriodStart(value)}
          onEndDateChange={(value) => setPeriodEnd(value)}
          rangeDisabled
        />
        <div className="text-sm text-gray-400">{tr("Loading backtest...", "백테스트 불러오는 중...")}</div>
      </div>
    );
  }

  if (error && !job && !results) {
    return (
      <div className="space-y-6">
        <BacktestHeader
          rangeLabel={`${DEFAULT_PERIOD.start} to ${DEFAULT_PERIOD.end}`}
          startDate={periodStart}
          endDate={periodEnd}
          onStartDateChange={(value) => setPeriodStart(value)}
          onEndDateChange={(value) => setPeriodEnd(value)}
          rangeDisabled
        />
        <div className="text-sm text-red-400">{error}</div>
      </div>
    );
  }

  const metrics = results ? buildMetrics(results, tr) : [];
  const strategyOptions = myStrategies.map((strategy) => ({
    value: strategy.my_strategy_id,
    label: strategy.name
  }));
  const isRunning = job?.status === "queued" || job?.status === "running";
  const progressLabel =
    job?.progress !== undefined && job?.progress !== null
      ? `${job.progress}%`
      : "";
  const jobError = job?.error;

  const parseNumberInput = (value: string, fallback: number) => {
    const cleaned = value.replace(/[^0-9.-]/g, "");
    const parsed = Number(cleaned);
    return Number.isFinite(parsed) ? parsed : fallback;
  };

  const handleRunBacktest = async () => {
    if (!selectedStrategyId) {
      setError(tr("Please select a strategy.", "전략을 선택해주세요."));
      return;
    }
    if (periodStart && periodEnd && periodStart > periodEnd) {
      setError(tr("Please check the period.", "기간을 확인해주세요."));
      return;
    }

    setError(null);
    setIsEmpty(false);
    setResults(null);
    setJob(null);
    setLoading(true);
    setIsSubmitting(true);

    try {
      const payload = {
        mode: "single" as const,
        spec: {
          period_start: periodStart,
          period_end: periodEnd,
          timeframe: "1D" as const,
          initial_cash: parseNumberInput(initialCapitalInput, DEFAULT_CONFIG.initial_capital),
          fee_bps: parseNumberInput(commissionInput, DEFAULT_CONFIG.commission),
          slippage_bps: parseNumberInput(slippageInput, DEFAULT_CONFIG.slippage),
          rebalance: "monthly" as const,
          universe: DEFAULT_UNIVERSE,
          price_field: "adj_close" as const,
          currency: "USD" as const
        },
        strategies: [{ type: "my" as const, id: selectedStrategyId }],
        benchmarks: DEFAULT_BENCHMARKS
      };

      const created = await createBacktest(payload);
      setResolvedId(created.backtest_id);
      setJob(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : tr("Failed to start backtest", "백테스트 시작에 실패했습니다"));
    } finally {
      setIsSubmitting(false);
      setLoading(false);
    }
  };

  const primaryResult = results ? pickPrimaryResult(results) : undefined;
  const benchmark = results?.benchmarks?.[0];

  const equityCurve = mergeEquityCurve(
    primaryResult?.equity_curve,
    benchmark?.equity_curve
  );

  const monthlyReturns = toMonthlyReturns(primaryResult?.returns);

  return (
    <div className="space-y-6">
      <BacktestHeader
        rangeLabel={`${DEFAULT_PERIOD.start} to ${DEFAULT_PERIOD.end}`}
        startDate={periodStart}
        endDate={periodEnd}
        onStartDateChange={(value) => {
          setHasEditedConfig(true);
          setPeriodStart(value);
        }}
        onEndDateChange={(value) => {
          setHasEditedConfig(true);
          setPeriodEnd(value);
        }}
        rangeDisabled={isSubmitting || isRunning}
        onRun={handleRunBacktest}
        runDisabled={isSubmitting || isRunning || !selectedStrategyId}
      />
      {error && (
        <div className="text-sm text-red-400">{error}</div>
      )}
      {isRunning && (
        <div className="text-sm text-gray-400">
          {tr("Backtest", "백테스트")} {job?.status} {progressLabel && `· ${progressLabel}`}
        </div>
      )}
      {job?.status === "failed" && (
        <div className="text-sm text-red-400 space-y-1">
          <div>
            {tr("Backtest failed", "백테스트 실패")}{jobError?.message ? `: ${jobError.message}` : "."}
          </div>
          {jobError?.detail && (
            <div className="text-xs text-red-300">{jobError.detail}</div>
          )}
          {jobError?.details?.length ? (
            <div className="text-xs text-red-300">
              {jobError.details.map((d) => `${d.field}: ${d.reason}`).join(" · ")}
            </div>
          ) : null}
        </div>
      )}
      {job?.status === "canceled" && (
        <div className="text-sm text-gray-400">{tr("Backtest canceled.", "백테스트가 취소되었습니다.")}</div>
      )}
      <BacktestConfig
        strategies={strategyOptions}
        selectedStrategyId={selectedStrategyId}
        onStrategyChange={(value) => {
          setHasEditedConfig(true);
          setSelectedStrategyId(value);
        }}
        initialCapital={initialCapitalInput}
        onInitialCapitalChange={(value) => {
          setHasEditedConfig(true);
          setInitialCapitalInput(value);
        }}
        commission={commissionInput}
        onCommissionChange={(value) => {
          setHasEditedConfig(true);
          setCommissionInput(value);
        }}
        slippage={slippageInput}
        onSlippageChange={(value) => {
          setHasEditedConfig(true);
          setSlippageInput(value);
        }}
      />
      <BacktestMetrics metrics={metrics} />
      <EquityCurveChart data={equityCurve} />
      <MonthlyReturnsChart data={monthlyReturns} />
    </div>
  );
}
