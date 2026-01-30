import BacktestHeader from "@/components/backtest/BacktestHeader";
import BacktestConfig from "@/components/backtest/BacktestConfig";
import BacktestMetrics from "@/components/backtest/BacktestMetrics";
import EquityCurveChart from "@/components/backtest/EquityCurveChart";
import MonthlyReturnsChart from "@/components/backtest/MonthlyReturnsChart";
import { equityCurve, monthlyReturns, metrics, configData } from "@/data/backtest.mock";

export default function Backtest() {
  return (
    <div className="space-y-6">
      <BacktestHeader />
      <BacktestConfig config={configData} />
      <BacktestMetrics metrics={metrics} />
      <EquityCurveChart data={equityCurve} />
      <MonthlyReturnsChart data={monthlyReturns} />
    </div>
  );
}