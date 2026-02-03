import type { TradingPositionItem } from "@/types/trading";
import type { Position } from "@/types/portfolio";

export function mapPosition(p: TradingPositionItem): Position {
  const side = p.qty >= 0 ? "long" : "short";
  return {
    symbol: p.symbol,
    name: p.symbol,
    qty: p.qty,
    side,
    avgPrice: p.avg_price,
    currentPrice: p.market_price,
    pnl: p.unrealized_pnl,
    pnlPct: p.unrealized_pnl_pct,
    strategy: p.strategy?.name ?? "-",
  };
}