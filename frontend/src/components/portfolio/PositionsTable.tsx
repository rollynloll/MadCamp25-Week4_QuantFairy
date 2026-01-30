import type { Position } from "@/types/portfolio";

export default function PositionsTable({ positions }: { positions: Position[] }) {
  return (
    <div className="col-span-2 bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Positions</h2>
      <div className="space-y-1">
        <div className="grid grid-cols-8 gap-4 px-3 py-2 text-xs text-gray-500 font-medium border-b border-gray-800">
          <div className="col-span-2">Symbol</div>
          <div className="text-right">Qty</div>
          <div className="text-right">Avg Price</div>
          <div className="text-right">Current</div>
          <div className="text-right">P&L</div>
          <div className="text-right">P&L %</div>
          <div>Strategy</div>
        </div>

        {positions.map((pos) => (
          <div
            key={pos.symbol}
            className="grid grid-cols-8 gap-4 px-3 py-3 hover:bg-gray-800/50 rounded transition-colors text-sm"
          >
            <div className="col-span-2">
              <div className="font-semibold">{pos.symbol}</div>
              <div className="text-xs text-gray-500">{pos.name}</div>
            </div>
            <div
              className={`text-right font-mono ${
                pos.qty > 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {pos.qty > 0 ? "+" : ""}
              {pos.qty}
            </div>
            <div className="text-right font-mono text-gray-400">
              ${pos.avgPrice.toFixed(2)}
            </div>
            <div className="text-right font-mono">
              ${pos.currentPrice.toFixed(2)}
            </div>
            <div
              className={`text-right font-mono font-semibold ${
                pos.pnl >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {pos.pnl >= 0 ? "+" : ""}${pos.pnl.toFixed(2)}
            </div>
            <div
              className={`text-right font-mono ${
                pos.pnl >= 0 ? "text-green-500" : "text-red-500"
              }`}
            >
              {pos.pnl >= 0 ? "+" : ""}
              {pos.pnlPct.toFixed(2)}%
            </div>
            <div className="text-xs text-gray-500 truncate">{pos.strategy}</div>
          </div>
        ))}
      </div>
    </div>
  );
}