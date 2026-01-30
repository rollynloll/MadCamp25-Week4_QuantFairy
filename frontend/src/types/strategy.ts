export type StrategyStatus = "running" | "paused" | "stopped";

export interface Strategy {
  id: number;
  name: string;
  status: StrategyStatus;
  type: string;
  pnl: number;
  pnlPct: number;
  sharpe: number;
  maxDrawdown: number;
  trades: number;
  winRate: number;
  avgHoldTime: string;
}
