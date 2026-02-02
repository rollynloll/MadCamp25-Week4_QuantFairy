import type { Position } from "@/types/portfolio";

export default function PositionsTable({ positions }: { positions: Position[] }) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded">
      <div className="px-4 py-3 border-b border-gray-800">
        <h2 className="font-semibold">Positions</h2>
      </div>
      <div className="overflow-auto max-h-[400px]">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-[#0d1117] border-b border-gray-800">
            <tr className="text-xs text-gray-500">
              <th className="text-left py-2 px-4 font-medium">Symbol</th>
              <th className="text-right py-2 px-4 font-medium">Quantity</th>
              <th className="text-right py-2 px-4 font-medium">Avg Price</th>
              <th className="text-right py-2 px-4 font-medium">Current Price</th>
              <th className="text-right py-2 px-4 font-medium">P&L</th>
              <th className="text-right py-2 px-4 font-medium">P&L %</th>
              <th className="text-left py-2 px-4 font-medium">Strategy</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((pos) => (
              <tr
                key={pos.symbol}
                className="border-b border-gray-800/50 hover:bg-gray-900/30 transition-colors"
              >
                <td className="py-3 px-4">
                  <div className="font-semibold">{pos.symbol}</div>
                  <div className="text-xs text-gray-500">{pos.name}</div>
                </td>
                <td className={`text-right py-3 px-4 font-mono ${pos.side === "long" ? "text-green-500" : "text-red-500"}`}>
                  {pos.qty > 0 ? "+" : ""}{pos.qty}
                </td>
                <td className="text-right py-3 px-4 font-mono text-gray-400">
                  ${pos.avgPrice.toFixed(2)}
                </td>
                <td className="text-right py-3 px-4 font-mono">
                  ${pos.currentPrice.toFixed(2)}
                </td>
                <td className={`text-right py-3 px-4 font-mono font-semibold ${pos.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                  {pos.pnl >= 0 ? "+" : ""}${pos.pnl.toFixed(2)}
                </td>
                <td className={`text-right py-3 px-4 font-mono ${pos.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                  {pos.pnl >= 0 ? "+" : ""}{pos.pnlPct.toFixed(2)}%
                </td>
                <td className="py-3 px-4 text-gray-500">{pos.strategy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}