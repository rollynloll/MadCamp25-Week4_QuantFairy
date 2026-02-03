import type { Position } from "@/types/portfolio";
import { useLanguage } from "@/contexts/LanguageContext";

type Props = {
  positions: Position[];
  selectedSymbol?: string;
  onSelect?: (symbol: string) => void;
};

export default function PositionsTrade({ positions, selectedSymbol, onSelect }: Props) {
  const { tr } = useLanguage();
  return (
    <div className="bg-[#0d1117] border border-gray-800 rounded">
      <div className="px-4 py-3 border-b border-gray-800">
        <h2 className="font-semibold">{tr("Positions", "포지션")}</h2>
      </div>
      <div className="overflow-auto max-h-[400px]">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-[#0d1117] border-b border-gray-800">
            <tr className="text-xs text-gray-500">
              <th className="text-left py-2 px-4 font-medium">{tr("Symbol", "종목 코드")}</th>
              <th className="text-right py-2 px-4 font-medium">{tr("Quantity", "수량")}</th>
              <th className="text-right py-2 px-4 font-medium">{tr("Avg Price", "평균 매입가")}</th>
              <th className="text-right py-2 px-4 font-medium">{tr("Current Price", "현재가")}</th>
              <th className="text-right py-2 px-4 font-medium">{tr("P&L", "손익")}</th>
              <th className="text-right py-2 px-4 font-medium">{tr("P&L %", "손익률")}</th>
              <th className="text-left py-2 px-4 font-medium">{tr("Strategy", "전략")}</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((pos) => (
              <tr
                key={pos.symbol}
                onClick={() => onSelect?.(pos.symbol)}
                className={`border-b border-gray-800/50 hover:bg-gray-900/30 transition-colors ${
                  onSelect ? "cursor-pointer" : ""
                } ${
                  selectedSymbol === pos.symbol
                    ? "bg-blue-600/10 border-l-2 border-l-blue-400"
                    : ""
                }`}
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
