import type { TradingOrder } from "@/types/trading";

export interface UiOrder {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  type: "LIMIT" | "MARKET" | "STOP" | "STOP LIMIT";
  qty: number;
  filled: number;
  price: number | null;
  status: string;
  strategy: string;
}

export function mapOrder(o: TradingOrder): UiOrder {
  const price = o.limit_price ?? o.avg_fill_price ?? null;
  return {
    id: o.order_id,
    symbol: o.symbol,
    side: o.side.toUpperCase() as UiOrder["side"],
    type: o.type.replace("_", " ").toUpperCase() as UiOrder["type"],
    qty: o.qty ?? 0,
    filled: o.filled_qty ?? 0,
    price,
    status: o.status,
    strategy: o.strategy?.name ?? "-",
  };
}
