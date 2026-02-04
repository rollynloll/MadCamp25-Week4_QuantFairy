import { useMemo } from "react";
import { Activity, DollarSign, Target } from "lucide-react";
import MetricCard from "@/components/MetricCard";
import PerformanceChart from "@/components/PerformanceChart";
import ActiveStrategies from "@/components/ActiveStrategies";
import RecentTrades from "@/components/RecentTrades";
import { useDashboardContext } from "@/contexts/DashboardContext";
import { useLanguage } from "@/contexts/LanguageContext";
import type { StrategyState } from "@/types/dashboard";
import { useMarketStream } from "@/hooks/useMarketStream";

export default function Home() {
  const {
    data,
    loading,
    error,
    range,
    setRange,
    performanceLoading,
    userStrategies,
  } = useDashboardContext();
  const { tr } = useLanguage();

  const fmt = useMemo(
    () => new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }),
    []
  );
  const money = (v: number) => `$${fmt.format(v)}`;
  const pct = (v: number) => `${v >= 0 ? "+" : ""}${fmt.format(v)}%`;

  const recentTrades = data?.recent_trades ?? [];
  const streamSymbol = recentTrades[0]?.symbol ?? "AAPL";
  const { trades: streamTrades } = useMarketStream(streamSymbol);

  const runningStrategies = useMemo(
    () =>
      (userStrategies ?? [])
        .filter((strategy) => strategy.state === "running")
        .map((strategy) => ({
          strategy_id: strategy.user_strategy_id,
          name: strategy.name,
          state: strategy.state as StrategyState,
          positions_count: strategy.positions_count,
          pnl_today: strategy.today_pnl ?? { value: 0, pct: 0 },
        })),
    [userStrategies]
  );

  const recentTradesData = useMemo(() => {
    if (recentTrades.length > 0) {
      return recentTrades;
    }
    return streamTrades.map((trade, index) => ({
      fill_id: `${trade.time}-${index}`,
      filled_at: trade.time,
      symbol: streamSymbol,
      side: trade.side,
      qty: trade.size,
      price: trade.price,
      strategy_id: "market",
      strategy_name: "Market",
    }));
  }, [recentTrades, streamTrades, streamSymbol]);

  if (!data) {
    if (loading) {
      return (
        <div className="text-sm text-gray-400">
          {tr("Loading dashboard...", "대시보드 불러오는 중...")}
        </div>
      );
    }
    return (
      <div className="text-sm text-red-400">
        {error ?? tr("Failed to load dashboard", "대시보드를 불러오지 못했습니다.")}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title={tr("Equity", "총 자산")}
          value={money(data.account.equity)}
          change={`${tr("Today P&L", "일일 손익")} ${pct(data.account.today_pnl.pct)}`}
          isPositive={data.account.today_pnl.value >= 0}
          icon={<DollarSign className="w-5 h-5" />}
        />
        <MetricCard
          title={tr("Cash", "예수금")}
          value={money(data.account.cash)}
          change={`${data.account.active_positions.count} ${tr("positions", "개 보유")}`}
          isPositive={data.account.cash >= 0}
          icon={<DollarSign className="w-5 h-5" />}
        />
        <MetricCard
          title={tr("Today P&L", "일일 손익")}
          value={money(data.account.today_pnl.value)}
          change={pct(data.account.today_pnl.pct)}
          isPositive={data.account.today_pnl.value >= 0}
          icon={<Activity className="w-5 h-5" />}
        />
        <MetricCard
          title={tr("Active Positions", "보유 종목")}
          value={`${data.account.active_positions.count}`}
          change={`${data.account.active_positions.new_today} ${tr("new today", "오늘 신규")}`}
          isPositive={data.account.active_positions.new_today > 0}
          icon={<Target className="w-5 h-5" />}
        />
      </div>

      <PerformanceChart
        data={data.performance.equity_curve}
        range={range}
        onRangeChange={setRange}
        loading={performanceLoading}
      />

      <div className="grid grid-cols-2 gap-6">
        <ActiveStrategies data={runningStrategies} loading={!userStrategies} />
        <RecentTrades data={recentTradesData} />
      </div>
    </div>
  );
}