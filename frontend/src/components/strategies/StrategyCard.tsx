import { Pause, Play, Settings, Clock } from "lucide-react";
import type { Strategy } from "@/types/strategy";
import MetricItem from "@/components/strategies/MetricItem";

interface StrategyCardProps {
  strategy: Strategy;
}

export default function StrategyCard({ strategy }: StrategyCardProps) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6 hover:border-gray-700 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-start gap-4 flex-1">
          <div className="pt-1">
            <div
              className={`w-3 h-3 rounded-full ${
                strategy.status === "running"
                  ? "bg-green-500 animate-pulse"
                  : strategy.status === "paused"
                  ? "bg-yellow-500"
                  : "bg-gray-600"
              }`}
            />
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h3 className="text-lg font-semibold">{strategy.name}</h3>
              <span className="px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded">
                {strategy.type}
              </span>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-400">
              <span>{strategy.trades} trades</span>
              <span>Win rate: {strategy.winRate}%</span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Avg hold: {strategy.avgHoldTime}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {strategy.status === "running" ? (
            <button className="p-2 hover:bg-gray-800 rounded transition-colors">
              <Pause className="w-4 h-4" />
            </button>
          ) : (
            <button className="p-2 hover:bg-gray-800 rounded transition-colors">
              <Play className="w-4 h-4" />
            </button>
          )}
          <button className="p-2 hover:bg-gray-800 rounded transition-colors">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-6 pt-4 border-t border-gray-800">
        <MetricItem
          label="P&L"
          value={`$${Math.abs(strategy.pnl).toFixed(2)}`}
          subValue={`${strategy.pnlPct >= 0 ? "+" : ""}${strategy.pnlPct}%`}
          isPositive={strategy.pnl >= 0}
        />
        <MetricItem
          label="Sharpe Ratio"
          value={strategy.sharpe.toFixed(2)}
          isPositive={strategy.sharpe > 1.5}
        />
        <MetricItem
          label="Max Drawdown"
          value={`${strategy.maxDrawdown}%`}
          isPositive={false}
        />
        <MetricItem
          label="Win Rate"
          value={`${strategy.winRate}%`}
          isPositive={strategy.winRate > 60}
        />
        <MetricItem
          label="Status"
          value={`${strategy.status.charAt(0).toUpperCase()}${strategy.status.slice(1)}`}
          isPositive={strategy.status === "running"}
        />
      </div>
    </div>
  );
}
