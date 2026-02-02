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
} from "@/types/portfolio";

import {
  getPortfolioSummary,
  getPortfolioPositions,
  getPortfolioAllocation,
  getPortfolioPerformance,
  getPortfolioDrawdown,
  getPortfolioKpi,
  getPortfolioActivity,
  getPortfolioAttribution,
} from "@/api/portfolio";

type PortfolioPageData = {
  summary: PortfolioSummaryResponse;
  positions: PortfolioPositionsResponse;
  allocation: PortfolioAllocationResponse;
  performance: PortfolioPerformanceResponse;
  drawdown: PortfolioDrawdownResponse;
  kpi: PortfolioKpiResponse;
  activity: PortfolioActivityResponse;
  attribution: PortfolioAttributionResponse;
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

  useEffect(() => {
    let isMounted = true;

    const load = async () => {
      setLoading(true);
      setError(null);

      try {
        const benchmark = showBenchmark ? "SPY" : undefined;

        // 병렬 로딩
        const [
          summary,
          positions,
          allocation,
          performance,
          drawdown,
          kpi,
          attribution,
        ] = await Promise.all([
          getPortfolioSummary(env),
          getPortfolioPositions(env),
          getPortfolioAllocation(env),
          getPortfolioPerformance({ env, range, benchmark }),
          getPortfolioDrawdown(env, range),
          getPortfolioKpi(env, range),
          getPortfolioAttribution({ env, by: "strategy", range }),
        ]);

        const activityResult = await getPortfolioActivity({
          env,
          types: "orders,trades,alerts,bot_runs",
          limit: 50,
        }).catch(() => ({
          env,
          items: [],
        }));

        if (!isMounted) return;

        setData({
          summary,
          positions,
          allocation,
          performance,
          drawdown,
          kpi,
          attribution,
          activity: activityResult,
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
  }, [env, range, showBenchmark]);

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

    const equityCurve = (data.performance.equity_curve ?? []).map((x) => ({
      date: x.t,
      value: x.equity,
    }));

    const drawdownData = (data.drawdown.drawdown_curve ?? []).map((x) => ({
      date: x.t,
      value: x.drawdown_pct,
    }));

    return { positions, sectorAllocation, equityCurve, drawdownData };
  }, [data]);

  return { data, view, loading, error };
}
