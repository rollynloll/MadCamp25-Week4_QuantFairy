import type { PerformancePoint, Strategy, Trade } from "../types/dashboard";

export const performanceData: PerformancePoint[] = [
  { date: "Jan 1", value: 100000 },
  { date: "Jan 8", value: 102500 },
  { date: "Jan 15", value: 101800 },
  { date: "Jan 22", value: 105200 },
  { date: "Jan 29", value: 108500 },
  { date: "Feb 5", value: 107200 },
  { date: "Feb 12", value: 110800 },
  { date: "Feb 19", value: 113400 },
  { date: "Feb 26", value: 112100 },
  { date: "Today", value: 115600 },
];

export const activeStrategies: Strategy[] = [
  { id: 1, name: "Mean Reversion Alpha", status: "running", pnl: 2850.5, pnlPct: 2.85, positions: 3 },
  { id: 2, name: "Momentum Breakout", status: "running", pnl: 1240.2, pnlPct: 1.24, positions: 2 },
  { id: 3, name: "Pairs Trading XLE/XLF", status: "paused", pnl: -450.8, pnlPct: -0.45, positions: 0 },
];

export const recentTrades: Trade[] = [
  { id: 1, time: "14:32:15", symbol: "AAPL", side: "BUY", qty: 100, price: 178.25, strategy: "Mean Reversion" },
  { id: 2, time: "14:28:42", symbol: "TSLA", side: "SELL", qty: 50, price: 242.18, strategy: "Momentum Breakout" },
  { id: 3, time: "14:15:33", symbol: "MSFT", side: "BUY", qty: 75, price: 412.5, strategy: "Mean Reversion" },
  { id: 4, time: "13:58:21", symbol: "NVDA", side: "SELL", qty: 25, price: 875.3, strategy: "Momentum Breakout" },
];