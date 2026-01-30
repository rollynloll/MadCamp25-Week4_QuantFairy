import type { TradeSide } from "@/types/dashboard";

interface RecentTrade {
  fill_id: string;
  filled_at: string;
  symbol: string;
  side: TradeSide;
  qty: number;
  price: number;
  strategy_id: string;
  strategy_name: string;
}

export default function RecentTrades({ data }: { data: RecentTrade[] }) {
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Recent Trades</h2>
      <div className="space-y-2">
        {data.map((trade) => (
          <div
            key={trade.fill_id}
            className="flex items-center justify-between py-2 px-3 bg-[#0a0d14] rounded hover:bg-gray-800/50 transition-colors text-sm"
          >
            <div className="flex items-center gap-3 flex-1">
              <span className="text-gray-500 text-xs font-mono w-16">
                {new Date(trade.filled_at).toLocaleTimeString()}
              </span>
              <span className="font-semibold w-12">{trade.symbol}</span>
              <span
                className={`w-10 text-xs font-semibold ${
                  trade.side === "buy" ? "text-green-500" : "text-red-500"
                }`}
              >
                {trade.side.toUpperCase()}
              </span>
              <span className="text-gray-400 w-12">{trade.qty}</span>
              <span className="text-gray-300 font-mono w-16">
                ${trade.price}
              </span>
            </div>
            <span className="text-xs text-gray-500">{trade.strategy_name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}