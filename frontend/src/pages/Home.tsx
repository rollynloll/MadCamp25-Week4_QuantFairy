import { Activity, DollarSign, Target, Zap } from "lucide-react";
import MetricCard from "@/components/MetricCard";
import PerformanceChart from "@/components/PerformanceChart";
import ActiveStrategies from "@/components/ActiveStrategies";
import RecentTrades from "@/components/RecentTrades";
import { useDashboard } from "@/hooks/useDashboard";
import { useState } from "react";
import type { Range } from "@/types/dashboard";

export default function Home() {
  const [range, setRange] = useState<Range>("1M");
  const { data, loading, error } = useDashboard(range);

  const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
  const money = (v: number) => `$${fmt.format(v)}`;
  const pct = (v: number) => `${v >= 0 ? "+" : ""}${fmt.format(v)}%`;

  if (loading) {
    return <div className="text-sm text-gray-400">Loading dashboard...</div>;
  }

  if (error || !data) {
    return (
      <div className="text-sm text-red-400">
        {error ?? "Failed to load dashboard"}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title="Equity"
          value={money(data.account.equity)}
          change={`Updated ${new Date(data.account.updated_at).toLocaleTimeString()}`}
          isPositive={data.kpi.today_pnl.value >= 0}
          icon={<DollarSign className="w-5 h-5" />}
        />
        <MetricCard
          title="Cash"
          value={money(data.account.cash)}
          change={`Buying Power ${money(data.account.buying_power)}`}
          isPositive={data.account.cash >= 0}
          icon={<DollarSign className="w-5 h-5" />}
        />
        <MetricCard
          title="Today P&L"
          value={money(data.kpi.today_pnl.value)}
          change={pct(data.kpi.today_pnl.pct)}
          isPositive={data.kpi.today_pnl.value >= 0}
          icon={<Activity className="w-5 h-5" />}
        />
        <MetricCard
          title="Active Positions"
          value={`${data.kpi.active_positions.count}`}
          change={`${data.kpi.active_positions.new_today} new today`}
          isPositive={data.kpi.active_positions.new_today > 0}
          icon={<Target className="w-5 h-5" />}
        />
      </div>

      <PerformanceChart
        data={data.performance.equity_curve} 
        range={range} 
        onRangeChange={setRange} 
      />

      <div className="grid grid-cols-2 gap-6">
        <ActiveStrategies data={data.active_strategies} />
        <RecentTrades data={data.recent_trades} />
      </div>
    </div>
  );
}
