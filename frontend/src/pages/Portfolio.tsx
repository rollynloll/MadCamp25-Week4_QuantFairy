import AllocationCard from "@/components/portfolio/AllocationCard";
import PortfolioSummary from "@/components/portfolio/PortfolioSummary";
import PositionsTable from "@/components/portfolio/PositionsTable";
import { allocation, positions } from "@/data/portfolio.mock";

export default function Portfolio() {
  const totalPnL = positions.reduce((sum, pos) => sum + pos.pnl, 0);
  const totalValue = positions.reduce(
    (sum, pos) => sum + Math.abs(pos.qty) * pos.currentPrice, 0
  );

  const openPoritions = positions.length;
  const longCount = positions.filter((p) => p.qty > 0).length;
  const shortCount = positions.filter((p) => p.qty < 0).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold mb-1">Portfolio</h1>
        <p className="text-sm text-gray-400">
          Current positions and allocation
        </p>
      </div>

      <PortfolioSummary
        totalValue={totalValue}
        totalPnL={totalPnL}
        openPositions={openPoritions}
        longCount={longCount}
        shortCount={shortCount}
      />

      <div className="grid grid-cols-3 gap-6">
        <PositionsTable positions={positions} />
        <AllocationCard allocation={allocation} />
      </div>
    </div>
  );
}