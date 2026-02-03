import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import BacktestHeader from "@/components/backtest/BacktestHeader";
import BacktestConfigSection from "@/components/backtest/BacktestConfigSection";
import BacktestMetricsSection from "@/components/backtest/BacktestMetricsSection";
import BacktestCharts from "@/components/backtest/BacktestCharts";
import BacktestStatus from "@/components/backtest/BacktestStatus";
import {
  BENCHMARK_COLORS,
  BENCHMARK_OPTIONS,
  DEFAULT_BENCHMARK_CONFIG,
  DEFAULT_BENCHMARKS,
  DEFAULT_CONFIG,
  DEFAULT_PERIOD,
  DEFAULT_UNIVERSE,
  POLL_MS,
  STRATEGY_COLORS
} from "@/constants/backtestConstants";
import {
  buildEquityData,
  buildMetricsFromResult,
  buildMonthlyHoldingsAll,
  getStrategyResults,
  toMonthlyReturns
} from "@/utils/backtestUtils";
import type { BacktestJob, BacktestResultsResponse } from "@/types/backtest";
import { createBacktest, getBacktestJob, getBacktestResults, getBacktests } from "@/api/backtests";
import { useLanguage } from "@/contexts/LanguageContext";
import { useMyStrategies } from "@/hooks/useMyStrategies";

export default function Backtest() {
  const [searchParams] = useSearchParams();
  const backtestIdParam = searchParams.get("id");
  const [resolvedId, setResolvedId] = useState<string | null>(null);

  const { tr } = useLanguage();
  const { myStrategies } = useMyStrategies();

  const [job, setJob] = useState<BacktestJob | null>(null);
  const [results, setResults] = useState<BacktestResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEmpty, setIsEmpty] = useState(false);
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

  const strategyResults = getStrategyResults(results);
  const hasMultipleStrategies = strategyResults.length > 1 || selectedStrategyIds.length > 1;

  const metricsByStrategy = strategyResults.map((item) => ({
    label: item.label,
    metrics: buildMetricsFromResult(item, tr)
  }));

  const strategyOptions = myStrategies.map((strategy) => ({
    value: strategy.my_strategy_id,
    label: strategy.name
  }));

  const parseNumberInput = (value: string, fallback: number) => {
    const cleaned = value.replace(/[^0-9.-]/g, "");
    const parsed = Number(cleaned);
    return Number.isFinite(parsed) ? parsed : fallback;
  };

  const handleRunBacktest = async () => {
    const uniqueStrategyIds = Array.from(new Set(selectedStrategyIds.filter(Boolean)));
    if (uniqueStrategyIds.length === 0) {
      setError(tr("Please select a strategy.", "전략을 선택해주세요."));
      return;
    }
    if (periodStart && periodEnd && periodStart > periodEnd) {
      setError("기간을 확인해주세요.");
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
      setError(err instanceof Error ? err.message : "Failed to start backtest");
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
        rangeDisabled={isSubmitting || (job?.status === "queued" || job?.status === "running")}
        onRun={handleRunBacktest}
        runDisabled={isSubmitting || (job?.status === "queued" || job?.status === "running") || selectedStrategyIds.length === 0}
      />
      <BacktestStatus error={error} job={job} tr={tr} />
      <BacktestConfigSection
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
      <BacktestMetricsSection items={metricsByStrategy} />
      <BacktestCharts
        equityCurve={equityCurve}
        equitySeries={equitySeries}
        hasMultipleStrategies={hasMultipleStrategies}
        monthlyReturns={monthlyReturns}
        portfolioHoldings={portfolioHoldings}
        tr={tr}
      />
    </div>
  );
}