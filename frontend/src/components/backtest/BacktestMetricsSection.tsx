
import BacktestMetrics from "@/components/backtest/BacktestMetrics";
import type { BacktestMetric } from "@/types/backtest";

type MetricsByStrategy = {
  label?: string;
  metrics: BacktestMetric[];
};

type Props = {
  items: MetricsByStrategy[];
};

export default function BacktestMetricsSection({ items }: Props) {
  if (items.length > 1) {
    return (
      <div className="space-y-4">
        {items.map((item, index) => (
          <div key={`${item.label}-${index}`} className="space-y-2">
            <div className="text-sm text-gray-400">{item.label}</div>
            <BacktestMetrics metrics={item.metrics} />
          </div>
        ))}
      </div>
    );
  }

  return <BacktestMetrics metrics={items[0]?.metrics ?? []} />;
}
