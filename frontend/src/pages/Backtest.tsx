import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import BacktestHeader from "@/components/backtest/BacktestHeader";
import BacktestConfig from "@/components/backtest/BacktestConfig";
import BenchmarkConfig from "@/components/backtest/BenchmarkConfig";
import BacktestMetrics from "@/components/backtest/BacktestMetrics";
import EquityCurveChart from "@/components/backtest/EquityCurveChart";
import MonthlyReturnsChart from "@/components/backtest/MonthlyReturnsChart";
import PortfolioChangeChart, {
  type PortfolioChangePoint,
  type PortfolioHoldingsSeries
} from "@/components/backtest/PortfolioChangeChart";
import type {
  ApiEquityPoint,
  ApiResultItem,
  ApiReturnPoint,
  BacktestJob,
  BacktestMetric,
  BacktestResultsResponse,
  MonthlyReturn
} from "@/types/backtest";
import type { MyStrategy } from "@/types/strategy";
import { createBacktest, getBacktestJob, getBacktestResults, getBacktests } from "@/api/backtests";
import { getMyStrategies } from "@/api/strategies";
import { useLanguage } from "@/contexts/LanguageContext";

const POLL_MS = 500;
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
const BENCHMARK_OPTIONS = [
  { value: "CASH", label: "CASH" },
  { value: "SPY", label: "SPY · S&P 500 ETF" },
  { value: "QQQ", label: "QQQ · Nasdaq 100 ETF" },
  { value: "IWM", label: "IWM · Russell 2000 ETF" }
];
const DEFAULT_BENCHMARK_CONFIG = {
  initial_capital: 100000,
  commission: 0,
  slippage: 0
};
const STRATEGY_COLORS = ["#3b82f6", "#22c55e", "#f97316", "#ec4899", "#8b5cf6", "#14b8a6"];
const BENCHMARK_COLORS = ["#6b7280", "#9ca3af", "#94a3b8", "#64748b"];
const HOLDINGS_COLORS = [
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
const CASH_COLOR = "#5a6675";

function formatPct(value?: number, digits = 1) {
  if (value === undefined || value === null || Number.isNaN(value)) return "-";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}%`;
}

function getStrategyResults(payload?: BacktestResultsResponse | null): ApiResultItem[] {
  if (!payload) return [];
  if (payload.mode === "ensemble") {
    if (payload.components?.length) return payload.components;
    return payload.ensemble_result ? [payload.ensemble_result] : [];
  }
  return payload.results ?? [];
}

type EquitySeries = {
  key: string;
  name: string;
  data?: ApiEquityPoint[];
  stroke: string;
  dashed?: boolean;
};

function buildEquityData(series: EquitySeries[]) {
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

type HoldingsSnapshot = { month: string; weights: Record<string, number> };

function buildMonthlyHoldingsAll(
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
  const [selectedStrategyIds, setSelectedStrategyIds] = useState<string[]>([]);
  const [initialCapitalInput, setInitialCapitalInput] = useState(
    String(DEFAULT_CONFIG.initial_capital)
  );
  const [commissionInput, setCommissionInput] = useState(
    String(DEFAULT_CONFIG.commission)
  );
  const [slippageInput, setSlippageInput] = useState(String(DEFAULT_CONFIG.slippage));
  const [benchmarkConfigs, setBenchmarkConfigs] = useState<
    { symbol: string; initialCapital: string; commission: string; slippage: string }[]
  >([
    {
      symbol: DEFAULT_BENCHMARKS[0]?.symbol ?? "CASH",
      initialCapital: String(DEFAULT_BENCHMARK_CONFIG.initial_capital),
      commission: String(DEFAULT_BENCHMARK_CONFIG.commission),
      slippage: String(DEFAULT_BENCHMARK_CONFIG.slippage)
    }
  ]);
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
    if (selectedStrategyIds.length > 0 || myStrategies.length === 0) return;
    setSelectedStrategyIds([myStrategies[0].my_strategy_id]);
  }, [myStrategies, selectedStrategyIds.length]);

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
    const jobStrategyIds = job.strategies?.filter((s) => s.type === "my").map((s) => s.id) ?? [];
    if (jobStrategyIds.length) {
      setSelectedStrategyIds(jobStrategyIds);
    }
    const jobBenchmarks = job.benchmarks ?? [];
    if (jobBenchmarks.length) {
      setBenchmarkConfigs(
        jobBenchmarks.map((benchmark) => ({
          symbol: benchmark.symbol,
          initialCapital:
            benchmark.initial_cash !== undefined && benchmark.initial_cash !== null
              ? String(benchmark.initial_cash)
              : String(DEFAULT_BENCHMARK_CONFIG.initial_capital),
          commission:
            benchmark.fee_bps !== undefined && benchmark.fee_bps !== null
              ? String(benchmark.fee_bps)
              : String(DEFAULT_BENCHMARK_CONFIG.commission),
          slippage:
            benchmark.slippage_bps !== undefined && benchmark.slippage_bps !== null
              ? String(benchmark.slippage_bps)
              : String(DEFAULT_BENCHMARK_CONFIG.slippage)
        }))
      );
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
  const strategyResults = getStrategyResults(results);
  const hasMultipleStrategies = strategyResults.length > 1 || selectedStrategyIds.length > 1;
  const metricsByStrategy = strategyResults.map((item) => ({
    label: item.label,
    metrics: buildMetricsFromResult(item)
  }));
  const strategyOptions = myStrategies.map((strategy) => ({
    value: strategy.my_strategy_id,
    label: strategy.name
  }));
  const isRunning = job?.status === "queued" || job?.status === "running";
  const progressLabel =
    job?.progress !== undefined && job?.progress !== null
      ? `${job.progress}%`
      : "";
  const remainingLabel =
    job?.progress !== undefined && job?.progress !== null
      ? `${Math.max(0, 100 - job.progress)}% left`
      : "";
  const etaMinutes =
    job?.eta_seconds && job.eta_seconds > 0
      ? Math.max(1, Math.ceil(job.eta_seconds / 60))
      : null;
  const etaLabel = etaMinutes ? `ETA ${etaMinutes}m` : "";
  const progressMessage = job?.progress_message || job?.progress_stage || "";
  const recentLogs = job?.progress_log?.slice(-4) ?? [];
  const jobError = job?.error;

  const parseNumberInput = (value: string, fallback: number) => {
    const cleaned = value.replace(/[^0-9.-]/g, "");
    const parsed = Number(cleaned);
    return Number.isFinite(parsed) ? parsed : fallback;
  };

  const handleRunBacktest = async () => {
    if (!selectedStrategyId) {
      setError(tr("Please select a strategy.", "전략을 선택해주세요."));
    const uniqueStrategyIds = Array.from(new Set(selectedStrategyIds.filter(Boolean)));
    if (uniqueStrategyIds.length === 0) {
      setError("전략을 선택해주세요.");
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
      const mode = (uniqueStrategyIds.length > 1 ? "batch" : "single") as
        | "batch"
        | "single";
      const payload = {
        mode,
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
        strategies: uniqueStrategyIds.map((id) => ({ type: "my" as const, id })),
        benchmarks: benchmarkConfigs
          .filter((config) => config.symbol)
          .map((config) => ({
            symbol: config.symbol,
            initial_cash: parseNumberInput(
              config.initialCapital,
              DEFAULT_BENCHMARK_CONFIG.initial_capital
            ),
            fee_bps: parseNumberInput(
              config.commission,
              DEFAULT_BENCHMARK_CONFIG.commission
            ),
            slippage_bps: parseNumberInput(
              config.slippage,
              DEFAULT_BENCHMARK_CONFIG.slippage
            )
          }))
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

  const primaryResult = strategyResults[0];
  const benchmarkItems = Array.isArray(results?.benchmarks)
    ? results?.benchmarks
    : results?.benchmarks?.items;

  const strategySeries = strategyResults.map((item, index) => ({
    key: `strategy_${index}`,
    name: item.label || `Strategy ${index + 1}`,
    data: item.equity_curve,
    stroke: STRATEGY_COLORS[index % STRATEGY_COLORS.length]
  }));
  const benchmarkSeries =
    benchmarkItems?.map((item, index) => ({
      key: `benchmark_${index}`,
      name: item.label || item.symbol,
      data: item.equity_curve,
      stroke: BENCHMARK_COLORS[index % BENCHMARK_COLORS.length],
      dashed: true
    })) ?? [];
  const equitySeries = [...strategySeries, ...benchmarkSeries];
  const equityCurve = buildEquityData(equitySeries);

  const monthlyReturns = hasMultipleStrategies ? [] : toMonthlyReturns(primaryResult?.returns);
  const portfolioHoldings = hasMultipleStrategies
    ? { data: [], series: [] }
    : buildMonthlyHoldingsAll(primaryResult?.holdings_history);

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
        runDisabled={isSubmitting || isRunning || selectedStrategyIds.length === 0}
      />
      {error && (
        <div className="text-sm text-red-400">{error}</div>
      )}
      {isRunning && (
        <div className="text-sm text-gray-400 space-y-1">
          {tr("Backtest", "백테스트")} {job?.status} {progressLabel && `· ${progressLabel}`}
          <div>
            Backtest {job?.status}
            {progressLabel && ` · ${progressLabel}`}
            {remainingLabel && ` · ${remainingLabel}`}
            {etaLabel && ` · ${etaLabel}`}
          </div>
          {progressMessage && (
            <div className="text-xs text-gray-500">{progressMessage}</div>
          )}
          {recentLogs.length ? (
            <div className="text-xs text-gray-500 space-y-0.5">
              {recentLogs.map((entry) => {
                const timeLabel = new Date(entry.at).toLocaleTimeString("ko-KR", {
                  hour: "2-digit",
                  minute: "2-digit"
                });
                return (
                  <div key={`${entry.at}-${entry.stage}-${entry.message}`}>
                    {timeLabel} · {entry.message}
                    {entry.progress !== undefined ? ` (${entry.progress}%)` : ""}
                  </div>
                );
              })}
            </div>
          ) : null}
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
        selectedStrategyIds={selectedStrategyIds}
        onStrategyChange={(index, value) => {
          setHasEditedConfig(true);
          setSelectedStrategyIds((prev) => {
            const next = [...prev];
            next[index] = value;
            return next;
          });
        }}
        onAddStrategy={() => {
          if (strategyOptions.length === 0) return;
          setHasEditedConfig(true);
          setSelectedStrategyIds((prev) => {
            const existing = new Set(prev);
            const nextValue =
              strategyOptions.find((option) => !existing.has(option.value))?.value ??
              strategyOptions[0].value;
            return [...prev, nextValue];
          });
        }}
        onRemoveStrategy={(index) => {
          setHasEditedConfig(true);
          setSelectedStrategyIds((prev) => prev.filter((_, idx) => idx !== index));
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
      <BenchmarkConfig
        benchmarks={BENCHMARK_OPTIONS}
        benchmarkConfigs={benchmarkConfigs}
        onBenchmarkChange={(index, value) => {
          setHasEditedConfig(true);
          setBenchmarkConfigs((prev) =>
            prev.map((config, idx) => (idx === index ? { ...config, symbol: value } : config))
          );
        }}
        onBenchmarkInitialCapitalChange={(index, value) => {
          setHasEditedConfig(true);
          setBenchmarkConfigs((prev) =>
            prev.map((config, idx) =>
              idx === index ? { ...config, initialCapital: value } : config
            )
          );
        }}
        onBenchmarkCommissionChange={(index, value) => {
          setHasEditedConfig(true);
          setBenchmarkConfigs((prev) =>
            prev.map((config, idx) =>
              idx === index ? { ...config, commission: value } : config
            )
          );
        }}
        onBenchmarkSlippageChange={(index, value) => {
          setHasEditedConfig(true);
          setBenchmarkConfigs((prev) =>
            prev.map((config, idx) =>
              idx === index ? { ...config, slippage: value } : config
            )
          );
        }}
        onAddBenchmark={() => {
          if (BENCHMARK_OPTIONS.length === 0) return;
          setHasEditedConfig(true);
          setBenchmarkConfigs((prev) => {
            const existing = new Set(prev.map((config) => config.symbol));
            const nextSymbol =
              BENCHMARK_OPTIONS.find((option) => !existing.has(option.value))?.value ??
              BENCHMARK_OPTIONS[0].value;
            return [
              ...prev,
              {
                symbol: nextSymbol,
                initialCapital: String(DEFAULT_BENCHMARK_CONFIG.initial_capital),
                commission: String(DEFAULT_BENCHMARK_CONFIG.commission),
                slippage: String(DEFAULT_BENCHMARK_CONFIG.slippage)
              }
            ];
          });
        }}
        onRemoveBenchmark={(index) => {
          setHasEditedConfig(true);
          setBenchmarkConfigs((prev) => prev.filter((_, idx) => idx !== index));
        }}
      />
      {metricsByStrategy.length > 1 ? (
        <div className="space-y-4">
          {metricsByStrategy.map((item, index) => (
            <div key={`${item.label}-${index}`} className="space-y-2">
              <div className="text-sm text-gray-400">{item.label}</div>
              <BacktestMetrics metrics={item.metrics} />
            </div>
          ))}
        </div>
      ) : (
        <BacktestMetrics metrics={metricsByStrategy[0]?.metrics ?? []} />
      )}
      <EquityCurveChart data={equityCurve} series={equitySeries} height={hasMultipleStrategies ? 420 : 300} />
      {hasMultipleStrategies ? (
        <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6 text-sm text-gray-400">
          Monthly Returns는 여러 전략 비교 시 비활성화됩니다. 전략이 하나일 때만 표시됩니다.
        </div>
      ) : (
        <>
          <MonthlyReturnsChart data={monthlyReturns} />
          <PortfolioChangeChart
            data={portfolioHoldings.data}
            series={portfolioHoldings.series}
          />
        </>
      )}
    </div>
  );
}
