import type { BacktestMetric, TradeLogRow } from "@/types/strategyBuilder";
import { useLanguage } from "@/contexts/LanguageContext";

interface BacktestResultsProps {
  metrics: BacktestMetric[];
  trades: TradeLogRow[];
}

export default function BacktestResults({ metrics, trades }: BacktestResultsProps) {
  const { tr } = useLanguage();

  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-200">
          {tr("Backtest Results", "백테스트 결과")}
        </h2>
        <span className="text-xs text-gray-500">{tr("Mock data", "목업 데이터")}</span>
      </div>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-lg border border-dashed border-gray-700 bg-gradient-to-br from-gray-900/40 to-transparent p-4 h-56">
          <div className="text-xs text-gray-500">{tr("Equity Curve", "에쿼티 커브")}</div>
          <div className="mt-4 h-36 w-full rounded bg-[linear-gradient(120deg,#1f2937_0%,#0b0f17_55%,#111827_100%)]" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded border border-gray-800 bg-gray-900/40 p-3">
              <div className="text-xs text-gray-500">{metric.label}</div>
              <div className="text-sm font-semibold text-white mt-1">{metric.value}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-6">
        <div className="text-xs text-gray-500 mb-2">{tr("Trade Log", "거래 로그")}</div>
        <div className="overflow-auto rounded border border-gray-800">
          <table className="w-full text-xs">
            <thead className="bg-gray-900/60 text-gray-500">
              <tr>
                <th className="text-left px-3 py-2">{tr("Time", "시간")}</th>
                <th className="text-left px-3 py-2">{tr("Symbol", "종목")}</th>
                <th className="text-left px-3 py-2">{tr("Side", "구분")}</th>
                <th className="text-right px-3 py-2">{tr("Qty", "수량")}</th>
                <th className="text-right px-3 py-2">{tr("Price", "가격")}</th>
                <th className="text-right px-3 py-2">{tr("PnL", "손익")}</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr key={trade.id} className="border-t border-gray-800/70 text-gray-300">
                  <td className="px-3 py-2">{trade.time}</td>
                  <td className="px-3 py-2">{trade.symbol}</td>
                  <td className={`px-3 py-2 ${trade.side === "BUY" ? "text-green-400" : "text-red-400"}`}>
                    {trade.side}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">{trade.qty}</td>
                  <td className="px-3 py-2 text-right font-mono">{trade.price.toFixed(2)}</td>
                  <td className={`px-3 py-2 text-right font-mono ${trade.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                    {trade.pnl >= 0 ? "+" : ""}{trade.pnl.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
