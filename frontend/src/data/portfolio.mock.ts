import type { Position } from "@/types/portfolio";

export const positions: Position[] = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    qty: 100,
    avgPrice: 175.30,
    currentPrice: 178.25,
    pnl: 295.00,
    pnlPct: 1.68,
    strategy: "Mean Reversion Alpha",
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corp.",
    qty: 75,
    avgPrice: 410.50,
    currentPrice: 412.50,
    pnl: 150.00,
    pnlPct: 0.49,
    strategy: "Mean Reversion Alpha",
  },
  {
    symbol: "NVDA",
    name: "NVIDIA Corp.",
    qty: -25,
    avgPrice: 880.20,
    currentPrice: 875.30,
    pnl: 122.50,
    pnlPct: 0.56,
    strategy: "Momentum Breakout",
  },
  {
    symbol: "TSLA",
    name: "Tesla Inc.",
    qty: -50,
    avgPrice: 245.80,
    currentPrice: 242.18,
    pnl: 181.00,
    pnlPct: 1.47,
    strategy: "Momentum Breakout",
  },
  {
    symbol: "GOOGL",
    name: "Alphabet Inc.",
    qty: 60,
    avgPrice: 142.10,
    currentPrice: 141.25,
    pnl: -51.00,
    pnlPct: -0.60,
    strategy: "Mean Reversion Alpha",
  },
];

export const allocation = [
  { category: "Technology", value: 42, amount: 48580 },
  { category: "Energy", value: 28, amount: 32400 },
  { category: "Financial", value: 18, amount: 20820 },
  { category: "Healthcare", value: 8, amount: 9260 },
  { category: "Cash", value: 4, amount: 4540 },
];