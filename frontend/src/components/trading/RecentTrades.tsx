import type { RecentTrade } from "@/types/trading";

export default function RecentTrades({ trades }: { trades: RecentTrade[] }) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Recent Trades</h2>
      <div className="space-y-1">
        <div className="text-xs text-gray-500 mb-2 flex justify-between px-2">
          <span>Time</span>
          <span>Price</span>
          <span>Size</span>
        </div>
        {trades.map((trade, i) => (
          <div
            key={i}
            className={`flex justify-between items-center text-sm py-1.5 px-2 rounded ${
              trade.side === "buy"
                ? "hover:bg-green-600/10"
                : "hover:bg-red-600/10"
            }`}
          >
            <span className="font-mono text-xs text-gray-500">
              {trade.time.split(".")[1]}
            </span>
            <span
              className={`font-mono font-semibold ${
                trade.side === "buy" ? "text-green-400" : "text-red-400"
              }`}
            >
              {trade.price.toFixed(2)}
            </span>
            <span className="font-mono text-gray-400">{trade.size}</span>
          </div>
        ))}
      </div>
    </div>
  );
}