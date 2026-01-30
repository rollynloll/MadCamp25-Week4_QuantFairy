import type { PortfolioSummaryData } from "@/types/portfolio";

export default function PortfolioSummary({
  totalValue,
  totalPnL,
  openPositions,
  longCount,
  shortCount
}: PortfolioSummaryData) {
  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-5">
        <div className="text-sm text-gray-400 mb-1">Total Value</div>
        <div className="text-2xl font-semibold">${totalValue.toFixed(2)}</div>
      </div>
      <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-5">
        <div className="text-sm text-gray-400 mb-1">Unrealized P&L</div>
        <div
          className={`text-2xl font-semibold ${
            totalPnL >= 0 ? "text-green-500" : "text-red-500"
          }`}
        >
          {totalPnL >= 0 ? "+" : ""}${totalPnL.toFixed(2)}
        </div>
      </div>
      <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-5">
        <div className="text-sm text-gray-400 mb-1">Open Positions</div>
        <div className="text-2xl font-semibold">{openPositions}</div>
      </div>
      <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-5">
        <div className="text-sm text-gray-400 mb-1">Long / Short</div>
        <div className="text-2xl font-semibold">
          {longCount} / {shortCount}
        </div>
      </div>
    </div>
  );
}