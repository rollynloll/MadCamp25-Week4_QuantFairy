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

const normalizeToken = (value: string | null | undefined) => {
  const raw = (value ?? "").trim();
  if (!raw) return "";
  return raw.includes(".") ? raw.split(".").pop() ?? raw : raw;
};

export function mapOrder(o: TradingOrder): UiOrder {
  const price = o.limit_price ?? o.avg_fill_price ?? null;
  const side = normalizeToken(o.side).toUpperCase();
  const type = normalizeToken(o.type).replaceAll("_", " ").toUpperCase();
  const status = normalizeToken(o.status).toUpperCase();
  return {
    id: o.order_id,
    symbol: o.symbol,
    side: (side || "BUY") as UiOrder["side"],
    type: (type || "MARKET") as UiOrder["type"],
    qty: o.qty ?? 0,
    filled: o.filled_qty ?? 0,
    price,
    status: status || "PENDING",
    strategy: o.strategy?.name ?? "-",
  };
}
