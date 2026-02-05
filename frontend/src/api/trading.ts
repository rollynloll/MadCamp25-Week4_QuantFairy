import { buildApiUrl } from "@/api/base";
import type {
  TradingOrdersResponse,
  TradingOrderDetail,
  TradingPositionsResponse,
  TradingBarsResponse,
  TradingQuoteResponse,
} from "@/types/trading";

export type OrderScope = "open" | "filled" | "all";

export async function getTradingOrders(params: {
  scope: OrderScope;
  limit?: number;
  cursor?: string | null;
}): Promise<TradingOrdersResponse> {
  const { scope, limit = 50, cursor } = params;

  const res = await fetch(buildApiUrl("/trading/orders", {
    scope,
    limit,
    cursor: cursor ?? undefined
  }), {
    headers: { "Content-Type": "application/json" }
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load orders (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function getTradingOrder(orderId: string): Promise<TradingOrderDetail> {
  const res = await fetch(buildApiUrl(`/trading/orders/${orderId}`), {
    headers: { "Content-Type": "application/json" }
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load order (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function getTradingPositions(): Promise<TradingPositionsResponse> {
  const res = await fetch(buildApiUrl("/trading/positions"), {
    headers: { "Content-Type": "application/json" }
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load positions (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function getTradingBars(params: {
  symbol: string;
  timeframe?: string;
  limit?: number;
  feed?: string;
}): Promise<TradingBarsResponse> {
  const { symbol, timeframe = "1Min", limit = 200, feed } = params;
  const res = await fetch(
    buildApiUrl("/trading/bars", {
      symbol,
      timeframe,
      limit,
      feed: feed ?? undefined,
    }),
    {
      headers: { "Content-Type": "application/json" },
    }
  );

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load bars (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}

export async function getTradingQuote(params: {
  symbol: string;
  feed?: string;
}): Promise<TradingQuoteResponse> {
  const { symbol, feed } = params;
  const res = await fetch(
    buildApiUrl("/trading/quote", {
      symbol,
      feed: feed ?? undefined,
    }),
    {
      headers: { "Content-Type": "application/json" },
    }
  );

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message ?? `Failed to load quote (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}
