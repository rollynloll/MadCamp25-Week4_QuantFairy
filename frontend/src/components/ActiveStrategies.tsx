import type { StrategyState } from "@/types/dashboard";

interface ActiveStrategy {
  strategy_id: string;
  name: string;
  state: StrategyState;
  positions_count: number;
  pnl_today: {
    value: number;
    pct: number;
  };
}

export default function ActiveStrategies({ data }: { data: ActiveStrategy[] }) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Active Strategies</h2>
      <div className="space-y-3">
        {data.map((strategy) => (
          <div 
            key={strategy.strategy_id} 
            className="p-4 bg-[#0a0d14] border border-gray-800 rounded-lg hover:border-gray-700 transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    strategy.state === "running"
                      ? "bg-green-500"
                      : strategy.state === "paused"
                      ? "bg-yellow-500"
                      : strategy.state === "idle"
                      ? "bg-gray-500"
                      : "bg-red-500"
                  }`}
                />
                <span
                  className={`text-sm font-semibold ${
                    strategy.pnl_today.value >= 0 ? "text-green-500" : "text-red-500"
                  }`}
                >
                  {strategy.pnl_today.value >= 0 ? "+" : ""}
                  ${strategy.pnl_today.value.toFixed(2)}
                </span>
              </div>
              <span
                className={`text-sm font-semibold ${
                  strategy.pnl_today.value >= 0 ? "text-green-500" : "text-red-500"
                }`}
              >
                {strategy.pnl_today.value >= 0 ? "+" : ""}
                ${strategy.pnl_today.value.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{strategy.positions_count} positions</span>
              <span
                className={
                  strategy.state === "running"
                    ? "text-green-500"
                    : strategy.state === "paused"
                    ? "text-yellow-500"
                    : strategy.state === "idle"
                    ? "text-gray-400"
                    : "text-red-500"
                }
              >
                {strategy.state === "running"
                  ? "Running"
                  : strategy.state === "paused"
                  ? "Paused"
                  : strategy.state === "idle"
                  ? "Idle"
                  : "Error"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}