import { Clock } from "lucide-react";
import type { PublicStrategyListItem } from "@/types/strategy";
import MetricItem from "@/components/strategies/MetricItem";

interface StrategyCardProps {
  strategy: PublicStrategyListItem;
  onSelect?: (strategy: PublicStrategyListItem) => void;
}

export default function StrategyCard({ strategy, onSelect }: StrategyCardProps) {
  const updatedAt = new Date(strategy.updated_at);
  const isNew =
    Date.now() - updatedAt.getTime() < 7 * 24 * 60 * 60 * 1000;
  // const updatedLabel = updatedAt.toLocaleDateString("en-US", {
  //   month: "short",
  //   day: "numeric",
  //   year: "numeric",
  // });

  const pnlAmount = strategy.sample_metrics.pnl_amount;
  const pnlPct = strategy.sample_metrics.pnl_pct;

  return (
    <div
      className="bg-[#0d1117] border border-gray-800 rounded-lg p-6 hover:border-gray-700 transition-colors cursor-pointer"
      role="button"
      tabIndex={0}
      onClick={() => onSelect?.(strategy)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect?.(strategy);
        }
      }}
    >
      <div className="flex items-start justify-between gap-6 mb-2">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <h3 className="text-lg font-semibold">{strategy.name}</h3>
            <span className="px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded">
              {strategy.category}
            </span>
            {/* <span className="px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded">
              Risk: {strategy.risk_level}
            </span> */}
            {isNew && (
              <span className="px-2 py-0.5 bg-blue-600/20 text-blue-400 text-xs rounded">
                NEW
              </span>
            )}
          </div>

          {/* <p className="text-sm text-gray-400 mb-2">{strategy.one_liner}</p>

          <div className="flex flex-wrap gap-2">
            {strategy.tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-0.5 bg-gray-800 text-gray-400 text-xs rounded"
              >
                {tag}
              </span>
            ))}
          </div> */}
        </div>
      </div>

      <div className="flex items-center gap-6 text-sm text-gray-400 mb-4">
        <span>{strategy.sample_trade_stats.trades_count} trades</span>
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Avg hold: {strategy.sample_trade_stats.avg_hold_hours}h
        </span>
      </div>

      <div className="grid grid-cols-5 gap-6 pt-4 border-t border-gray-800">
        <MetricItem
          label="P&L"
          value={`$${Math.abs(pnlAmount).toFixed(2)}`}
          subValue={`${pnlPct >= 0 ? "+" : ""}${pnlPct}%`}
          isPositive={pnlAmount >= 0}
        />
        <MetricItem
          label="Sharpe"
          value={strategy.sample_metrics.sharpe.toFixed(2)}
          isPositive={strategy.sample_metrics.sharpe > 1.5}
        />
        <MetricItem
          label="Max DD"
          value={`${strategy.sample_metrics.max_drawdown_pct}%`}
          isPositive={false}
        />
        <MetricItem
          label="Win Rate"
          value={`${strategy.sample_metrics.win_rate_pct}%`}
          isPositive={strategy.sample_metrics.win_rate_pct > 60}
        />
        <MetricItem
          label="Status"
          value={`${strategy.sample_metrics.win_rate_pct}%`}
          isPositive={strategy.sample_metrics.win_rate_pct > 60}
        />
      </div>
    </div>
  );
}
