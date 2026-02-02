import type {
  Position,
  Strategy,
  SectorAllocationItem,
  EquityPoint,
  DrawdownPoint,
  Order,
  AlertItem,
  BotRun,
} from "@/types/portfolio";

export const positions: Position[] = [
  { symbol: "AAPL", name: "Apple Inc.", qty: 100, side: "long", avgPrice: 175.3, currentPrice: 178.25, pnl: 295, pnlPct: 1.68, strategy: "Mean Reversion" },
  { symbol: "MSFT", name: "Microsoft Corp.", qty: 75, side: "long", avgPrice: 410.5, currentPrice: 412.5, pnl: 150, pnlPct: 0.49, strategy: "Momentum" },
  { symbol: "NVDA", name: "NVIDIA Corp.", qty: 25, side: "long", avgPrice: 875.2, currentPrice: 880.3, pnl: 127.5, pnlPct: 0.58, strategy: "Growth Alpha" },
  { symbol: "GOOGL", name: "Alphabet Inc.", qty: 60, side: "long", avgPrice: 142.1, currentPrice: 141.25, pnl: -51, pnlPct: -0.6, strategy: "Value" },
  { symbol: "TSLA", name: "Tesla Inc.", qty: -50, side: "short", avgPrice: 245.8, currentPrice: 242.18, pnl: 181, pnlPct: 1.47, strategy: "Short Vol" },
];

export const strategies: Strategy[] = [
  { id: 1, name: "Mean Reversion", state: "running", currentWeight: 28.5, targetWeight: 30, positionsCount: 2, lastRun: "2 min ago" },
  { id: 2, name: "Momentum", state: "running", currentWeight: 22.0, targetWeight: 20, positionsCount: 1, lastRun: "2 min ago" },
  { id: 3, name: "Growth Alpha", state: "running", currentWeight: 18.3, targetWeight: 15, positionsCount: 1, lastRun: "2 min ago" },
  { id: 4, name: "Value", state: "paused", currentWeight: 8.5, targetWeight: 10, positionsCount: 1, lastRun: "1 hour ago" },
  { id: 5, name: "Short Vol", state: "running", currentWeight: 10.2, targetWeight: 10, positionsCount: 1, lastRun: "2 min ago" },
];

export const sectorAllocation: SectorAllocationItem[] = [
  { sector: "Technology", percent: 67.0, value: 77476 },
  { sector: "Consumer Discretionary", percent: 10.2, value: 11791 },
  { sector: "Communication Services", percent: 7.3, value: 8439 },
  { sector: "Cash", percent: 12.5, value: 14450 },
];

export const equityCurve: EquityPoint[] = [
  { date: "Jan 1", value: 100000 },
  { date: "Jan 8", value: 102500 },
  { date: "Jan 15", value: 101800 },
  { date: "Jan 22", value: 105200 },
  { date: "Jan 29", value: 108500 },
  { date: "Feb 5", value: 110200 },
  { date: "Feb 12", value: 112800 },
  { date: "Feb 19", value: 114100 },
  { date: "Feb 26", value: 113400 },
  { date: "Today", value: 115600 },
];

export const drawdownData: DrawdownPoint[] = [
  { date: "Jan 1", value: 0 },
  { date: "Jan 8", value: 0 },
  { date: "Jan 15", value: -0.68 },
  { date: "Jan 22", value: 0 },
  { date: "Jan 29", value: 0 },
  { date: "Feb 5", value: 0 },
  { date: "Feb 12", value: 0 },
  { date: "Feb 19", value: 0 },
  { date: "Feb 26", value: -0.61 },
  { date: "Today", value: 0 },
];

export const orders: Order[] = [
  { id: 1, time: "14:32:15", type: "BUY", symbol: "AAPL", qty: 100, status: "filled", strategy: "Mean Reversion" },
  { id: 2, time: "14:28:42", type: "SELL", symbol: "TSLA", qty: 50, status: "filled", strategy: "Short Vol" },
  { id: 3, time: "14:15:33", type: "BUY", symbol: "MSFT", qty: 75, status: "partial", strategy: "Momentum" },
];

export const alerts: AlertItem[] = [
  { id: 1, time: "14:35:12", level: "warning", message: "Position size approaching limit for AAPL", strategy: "Mean Reversion" },
  { id: 2, time: "13:22:45", level: "error", message: "Failed to execute order: insufficient buying power", strategy: "Value" },
];

export const botRuns: BotRun[] = [
  { id: 1, time: "14:30:00", status: "success", duration: "2.3s", trades: 5 },
  { id: 2, time: "14:00:00", status: "success", duration: "1.8s", trades: 3 },
  { id: 3, time: "13:30:00", status: "failed", duration: "0.5s", trades: 0 },
];