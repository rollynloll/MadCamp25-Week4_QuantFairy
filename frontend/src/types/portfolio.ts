export interface Position {
  symbol: string;
  name: string;
  qty: number;
  side: "short" | "long";
  avgPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPct: number;
  strategy: string;
};

export type StrategyState = "running" | "paused" | "stopped";

export interface Strategy {
  id: number;
  name: string;
  state: StrategyState;
  currentWeight: number;
  targetWeight: number;
  positionsCount: number;
  lastRun: string;
};

export interface SectorAllocationItem {
  sector: string;
  percent: number;
  value: number;
};

export interface EquityPoint {
  date: string;
  value: number;
};

export interface DrawdownPoint {
  date: string;
  value: number;
};

export type OrderStatus = "filled" | "partial" | "cancelled" | "pending"; 
export interface Order {
  id: number;
  time: string;
  type: "BUY" | "SELL";
  symbol: string;
  qty: number;
  status: OrderStatus;
  strategy: string;
};

export type AlertLevel = "warning" | "error";

export interface AlertItem {
  id: number;
  time: string;
  level: AlertLevel;
  message: string;
  strategy: string;
};
export interface BotRun {
  id: number;
  time: string;
  status: "success" | "failed";
  duration: string;
  trades: number;
};