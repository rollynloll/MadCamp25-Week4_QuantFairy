import type { RecentTrade } from "@/types/trading";
import { useLanguage } from "@/contexts/LanguageContext";

export default function RecentTrades({ trades }: { trades: RecentTrade[] }) {
  const { tr } = useLanguage();
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">{tr("Recent Trades", "최근 체결")}</h2>
      <div className="space-y-1">
        <div className="text-xs text-gray-500 mb-2 flex justify-between px-2">
          <span>{tr("Time", "시간")}</span>
          <span>{tr("Price", "가격")}</span>
          <span>{tr("Size", "수량")}</span>
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
              {new Date(trade.time).toLocaleTimeString()}
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
