import { Activity, DollarSign, Target } from "lucide-react";
import MetricCard from "@/components/MetricCard";
import PerformanceChart from "@/components/PerformanceChart";
import ActiveStrategies from "@/components/ActiveStrategies";
import RecentTrades from "@/components/RecentTrades";
import { useDashboardContext } from "@/contexts/DashboardContext";
import { useLanguage } from "@/contexts/LanguageContext";

export default function Home() {
  const { data, loading, error, range, setRange } = useDashboardContext();
  const { tr } = useLanguage();

  const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
  const money = (v: number) => `$${fmt.format(v)}`;
  const pct = (v: number) => `${v >= 0 ? "+" : ""}${fmt.format(v)}%`;

  if (loading) {
    return <div className="text-sm text-gray-400">{tr("Loading dashboard...", "대시보드 불러오는 중...")}</div>;
  }

  if (error || !data) {
    return (
      <div className="text-sm text-red-400">
        {error ?? tr("Failed to load dashboard", "대시보드를 불러오지 못했습니다")}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title={tr("Equity", "총 자산")}
          value={money(data.account.equity)}
          change={`${tr("Today P&L", "금일 손익")} ${pct(data.account.today_pnl.pct)}`}
          isPositive={data.account.today_pnl.value >= 0}
          icon={<DollarSign className="w-5 h-5" />}
        />
        <MetricCard
          title={tr("Cash", "예수금")}
          value={money(data.account.cash)}
          change={`${data.account.active_positions.count} ${tr("positions", "종목 수")}`}
          isPositive={data.account.cash >= 0}
          icon={<DollarSign className="w-5 h-5" />}
        />
        <MetricCard
          title={tr("Today P&L", "금일 손익")}
          value={money(data.account.today_pnl.value)}
          change={pct(data.account.today_pnl.pct)}
          isPositive={data.account.today_pnl.value >= 0}
          icon={<Activity className="w-5 h-5" />}
        />
        <MetricCard
          title={tr("Active Positions", "보유 종목 수")}
          value={`${data.account.active_positions.count}`}
          change={`${data.account.active_positions.new_today} ${tr("new today", "금일 신규")}`}
          isPositive={data.account.active_positions.new_today > 0}
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
