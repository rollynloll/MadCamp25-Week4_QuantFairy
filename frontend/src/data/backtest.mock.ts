import type { EquityPoint, MonthlyReturn, BacktestMetric, BacktestConfigData } from "@/types/backtest";

export const equityCurve: EquityPoint[] = [
  { date: "2024-01", value: 100000, benchmark: 100000 },
  { date: "2024-02", value: 103500, benchmark: 101200 },
  { date: "2024-03", value: 107200, benchmark: 102800 },
  { date: "2024-04", value: 105800, benchmark: 103500 },
  { date: "2024-05", value: 110500, benchmark: 105100 },
  { date: "2024-06", value: 114200, benchmark: 106200 },
  { date: "2024-07", value: 112900, benchmark: 107800 },
  { date: "2024-08", value: 117600, benchmark: 109200 },
  { date: "2024-09", value: 121300, benchmark: 110500 },
  { date: "2024-10", value: 119800, benchmark: 111800 },
  { date: "2024-11", value: 125400, benchmark: 113000 },
  { date: "2024-12", value: 128900, benchmark: 114500 },
];

export const monthlyReturns: MonthlyReturn[] = [
  { month: "Jan", return: 3.5 },
  { month: "Feb", return: 3.6 },
  { month: "Mar", return: 3.5 },
  { month: "Apr", return: -1.3 },
  { month: "May", return: 4.4 },
  { month: "Jun", return: 3.3 },
  { month: "Jul", return: -1.1 },
  { month: "Aug", return: 4.2 },
  { month: "Sep", return: 3.2 },
  { month: "Oct", return: -1.2 },
  { month: "Nov", return: 4.7 },
  { month: "Dec", return: 2.8 },
];

export const metrics: BacktestMetric[] = [
  { label: "Total Return", value: "+28.9%", isPositive: true },
  { label: "Annual Return", value: "+28.9%", isPositive: true },
  { label: "Sharpe Ratio", value: "2.34", isPositive: true },
  { label: "Max Drawdown", value: "-5.2%", isPositive: false },
  { label: "Win Rate", value: "68.4%", isPositive: true },
];

export const configData: BacktestConfigData = {
  strategy: "Mean Reversion Alpha",
  initialCapital: "$100,000",
  commission: "$0.005/share",
  slippage: "0.05%",
};