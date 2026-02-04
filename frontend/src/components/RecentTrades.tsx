import type { TradeSide } from "@/types/dashboard";
import { useLanguage } from "@/contexts/LanguageContext";

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
  const { tr } = useLanguage();
  const gridCols =
    "grid-cols-[96px_72px_64px_80px_96px_minmax(120px,1fr)]";

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6 flex h-[460px] flex-col">
      <h2 className="text-lg font-semibold mb-4">{tr("Recent Trades", "최근 거래 내역")}</h2>
      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        <div className={`sticky top-0 z-10 hidden ${gridCols} gap-3 border-b border-gray-800 bg-[#0d1117] px-3 py-2 text-xs font-medium text-gray-500 md:grid`}>
          <span>{tr("Time", "시간")}</span>
          <span>{tr("Symbol", "종목")}</span>
          <span>{tr("Side", "구분")}</span>
          <span className="text-right">{tr("Qty", "수량")}</span>
          <span className="text-right">{tr("Price", "가격")}</span>
          <span>{tr("Strategy", "전략")}</span>
        </div>

        <div className="space-y-2 pt-1">
          {data.map((trade) => (
            <div
              key={trade.fill_id}
              className="rounded bg-[#0a0d14] px-3 py-2 text-sm transition-colors hover:bg-gray-800/50"
            >
              <div className={`flex flex-col gap-1 md:grid ${gridCols} md:items-center md:gap-3`}>
                <span className="font-mono text-xs text-gray-500">
                  {new Date(trade.filled_at).toLocaleTimeString()}
                </span>
                <span className="font-semibold">{trade.symbol}</span>
                <span
                  className={`text-xs font-semibold ${
                    trade.side === "buy" ? "text-green-500" : "text-red-500"
                  }`}
                >
                  {trade.side.toUpperCase()}
                </span>
                <span className="font-mono text-gray-400 md:text-right">{trade.qty}</span>
                <span className="font-mono text-gray-300 md:text-right">
                  ${Number(trade.price).toFixed(2)}
                </span>
                <span className="truncate text-xs text-gray-500">{trade.strategy_name}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
