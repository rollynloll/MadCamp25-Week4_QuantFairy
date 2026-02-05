import type { TradingPositionItem } from "@/types/trading";
import type { Position } from "@/types/portfolio";

export function mapPosition(p: TradingPositionItem): Position {
  const qty = p.qty ?? 0;
  const avgPrice = p.avg_price ?? 0;
  const currentPrice = p.market_price ?? avgPrice;
  const pnl = p.unrealized_pnl ?? 0;
  const base = Math.abs(qty) * (avgPrice || 1);
  const pnlPct = p.unrealized_pnl_pct ?? (base ? (pnl / base) * 100 : 0);
  const side = qty >= 0 ? "long" : "short";
  return {
    symbol: p.symbol,
    name: p.symbol,
    qty,
    side,
    avgPrice,
    currentPrice,
    pnl,
    pnlPct,
    strategy: p.strategy?.name ?? p.strategy?.id ?? p.strategy_id ?? "Unassigned",
  };
}
