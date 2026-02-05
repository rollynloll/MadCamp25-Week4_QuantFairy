import { useEffect, useMemo, useState } from "react";
import type {
  Env,
  Range,
  PortfolioSummaryResponse,
  PortfolioPositionsResponse,
  PortfolioAllocationResponse,
  PortfolioPerformanceResponse,
  PortfolioDrawdownResponse,
  PortfolioKpiResponse,
  PortfolioActivityResponse,
  PortfolioAttributionResponse,
  UserStrategiesResponse,
  PortfolioRebalanceTargetsResponse,
} from "@/types/portfolio";

import {
  getPortfolioOverview,
  getPortfolioPositions,
  getPortfolioPerformance,
  getPortfolioDrawdown,
  getPortfolioKpi,
  getPortfolioActivity,
  getPortfolioAttribution,
  getPortfolioRebalanceTargets,
} from "@/api/portfolio";
import { getUserStrategies } from "@/api/userStrategies";

type PortfolioPageData = {
  summary: PortfolioSummaryResponse;
  positions: PortfolioPositionsResponse;
  allocation: PortfolioAllocationResponse;
  userStrategies: UserStrategiesResponse;
  rebalanceTargets: PortfolioRebalanceTargetsResponse;
  performance?: PortfolioPerformanceResponse;
  drawdown?: PortfolioDrawdownResponse;
  kpi?: PortfolioKpiResponse;
  activity?: PortfolioActivityResponse;
  attribution?: PortfolioAttributionResponse;
};

type PortfolioViewData = {
  positions: Array<{
    symbol: string;
    name: string;
    qty: number;
    side: "short" | "long";
    avgPrice: number;
    currentPrice: number;
    pnl: number;
    pnlPct: number;
    strategy: string;
  }>;
  sectorAllocation: Array<{
    sector: string;
    percent: number;
    value: number;
  }>;
  equityCurve: Array<{ date: string; value: number }>;
  drawdownData: Array<{ date: string; value: number }>;
};

export function usePortfolioPageData(env: Env, range: Range, showBenchmark: boolean) {
  const [data, setData] = useState<PortfolioPageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [extrasLoading, setExtrasLoading] = useState({
    analytics: false,
    activity: false,
  });
  const [extrasError, setExtrasError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      setLoading(true);
      setError(null);

      try {
        // 병렬 로딩 (overview + positions + strategies)
        const [overview, positions, userStrategies, rebalanceTargets] = await Promise.all([
          getPortfolioOverview(env),
          getPortfolioPositions(env),
          getUserStrategies(env),
          getPortfolioRebalanceTargets(env).catch(() => ({ env, items: [] })),
        ]);

        if (!isMounted) return;

        setData({
          summary: overview.summary,
          positions,
          allocation: overview.allocation,
          userStrategies,
          rebalanceTargets,
        });
      } catch (err) {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to load portfolio");
      } finally {
        if (!isMounted) return;
        setLoading(false);
      }
    };

    load();
    return () => {
      isMounted = false;
    };
  }, [env]);

  const loadAnalytics = async (force = false) => {
    if (!data) return;
    if (!force && data.performance && data.drawdown && data.kpi && data.attribution) return;
    if (extrasLoading.analytics) return;
    setExtrasLoading((prev) => ({ ...prev, analytics: true }));
    setExtrasError(null);
    try {
      const benchmark = showBenchmark ? "SPY" : undefined;
      const [performance, drawdown, kpi, attribution] = await Promise.all([
        getPortfolioPerformance({ env, range, benchmark }),
        getPortfolioDrawdown(env, range),
        getPortfolioKpi(env, range),
        getPortfolioAttribution({ env, by: "strategy", range }),
      ]);
      setData((prev) =>
        prev
          ? {
              ...prev,
              performance,
              drawdown,
              kpi,
              attribution,
            }
          : prev
      );
    } catch (err) {
      setExtrasError(err instanceof Error ? err.message : "Failed to load analytics");
    } finally {
      setExtrasLoading((prev) => ({ ...prev, analytics: false }));
    }
  };

  useEffect(() => {
    if (!data) return;
    // Only refetch analytics when query params or base snapshot changes.
    // This avoids refetch loops caused by data updates from analytics responses.
    loadAnalytics(true);
  }, [env, range, showBenchmark, data?.summary?.as_of]);

  const loadActivity = async (force = false) => {
    if (!data) return;
    if (!force && data.activity) return;
    if (extrasLoading.activity) return;
    setExtrasLoading((prev) => ({ ...prev, activity: true }));
    setExtrasError(null);
    try {
      const activity = await getPortfolioActivity({
        env,
        types: "orders,trades,alerts,bot_runs",
        limit: 50,
      });
      setData((prev) => (prev ? { ...prev, activity } : prev));
    } catch (err) {
      setExtrasError(err instanceof Error ? err.message : "Failed to load activity");
    } finally {
      setExtrasLoading((prev) => ({ ...prev, activity: false }));
    }
  };

  const view = useMemo<PortfolioViewData | null>(() => {
    if (!data) return null;

    const positions = (data.positions.items ?? []).map((p) => ({
      symbol: p.symbol,
      name: p.symbol,
      qty: p.side === "short" ? -Math.abs(p.qty) : Math.abs(p.qty),
      side: p.side,
      avgPrice: p.avg_entry_price,
      currentPrice: p.current_price,
      pnl: p.unrealized_pnl.value,
      pnlPct: p.unrealized_pnl.pct,
      strategy: p.strategy?.name ?? "-",
    }));

    const sectorAllocation = (data.allocation.by_sector ?? []).map((s) => ({
      sector: s.sector,
      percent: s.pct,
      value: s.value,
    }));

    const equityCurve = (data.performance?.equity_curve ?? []).map((x) => ({
      date: x.t,
      value: x.equity,
    }));

    const drawdownData = (data.drawdown?.drawdown_curve ?? []).map((x) => ({
      date: x.t,
      value: x.drawdown_pct,
    }));

    return { positions, sectorAllocation, equityCurve, drawdownData };
  }, [data]);

  return {
    data,
    view,
    loading,
    error,
    extrasLoading,
    extrasError,
    loadAnalytics,
    loadActivity,
  };
}
