export interface PerformancePoint {
  date: string;
  value: number;
}

export interface Strategy {
  id: number;
  name: string;
  status: "running" | "paused";
  pnl: number;
  pnlPct: number;
  positions: number;
}

export interface Trade {
  id: number;
  time: string;
  symbol: string;
  side: "BUY" | "SELL";
  qty: number;
  price: number;
  strategy: string;
}

export interface DashboardData {
  performance: PerformancePoint[];
  strategies: Strategy[];
  trades: Trade[];
}