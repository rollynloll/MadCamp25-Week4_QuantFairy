import { Activity, DollarSign, Target, Zap } from "lucide-react";
import MetricCard from "@/components/MetricCard";
import PerformanceChart from "@/components/PerformanceChart";
import ActiveStrategies from "@/components/ActiveStrategies";
import RecentTrades from "@/components/RecentTrades";
import { useDashboard } from "@/hooks/useDashboard";

export default function Home() {
  const { data, loading, error } = useDashboard();

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
        <MetricCard title="Total P&L" value="$15,600" change="+15.6%" isPositive icon={<DollarSign className="w-5 h-5" />} />
        <MetricCard title="Win Rate" value="68.4%" change="+2.1%" isPositive icon={<Target className="w-5 h-5" />} />
        <MetricCard title="Active Positions" value="5" change="2 new today" isPositive={false} icon={<Activity className="w-5 h-5" />} />
        <MetricCard title="Sharpe Ratio" value="2.34" change="+0.12" isPositive icon={<Zap className="w-5 h-5" />} />
      </div>

      <PerformanceChart data={data.performance} />

      <div className="grid grid-cols-2 gap-6">
        <ActiveStrategies data={data.strategies} />
        <RecentTrades data={data.trades} />
      </div>
    </div>
  );
}
