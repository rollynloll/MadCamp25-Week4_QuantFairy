import type { BacktestMetric } from "@/types/backtest";

export default function BacktestMetrics({ metrics }: { metrics: BacktestMetric[] }) {
  return (
    <div className="grid grid-cols-5 gap-4">
      {metrics.map((m) => (
        <div key={m.label} className="bg-[#0d1117] border border-gray-800 rounded-lg p-5">
          <div className="text-sm text-gray-400 mb-2">{m.label}</div>
          <div className={`text-2xl font-semibold ${m.isPositive ? "text-green-500" : "text-gray-300"}`}>
            {m.value}
          </div>
        </div>
      ))}
    </div>
  );
}