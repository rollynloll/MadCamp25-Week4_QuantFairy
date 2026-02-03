import EquityCurveChart from "@/components/backtest/EquityCurveChart";
import MonthlyReturnsChart from "@/components/backtest/MonthlyReturnsChart";
import PortfolioChangeChart, {
  type PortfolioChangePoint,
  type PortfolioHoldingsSeries
} from "@/components/backtest/PortfolioChangeChart";
import type { MonthlyReturn } from "@/types/backtest";
import type { EquityCurvePoint, EquitySeries } from "@/utils/backtestUtils";

type Props = {
  equityCurve: EquityCurvePoint[];
  equitySeries: EquitySeries[];
  hasMultipleStrategies: boolean;
  monthlyReturns: MonthlyReturn[];
  portfolioHoldings: { data: PortfolioChangePoint[]; series: PortfolioHoldingsSeries[] };
  tr: (en: string, ko: string) => string;
};

export default function BacktestCharts({
  equityCurve,
  equitySeries,
  hasMultipleStrategies,
  monthlyReturns,
  portfolioHoldings,
  tr
}: Props) {
  return (
    <>
      <EquityCurveChart
        data={equityCurve}
        series={equitySeries}
        height={hasMultipleStrategies ? 420 : 300}
      />
      {hasMultipleStrategies ? (
        <div className="bg-[#0d1117] border border-gray-800 rounded-lg p-6 text-sm text-gray-400">
          {tr(
            "Monthly Returns are disabled when comparing multiple strategies.",
            "Monthly Returns는 여러 전략 비교 시 비활성화됩니다. 전략이 하나일 때만 표시됩니다."
          )}
        </div>
      ) : (
        <>
          <MonthlyReturnsChart data={monthlyReturns} />
          <PortfolioChangeChart
            data={portfolioHoldings.data}
            series={portfolioHoldings.series}
          />
        </>
      )}
    </>
  );
}
