import type { Strategy } from "@/types/dashboard";

export default function ActiveStrategies({ data }: { data: Strategy[] }) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Active Strategies</h2>
      <div className="space-y-3">
        {data.map((strategy) => (
          <div key={strategy.id} className="p-4 bg-[#0a0d14] border border-gray-800 rounded-lg hover:border-gray-700 transition-colors">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${strategy.status === "running" ? "bg-green-500" : "bg-yellow-500"}`}
                />
                <span className="font-medium text-sm">{strategy.name}</span>
              </div>
              <span className={`text-sm font-semibold ${strategy.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                {strategy.pnl >= 0 ? "+" : ""}${strategy.pnl.toFixed(2)}
              </span>
            </div>
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{strategy.positions} positions</span>
              <span className={strategy.pnl >= 0 ? "text-green-500" : "text-red-500"}>
                {strategy.pnl >= 0 ? "+" : ""}
                {strategy.pnlPct}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}