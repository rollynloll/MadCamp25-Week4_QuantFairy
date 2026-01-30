export interface Position {
  symbol: string;
  name: string;
  qty: number;
  avgPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPct: number;
  strategy: string;
}

export interface AllocationItem {
  category: string;
  value: number;
  amount: number;
}

export interface PortfolioSummaryData {
  totalValue: number;
  totalPnL: number;
  openPositions: number;
  longCount: number;
  shortCount: number;
}